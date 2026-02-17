import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size_bytes: int
    page_count: int | None = None
    doc_type: str | None = None
    classification_method: str | None = None
    classification_confidence: float | None = None
    processing_status: str
    error_code: str | None = None
    error_message: str | None = None
    sha256_hash: str | None = None
    uploaded_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    status: str
    sha256_hash: str


class DocumentPageResponse(BaseModel):
    id: uuid.UUID
    page_number: int
    extraction_method: str
    char_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProcessingResponse(BaseModel):
    case_id: uuid.UUID
    documents_processed: int
    documents_errored: int
    case_status: str
