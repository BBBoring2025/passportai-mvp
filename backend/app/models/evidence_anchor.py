from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class EvidenceAnchor(TimestampMixin, Base):
    __tablename__ = "evidence_anchors"

    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_fields.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False
    )
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    snippet_text: Mapped[str] = mapped_column(Text, nullable=False)
    bbox: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON string for bounding box, optional for MVP
    snippet_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    # SHA256 of snippet_text

    # Relationships
    field: Mapped[ExtractedField] = relationship(
        back_populates="evidence_anchors"
    )
    document: Mapped[Document] = relationship()


from app.models.document import Document  # noqa: E402
from app.models.extracted_field import ExtractedField  # noqa: E402
