from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Invite(TimestampMixin, Base):
    __tablename__ = "invites"

    buyer_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    supplier_email: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | accepted | expired
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    buyer_tenant: Mapped[Tenant] = relationship(
        back_populates="sent_invites", foreign_keys=[buyer_tenant_id]
    )
    cases: Mapped[list[Case]] = relationship(back_populates="invite")


from app.models.case import Case  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
