from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BuyerSupplierLink(TimestampMixin, Base):
    __tablename__ = "buyer_supplier_links"

    buyer_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    supplier_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    invite_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invites.id"), nullable=False
    )

    buyer_tenant: Mapped[Tenant] = relationship(foreign_keys=[buyer_tenant_id])
    supplier_tenant: Mapped[Tenant] = relationship(foreign_keys=[supplier_tenant_id])
    invite: Mapped[Invite] = relationship()


from app.models.invite import Invite  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
