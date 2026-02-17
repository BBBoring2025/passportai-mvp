"""Validation result — output of a single rule evaluation against a case."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ValidationResult(TimestampMixin, Base):
    __tablename__ = "validation_results"
    __table_args__ = (
        Index("ix_validation_results_case_id", "case_id"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    rule_key: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    related_field_ids: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    case: Mapped[Case] = relationship(foreign_keys=[case_id])


# Deferred import to avoid circular dependency
from app.models.case import Case  # noqa: E402, F811
