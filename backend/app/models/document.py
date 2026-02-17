from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    doc_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # invoice | packing_list | certificate | test_report | sds | bom | null
    classification_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # heuristic | llm | manual
    classification_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    processing_status: Mapped[str] = mapped_column(String(20), default="uploaded")
    # uploaded | processing | text_extracted | classified | extracted | error

    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # encrypted_pdf | low_quality_image | ocr_failed | unsupported_file | extraction_timeout
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Turkish human-readable error message

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    case: Mapped[Case] = relationship(back_populates="documents")
    uploaded_by_user: Mapped[User] = relationship(foreign_keys=[uploaded_by])
    extracted_fields: Mapped[list[ExtractedField]] = relationship(back_populates="document")
    pages: Mapped[list[DocumentPage]] = relationship(
        back_populates="document", order_by="DocumentPage.page_number"
    )


from app.models.case import Case  # noqa: E402
from app.models.document_page import DocumentPage  # noqa: E402
from app.models.evidence_anchor import EvidenceAnchor  # noqa: E402, F401
from app.models.extracted_field import ExtractedField  # noqa: E402
from app.models.user import User  # noqa: E402
