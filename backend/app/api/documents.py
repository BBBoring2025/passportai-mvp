import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.database import get_db
from app.models.case import Case
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentUploadResponse
from app.services.audit import write_audit
from app.services.magic import validate_magic_bytes
from app.services.storage import compute_sha256, get_file_bytes, upload_file

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    case_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    doc_type: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("supplier")),
):
    # Validate case exists and belongs to supplier
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if case.supplier_tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Validate file type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{content_type}' not allowed. Use PDF, JPG, or PNG.",
        )

    # Read file content
    file_bytes = file.file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum 50 MB.",
        )

    # Validate magic bytes
    if not validate_magic_bytes(file_bytes, content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Dosya icerigi beklenen formata uymuyor."
                " Lutfen gecerli bir PDF, JPG veya PNG dosyasi yukleyin."
            ),
        )

    # Compute SHA256
    sha256 = compute_sha256(file_bytes)

    # Create document record (need ID for storage path)
    doc = Document(
        case_id=case_id,
        original_filename=file.filename or "unknown",
        storage_path="",  # updated after upload
        mime_type=content_type,
        file_size_bytes=len(file_bytes),
        doc_type=doc_type,
        processing_status="uploaded",
        sha256_hash=sha256,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.flush()

    # Upload to storage
    storage_path = upload_file(
        file_bytes=file_bytes,
        filename=file.filename or f"{doc.id}.bin",
        case_id=case_id,
        document_id=doc.id,
        mime_type=content_type,
    )
    doc.storage_path = storage_path

    # Audit logs
    write_audit(
        db,
        current_user.id,
        "document.uploaded",
        "document",
        doc.id,
        {"case_id": str(case_id), "filename": file.filename, "file_size": len(file_bytes)},
    )
    write_audit(
        db,
        current_user.id,
        "document.hash_computed",
        "document",
        doc.id,
        {"sha256": sha256},
    )

    db.commit()
    db.refresh(doc)

    return DocumentUploadResponse(
        document_id=doc.id,
        status=doc.processing_status,
        sha256_hash=sha256,
    )


@router.get("/{document_id}/download")
def download_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("supplier", "admin")),
):
    """Download raw document. Buyer CANNOT access this endpoint."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Tenant isolation: supplier can only download their own
    case = db.query(Case).filter(Case.id == doc.case_id).first()
    if current_user.role == "supplier" and case.supplier_tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    file_bytes = get_file_bytes(doc.storage_path)
    return Response(
        content=file_bytes,
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.original_filename}"'},
    )
