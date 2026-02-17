from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tenant_type: Mapped[str] = mapped_column(String(20), nullable=False)  # buyer | supplier
    is_active: Mapped[bool] = mapped_column(default=True)

    users: Mapped[list[User]] = relationship(back_populates="tenant")
    cases: Mapped[list[Case]] = relationship(
        back_populates="supplier_tenant", foreign_keys="Case.supplier_tenant_id"
    )
    sent_invites: Mapped[list[Invite]] = relationship(
        back_populates="buyer_tenant", foreign_keys="Invite.buyer_tenant_id"
    )


from app.models.case import Case  # noqa: E402
from app.models.invite import Invite  # noqa: E402
from app.models.user import User  # noqa: E402
