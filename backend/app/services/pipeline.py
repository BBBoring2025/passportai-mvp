"""Document processing pipeline orchestrator.

Synchronous MVP pipeline: validate → extract text → classify.
Extraction (AI field extraction) is triggered separately via API.
Commits after each major step for atomicity.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.document import Document
from app.models.document_page import DocumentPage
from app.models.evidence_anchor import EvidenceAnchor
from app.models.extracted_field import ExtractedField
from app.services.ai import get_classifier, get_extractor
from app.services.ai.extractor import snippet_hash
from app.services.audit import write_audit
from app.services.extraction import ExtractionError, extract_text
from app.services.magic import validate_magic_bytes
from app.services.storage import get_file_bytes

logger = logging.getLogger(__name__)

# ── Turkish error messages ──────────────────────────────────────────────────────
ERROR_MESSAGES: dict[str, str] = {
    "encrypted_pdf": "PDF dosyasi sifre korumali. Lutfen sifreyi kaldirip tekrar yukleyin.",
    "low_quality_image": (
        "Goruntu kalitesi cok dusuk. Lutfen daha net bir goruntu yukleyin."
    ),
    "ocr_failed": (
        "Metin cikarilmasi basarisiz oldu. Lutfen daha net bir goruntu yukleyin."
    ),
    "unsupported_file": "Dosya icerigi beklenen formata uymuyor.",
    "extraction_timeout": "Islem zaman asimina ugradi. Lutfen tekrar deneyin.",
    "extraction_failed": (
        "Veri cikarma basarisiz oldu. Lutfen tekrar deneyin."
    ),
}


def _set_error(
    db: Session,
    doc: Document,
    actor_id: uuid.UUID,
    error_code: str,
    error_message: str | None = None,
) -> Document:
    """Mark a document as errored, commit, and write audit."""
    doc.processing_status = "error"
    doc.error_code = error_code
    doc.error_message = error_message or ERROR_MESSAGES.get(error_code, error_code)
    write_audit(
        db,
        actor_id,
        "document.processing_error",
        "document",
        doc.id,
        {"error_code": error_code},
    )
    db.commit()
    return doc


def process_document(db: Session, document: Document, actor_id: uuid.UUID) -> Document:
    """
    Run the full processing pipeline for a single document.

    Pipeline:
    1. Validate magic bytes
    2. Extract text (page by page)
    3. Classify document type (heuristic-first, LLM fallback)

    Commits after each major step for atomicity.
    """
    # ── Step 1: Get file bytes ───────────────────────────────────────────────
    try:
        file_bytes = get_file_bytes(document.storage_path)
    except Exception as exc:
        logger.error("Failed to read file for document %s: %s", document.id, exc)
        return _set_error(db, document, actor_id, "unsupported_file")

    # ── Step 2: Validate magic bytes ─────────────────────────────────────────
    if not validate_magic_bytes(file_bytes, document.mime_type):
        return _set_error(db, document, actor_id, "unsupported_file")

    # ── Step 3: Update status to "processing" ────────────────────────────────
    document.processing_status = "processing"
    document.error_code = None
    document.error_message = None
    write_audit(db, actor_id, "document.processing_started", "document", document.id)
    db.commit()

    # ── Step 4: Extract text ─────────────────────────────────────────────────
    try:
        page_texts = extract_text(file_bytes, document.mime_type)
    except ExtractionError as exc:
        return _set_error(db, document, actor_id, exc.error_code, exc.message)
    except Exception as exc:
        logger.error("Unexpected extraction error for document %s: %s", document.id, exc)
        return _set_error(db, document, actor_id, "ocr_failed")

    # Save extracted pages
    for pt in page_texts:
        page = DocumentPage(
            document_id=document.id,
            page_number=pt.page_number,
            extracted_text=pt.text,
            extraction_method=pt.method,
            char_count=pt.char_count,
        )
        db.add(page)

    document.page_count = len(page_texts)
    document.processing_status = "text_extracted"
    write_audit(
        db,
        actor_id,
        "document.text_extracted",
        "document",
        document.id,
        {"page_count": len(page_texts)},
    )
    db.commit()

    # ── Step 5: Classify document ────────────────────────────────────────────
    first_page_text = page_texts[0].text if page_texts else ""
    classifier = get_classifier()

    try:
        result = classifier.classify(document.original_filename, first_page_text)
    except Exception as exc:
        logger.warning("Classification failed for document %s: %s", document.id, exc)
        result = None

    if result:
        document.doc_type = result.doc_type
        document.classification_method = result.method
        document.classification_confidence = result.confidence
    else:
        # No classification — manual review needed, but still advance status
        document.doc_type = None
        document.classification_method = None
        document.classification_confidence = None

    document.processing_status = "classified"
    write_audit(
        db,
        actor_id,
        "document.classified",
        "document",
        document.id,
        {
            "doc_type": document.doc_type,
            "method": document.classification_method,
            "confidence": document.classification_confidence,
        },
    )
    db.commit()
    db.refresh(document)

    return document


def process_case_documents(
    db: Session, case: Case, actor_id: uuid.UUID
) -> list[Document]:
    """
    Process all uploaded (unprocessed) documents in a case.

    Updates case.status to "processing" at start, then to "ready_l1" or "blocked"
    depending on results.
    """
    documents = [d for d in case.documents if d.processing_status == "uploaded"]

    if not documents:
        return []

    # Mark case as processing
    case.status = "processing"
    write_audit(db, actor_id, "case.processing_started", "case", case.id)
    db.commit()

    # Process each document
    results: list[Document] = []
    for doc in documents:
        result = process_document(db, doc, actor_id)
        results.append(result)

    # Determine final case status
    all_docs = db.query(Document).filter(Document.case_id == case.id).all()
    has_errors = any(d.processing_status == "error" for d in all_docs)
    all_classified = all(
        d.processing_status in ("classified", "extracted") for d in all_docs
    )

    if has_errors:
        case.status = "blocked"
    elif all_classified:
        case.status = "ready_l1"
    # else: stay "processing" (shouldn't happen in sync flow)

    db.commit()
    db.refresh(case)

    return results


def run_extraction(
    db: Session,
    document: Document,
    actor_id: uuid.UUID,
    use_mock: bool = False,
) -> Document:
    """
    Run AI field extraction on a classified document.

    Separate from process_document() — triggered via dedicated API.
    Expensive (LLM calls per page), so not run automatically.
    use_mock=True uses MockExtractor with ground truth data.
    """
    extractor = get_extractor(use_mock=use_mock)
    if extractor is None:
        return _set_error(
            db, document, actor_id, "extraction_failed",
            "AI extraction not available (API key not configured).",
        )

    # If re-extracting, delete existing fields (cascade deletes anchors)
    if document.processing_status == "extracted":
        db.query(ExtractedField).filter(
            ExtractedField.document_id == document.id
        ).delete()
        db.commit()

    # Load pages
    pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == document.id)
        .order_by(DocumentPage.page_number)
        .all()
    )

    if not pages:
        return _set_error(
            db, document, actor_id, "extraction_failed",
            "Dokumanda cikarilmis sayfa bulunamadi.",
        )

    page_tuples = [
        (p.page_number, p.extracted_text or "") for p in pages
    ]

    try:
        output = extractor.extract_fields(
            document.doc_type, page_tuples
        )
    except Exception as exc:
        logger.error(
            "Extraction failed for document %s: %s",
            document.id,
            exc,
        )
        return _set_error(
            db, document, actor_id, "extraction_failed"
        )

    # Persist extracted fields + evidence anchors
    for result in output.results:
        field = ExtractedField(
            document_id=document.id,
            case_id=document.case_id,
            canonical_key=result.canonical_key,
            value=result.value,
            unit=result.unit,
            page=result.page,
            snippet=result.snippet,
            confidence=result.confidence,
            tier="L1",
            status="pending_review",
            visibility="supplier_only",
            created_from="extraction",
        )
        db.add(field)
        db.flush()  # get field.id for anchor

        anchor = EvidenceAnchor(
            field_id=field.id,
            document_id=document.id,
            page_no=result.page,
            snippet_text=result.snippet,
            snippet_hash=snippet_hash(result.snippet),
        )
        db.add(anchor)

    # Update document status
    document.processing_status = "extracted"
    document.error_code = None
    document.error_message = None

    # Audit with token usage
    usage_meta = {
        "fields_extracted": len(output.results),
        "input_tokens": output.usage.input_tokens,
        "output_tokens": output.usage.output_tokens,
        "pages_processed": output.usage.pages_processed,
        "pages_skipped": output.usage.pages_skipped,
    }
    write_audit(
        db,
        actor_id,
        "document.extraction_completed",
        "document",
        document.id,
        usage_meta,
    )
    db.commit()
    db.refresh(document)

    return document
