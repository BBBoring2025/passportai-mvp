import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_role
from app.database import get_db
from app.models.case import Case
from app.models.document import Document
from app.models.document_page import DocumentPage
from app.models.user import User
from app.schemas.document import DocumentPageResponse, ProcessingResponse
from app.services.pipeline import process_case_documents, process_document

router = APIRouter(tags=["processing"])


@router.post(
    "/cases/{case_id}/start-processing",
    response_model=ProcessingResponse,
)
def start_processing(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("supplier")),
):
    """Start processing all uploaded documents in a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    # Tenant isolation
    if case.supplier_tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Check there are documents to process
    uploadable = [d for d in case.documents if d.processing_status == "uploaded"]
    if not uploadable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents in 'uploaded' state to process.",
        )

    # Run pipeline (synchronous for MVP)
    results = process_case_documents(db, case, current_user.id)

    documents_errored = sum(1 for d in results if d.processing_status == "error")
    documents_processed = len(results) - documents_errored

    # Refresh case to get updated status
    db.refresh(case)

    return ProcessingResponse(
        case_id=case.id,
        documents_processed=documents_processed,
        documents_errored=documents_errored,
        case_status=case.status,
    )


@router.post("/documents/{doc_id}/retry", response_model=ProcessingResponse)
def retry_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("supplier")),
):
    """Retry processing a failed document."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Tenant isolation
    case = db.query(Case).filter(Case.id == doc.case_id).first()
    if not case or case.supplier_tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if doc.processing_status != "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only documents in 'error' state can be retried.",
        )

    # Reset document state
    doc.processing_status = "uploaded"
    doc.error_code = None
    doc.error_message = None
    doc.doc_type = None
    doc.classification_method = None
    doc.classification_confidence = None
    doc.page_count = None

    # Delete existing pages
    db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).delete()
    db.commit()

    # Re-process
    result = process_document(db, doc, current_user.id)

    is_error = result.processing_status == "error"

    # Update case status
    all_docs = db.query(Document).filter(Document.case_id == case.id).all()
    has_errors = any(d.processing_status == "error" for d in all_docs)
    all_classified = all(
        d.processing_status in ("classified", "extracted") for d in all_docs
    )

    if has_errors:
        case.status = "blocked"
    elif all_classified:
        case.status = "ready_l1"
    db.commit()
    db.refresh(case)

    return ProcessingResponse(
        case_id=case.id,
        documents_processed=0 if is_error else 1,
        documents_errored=1 if is_error else 0,
        case_status=case.status,
    )


@router.get(
    "/documents/{doc_id}/pages",
    response_model=list[DocumentPageResponse],
)
def list_document_pages(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List extracted pages for a document."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Tenant isolation
    case = db.query(Case).filter(Case.id == doc.case_id).first()
    if current_user.role == "supplier" and case.supplier_tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.role in ("buyer", "admin") and case.buyer_tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == doc.id)
        .order_by(DocumentPage.page_number)
        .all()
    )
    return pages
