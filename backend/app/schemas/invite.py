import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class CreateInviteRequest(BaseModel):
    supplier_email: EmailStr


class InviteResponse(BaseModel):
    id: uuid.UUID
    supplier_email: str
    token: str
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
