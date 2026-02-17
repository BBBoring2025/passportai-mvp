from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ExtractedField(TimestampMixin, Base):
    __tablename__ = "extracted_fields"
    __table_args__ = (
        Index("ix_extracted_fields_case_key", "case_id", "canonical_key"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    canonical_key: Mapped[str] = mapped_column(String(200), nullable=False)
    # e.g. shipment.invoice_number, material.composition.cotton_pct
    value: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Evidence linkage — MANDATORY
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_from: Mapped[str] = mapped_column(
        String(20), nullable=False, default="extraction"
    )
    # extraction | manual | system

    tier: Mapped[str] = mapped_column(
        String(10), nullable=False, default="L1"
    )
    # L1 | L2 | L3

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review"
    )
    # missing | pending_review | approved | conflict | rejected

    visibility: Mapped[str] = mapped_column(
        String(30), nullable=False, default="supplier_only"
    )
    # supplier_only | buyer_visible

    # Relationships
    document: Mapped[Document] = relationship(
        back_populates="extracted_fields"
    )
    case: Mapped[Case] = relationship(foreign_keys=[case_id])
    evidence_anchors: Mapped[list[EvidenceAnchor]] = relationship(
        back_populates="field", cascade="all, delete-orphan"
    )


from app.models.case import Case  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.evidence_anchor import EvidenceAnchor  # noqa: E402
