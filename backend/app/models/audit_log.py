from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    # case.created | document.uploaded | document.hash_computed
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # case | document
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    actor: Mapped[User] = relationship(foreign_keys=[actor_user_id])


from app.models.user import User  # noqa: E402
