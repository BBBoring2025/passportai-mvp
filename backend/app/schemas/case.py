import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class CreateCaseRequest(BaseModel):
    reference_no: str = Field(..., max_length=100)
    product_group: str = Field(default="textiles", max_length=50)
    date_from: date | None = None
    date_to: date | None = None
    notes: str | None = None


class CaseResponse(BaseModel):
    id: uuid.UUID
    reference_no: str
    product_group: str
    status: str
    date_from: date | None
    date_to: date | None
    notes: str | None
    supplier_tenant_id: uuid.UUID
    buyer_tenant_id: uuid.UUID
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    model_config = {"from_attributes": True}


class CaseCreateResponse(BaseModel):
    case_id: uuid.UUID
    status: str
