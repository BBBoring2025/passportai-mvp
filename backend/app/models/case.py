from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Case(TimestampMixin, Base):
    __tablename__ = "cases"

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference_no: Mapped[str] = mapped_column(String(100), nullable=False)
    product_group: Mapped[str] = mapped_column(String(50), default="textiles")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    # draft | processing | ready_l1 | ready_l2 | blocked | closed

    date_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    supplier_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    buyer_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    invite_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invites.id"), nullable=True
    )

    supplier_tenant: Mapped[Tenant] = relationship(
        back_populates="cases", foreign_keys=[supplier_tenant_id]
    )
    buyer_tenant: Mapped[Tenant] = relationship(foreign_keys=[buyer_tenant_id])
    created_by: Mapped[User] = relationship()
    invite: Mapped[Invite | None] = relationship(back_populates="cases")
    documents: Mapped[list[Document]] = relationship(back_populates="case")


from app.models.document import Document  # noqa: E402
from app.models.invite import Invite  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.user import User  # noqa: E402
