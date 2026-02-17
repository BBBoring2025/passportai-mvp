"""Metrics computation service for Sprint 5 — buyer dashboard & reports."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.checklist_item import ChecklistItem
from app.models.document import Document
from app.models.evidence_anchor import EvidenceAnchor
from app.models.extracted_field import ExtractedField
from app.schemas.dashboard import CaseMetricsResponse

# Required fields for evidence coverage metric
REQUIRED_FIELDS = [
    "shipment.invoice_number",
    "shipment.total_quantity",
    "material.composition.cotton_pct",
    "material.composition.elastane_pct",
]


def compute_evidence_coverage(db: Session, case_id: uuid.UUID) -> float:
    """
    (required_fields with >=1 evidence_anchor) / total_required_fields * 100.

    Checks if each required canonical_key exists as an ExtractedField
    for this case and has at least one EvidenceAnchor.
    """
    covered = 0
    for key in REQUIRED_FIELDS:
        field = (
            db.query(ExtractedField)
            .filter(
                ExtractedField.case_id == case_id,
                ExtractedField.canonical_key == key,
                ExtractedField.status != "rejected",
            )
            .first()
        )
        if field:
            anchor_count = (
                db.query(EvidenceAnchor)
                .filter(EvidenceAnchor.field_id == field.id)
                .count()
            )
            if anchor_count >= 1:
                covered += 1

    total = len(REQUIRED_FIELDS)
    return round(covered / total * 100, 1) if total > 0 else 0.0


def compute_conflict_rate(db: Session, case_id: uuid.UUID) -> float:
    """(fields with status=conflict) / (total extracted fields) * 100."""
    total = (
        db.query(ExtractedField)
        .filter(ExtractedField.case_id == case_id)
        .count()
    )
    if total == 0:
        return 0.0

    conflicts = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.case_id == case_id,
            ExtractedField.status == "conflict",
        )
        .count()
    )
    return round(conflicts / total * 100, 1)


def compute_days_to_ready(db: Session, case: Case) -> float | None:
    """
    Simplified MVP: days from first document upload to now.

    Returns None if no documents have been uploaded yet.
    """
    first_doc = (
        db.query(Document)
        .filter(Document.case_id == case.id)
        .order_by(Document.created_at.asc())
        .first()
    )
    if not first_doc or not first_doc.created_at:
        return None

    now = datetime.now(UTC)
    # Handle naive datetimes from SQLite
    first_upload = first_doc.created_at
    if first_upload.tzinfo is None:
        first_upload = first_upload.replace(tzinfo=UTC)

    delta = now - first_upload
    return round(delta.total_seconds() / 86400, 1)


def compute_case_metrics(
    db: Session, case: Case
) -> CaseMetricsResponse:
    """Aggregate all metrics for a single case."""
    case_id = case.id

    # Field counts
    all_fields = (
        db.query(ExtractedField)
        .filter(ExtractedField.case_id == case_id)
        .all()
    )
    total_fields = len(all_fields)
    l1_fields = sum(1 for f in all_fields if f.tier == "L1")
    l2_fields = sum(1 for f in all_fields if f.tier == "L2")
    buyer_visible = sum(
        1 for f in all_fields if f.visibility == "buyer_visible"
    )

    # Required fields present
    present_keys = {f.canonical_key for f in all_fields}
    required_present = sum(
        1 for k in REQUIRED_FIELDS if k in present_keys
    )

    # Checklist counts
    checklist_open = (
        db.query(ChecklistItem)
        .filter(
            ChecklistItem.case_id == case_id,
            ChecklistItem.status == "open",
        )
        .count()
    )
    checklist_done = (
        db.query(ChecklistItem)
        .filter(
            ChecklistItem.case_id == case_id,
            ChecklistItem.status == "done",
        )
        .count()
    )

    return CaseMetricsResponse(
        case_id=case_id,
        evidence_coverage_pct=compute_evidence_coverage(db, case_id),
        conflict_rate=compute_conflict_rate(db, case_id),
        days_to_ready_l1=compute_days_to_ready(db, case),
        days_to_ready_l2=compute_days_to_ready(db, case),
        total_fields=total_fields,
        l1_fields=l1_fields,
        l2_fields=l2_fields,
        buyer_visible_fields=buyer_visible,
        required_fields_present=required_present,
        required_fields_total=len(REQUIRED_FIELDS),
        checklist_open=checklist_open,
        checklist_done=checklist_done,
    )
