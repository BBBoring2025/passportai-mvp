import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_role
from app.database import get_db
from app.models.case import Case
from app.models.document import Document
from app.models.document_page import DocumentPage
from app.models.evidence_anchor import EvidenceAnchor
from app.models.extracted_field import ExtractedField
from app.models.user import User
from app.schemas.extraction import (
    EvidenceAnchorResponse,
    ExtractedFieldResponse,
    ExtractionResponse,
    PageRenderResponse,
    UpdateFieldRequest,
)
from app.services.ai import get_extractor
from app.services.audit import write_audit
from app.services.pipeline import run_extraction

router = APIRouter(tags=["extraction"])


@router.post(
    "/documents/{doc_id}/run-extraction",
    response_model=ExtractionResponse,
)
def run_document_extraction(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("supplier")),
):
    """Run AI field extraction on a classified document."""
    # Check API key is available
    extractor = get_extractor()
    if extractor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI extraction not available (API key not configured).",
        )

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Tenant isolation
    case = db.query(Case).filter(Case.id == doc.case_id).first()
    if not case or case.supplier_tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Must be classified with a doc_type
    if doc.processing_status not in ("classified", "extracted"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Document must be in 'classified' or 'extracted' "
                "state to run extraction."
            ),
        )
    if not doc.doc_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no doc_type classification.",
        )

    # Run extraction
    result = run_extraction(db, doc, current_user.id)

    # Count extracted fields
    fields_count = (
        db.query(ExtractedField)
        .filter(ExtractedField.document_id == doc.id)
        .count()
    )

    token_usage = None
    # Get latest audit log for token usage
    from app.models.audit_log import AuditLog

    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.entity_id == doc.id,
            AuditLog.action == "document.extraction_completed",
        )
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    if audit and audit.metadata_json:
        import json

        meta = json.loads(audit.metadata_json)
        token_usage = {
            "input_tokens": meta.get("input_tokens", 0),
            "output_tokens": meta.get("output_tokens", 0),
        }

    return ExtractionResponse(
        document_id=doc.id,
        fields_extracted=fields_count,
        processing_status=result.processing_status,
        token_usage=token_usage,
    )


@router.get(
    "/cases/{case_id}/fields",
    response_model=list[ExtractedFieldResponse],
)
def list_case_fields(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List extracted fields for a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    # Tenant isolation
    if current_user.role == "supplier":
        if case.supplier_tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    elif current_user.role in ("buyer", "admin"):
        if case.buyer_tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

    # Base query
    query = db.query(ExtractedField).filter(
        ExtractedField.case_id == case_id
    )

    # Buyer can only see buyer_visible fields
    if current_user.role in ("buyer", "admin"):
        query = query.filter(
            ExtractedField.visibility == "buyer_visible"
        )

    fields = query.all()

    # Build response with denormalized doc info
    result = []
    # Cache doc info to avoid N+1
    doc_cache: dict[uuid.UUID, Document] = {}
    for f in fields:
        if f.document_id not in doc_cache:
            doc = (
                db.query(Document)
                .filter(Document.id == f.document_id)
                .first()
            )
            doc_cache[f.document_id] = doc
        doc = doc_cache[f.document_id]
        resp = ExtractedFieldResponse.model_validate(f)
        resp.document_filename = doc.original_filename if doc else None
        resp.doc_type = doc.doc_type if doc else None
        result.append(resp)

    return result


@router.get(
    "/fields/{field_id}/evidence",
    response_model=list[EvidenceAnchorResponse],
)
def list_field_evidence(
    field_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List evidence anchors for a field."""
    field = (
        db.query(ExtractedField)
        .filter(ExtractedField.id == field_id)
        .first()
    )
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    # Tenant isolation via field → case
    case = db.query(Case).filter(Case.id == field.case_id).first()
    if current_user.role == "supplier":
        if case.supplier_tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    elif current_user.role in ("buyer", "admin"):
        if case.buyer_tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

    anchors = (
        db.query(EvidenceAnchor)
        .filter(EvidenceAnchor.field_id == field_id)
        .all()
    )
    return anchors


@router.patch(
    "/fields/{field_id}",
    response_model=ExtractedFieldResponse,
)
def update_field(
    field_id: uuid.UUID,
    body: UpdateFieldRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("supplier")),
):
    """Update an extracted field (manual entry)."""
    field = (
        db.query(ExtractedField)
        .filter(ExtractedField.id == field_id)
        .first()
    )
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    # Tenant isolation
    case = db.query(Case).filter(Case.id == field.case_id).first()
    if not case or case.supplier_tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Enforce: if value is set, snippet must also be provided
    if body.value is not None and body.snippet is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Snippet (kanit) zorunludur. "
                "Deger girerken kaynagi da belirtmelisiniz."
            ),
        )

    # Apply updates
    if body.value is not None:
        field.value = body.value
        field.created_from = "manual"
    if body.unit is not None:
        field.unit = body.unit
    if body.page is not None:
        field.page = body.page
    if body.snippet is not None:
        field.snippet = body.snippet
    if body.status is not None:
        field.status = body.status

    write_audit(
        db,
        current_user.id,
        "field.manual_entry",
        "extracted_field",
        field.id,
        {"canonical_key": field.canonical_key},
    )
    db.commit()
    db.refresh(field)

    # Denormalized info
    doc = (
        db.query(Document)
        .filter(Document.id == field.document_id)
        .first()
    )
    resp = ExtractedFieldResponse.model_validate(field)
    resp.document_filename = doc.original_filename if doc else None
    resp.doc_type = doc.doc_type if doc else None
    return resp


@router.get(
    "/documents/{doc_id}/render",
    response_model=PageRenderResponse,
)
def render_document_page(
    doc_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("supplier", "admin")),
):
    """Render a single page of a document for the viewer.

    Buyer CANNOT access this endpoint — data minimization.
    Buyers see approved fields via GET /cases/{id}/fields
    and evidence snippets via GET /fields/{id}/evidence.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Tenant isolation — only supplier + admin reach here
    case = db.query(Case).filter(Case.id == doc.case_id).first()
    if current_user.role == "supplier":
        if case.supplier_tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    elif current_user.role == "admin":
        if case.buyer_tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

    total_pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == doc.id)
        .count()
    )

    if total_pages == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pages found for this document.",
        )

    doc_page = (
        db.query(DocumentPage)
        .filter(
            DocumentPage.document_id == doc.id,
            DocumentPage.page_number == page,
        )
        .first()
    )
    if not doc_page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page} not found.",
        )

    return PageRenderResponse(
        page_number=doc_page.page_number,
        total_pages=total_pages,
        text=doc_page.extracted_text or "",
        extraction_method=doc_page.extraction_method,
    )
