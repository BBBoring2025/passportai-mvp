import uuid
from datetime import datetime

from pydantic import BaseModel


class ExtractionResponse(BaseModel):
    document_id: uuid.UUID
    fields_extracted: int
    processing_status: str
    token_usage: dict | None = None


class ExtractedFieldResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    case_id: uuid.UUID
    canonical_key: str
    value: str
    unit: str | None = None
    page: int
    snippet: str
    confidence: float | None = None
    tier: str
    status: str
    visibility: str
    created_from: str
    created_at: datetime
    # Denormalized for UI
    document_filename: str | None = None
    doc_type: str | None = None

    model_config = {"from_attributes": True}


class EvidenceAnchorResponse(BaseModel):
    id: uuid.UUID
    field_id: uuid.UUID
    document_id: uuid.UUID
    page_no: int
    snippet_text: str
    bbox: str | None = None
    snippet_hash: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateFieldRequest(BaseModel):
    value: str | None = None
    unit: str | None = None
    page: int | None = None
    snippet: str | None = None
    status: str | None = None


class PageRenderResponse(BaseModel):
    page_number: int
    total_pages: int
    text: str
    extraction_method: str
