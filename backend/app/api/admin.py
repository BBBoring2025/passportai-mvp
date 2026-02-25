"""Admin L2 review + approve/reject endpoints for Sprint 4."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.database import get_db
from app.models.case import Case
from app.models.checklist_item import ChecklistItem
from app.models.document import Document
from app.models.extracted_field import ExtractedField
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.validation import (
    AdminFieldResponse,
    FieldRejectRequest,
)
from app.services.ai.field_mapping import FIELD_LABELS
from app.services.audit import write_audit

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Helper: build AdminFieldResponse with denormalized data ──


def _build_admin_response(
    field: ExtractedField,
    db: Session,
    case_map: dict | None = None,
) -> AdminFieldResponse:
    """Build AdminFieldResponse with denormalized info."""
    doc = (
        db.query(Document)
        .filter(Document.id == field.document_id)
        .first()
    )

    # Get case
    if case_map and field.case_id in case_map:
        case = case_map[field.case_id]
    else:
        case = (
            db.query(Case)
            .filter(Case.id == field.case_id)
            .first()
        )

    # Get supplier tenant name
    supplier_name = None
    if case:
        tenant = (
            db.query(Tenant)
            .filter(Tenant.id == case.supplier_tenant_id)
            .first()
        )
        supplier_name = tenant.name if tenant else None

    resp = AdminFieldResponse.model_validate(field)
    resp.document_filename = (
        doc.original_filename if doc else None
    )
    resp.doc_type = doc.doc_type if doc else None
    resp.supplier_name = supplier_name
    resp.case_reference_no = (
        case.reference_no if case else None
    )
    return resp


# ── GET /admin/review-queue ──────────────────────────────────


@router.get(
    "/review-queue",
    response_model=list[AdminFieldResponse],
)
def admin_review_queue(
    field_status: str = Query(
        default="pending_review", alias="status"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Admin L2 review queue — fields across all buyer's cases."""
    cases = (
        db.query(Case)
        .filter(Case.buyer_tenant_id == current_user.tenant_id)
        .all()
    )
    case_ids = [c.id for c in cases]
    if not case_ids:
        return []

    case_map = {c.id: c for c in cases}

    fields = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.case_id.in_(case_ids),
            ExtractedField.status == field_status,
        )
        .order_by(ExtractedField.created_at.desc())
        .all()
    )

    return [
        _build_admin_response(f, db, case_map) for f in fields
    ]


# ── POST /admin/fields/{id}/approve ─────────────────────────


@router.post(
    "/fields/{field_id}/approve",
    response_model=AdminFieldResponse,
)
def approve_field(
    field_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Admin approves a field: tier=L2, status=approved, visibility=buyer_visible."""
    field = (
        db.query(ExtractedField)
        .filter(ExtractedField.id == field_id)
        .first()
    )
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    # Tenant isolation: field's case must belong to admin's buyer tenant
    case = (
        db.query(Case).filter(Case.id == field.case_id).first()
    )
    if (
        not case
        or case.buyer_tenant_id != current_user.tenant_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    field.tier = "L2"
    field.status = "approved"
    field.visibility = "buyer_visible"

    write_audit(
        db,
        current_user.id,
        "field.l2_approved",
        "extracted_field",
        field.id,
        {"canonical_key": field.canonical_key},
    )

    db.commit()
    db.refresh(field)

    return _build_admin_response(field, db)


# ── POST /admin/fields/{id}/reject ──────────────────────────


@router.post(
    "/fields/{field_id}/reject",
    response_model=AdminFieldResponse,
)
def reject_field(
    field_id: uuid.UUID,
    body: FieldRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Admin rejects a field: status=rejected, creates checklist item."""
    field = (
        db.query(ExtractedField)
        .filter(ExtractedField.id == field_id)
        .first()
    )
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    case = (
        db.query(Case).filter(Case.id == field.case_id).first()
    )
    if (
        not case
        or case.buyer_tenant_id != current_user.tenant_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    field.status = "rejected"

    # Create checklist item for supplier to fix
    field_label = FIELD_LABELS.get(
        field.canonical_key, field.canonical_key
    )
    reason = body.reason or "Rejected by admin."

    checklist_item = ChecklistItem(
        case_id=field.case_id,
        type="missing_field",
        severity="high",
        status="open",
        title=f"Rejected Field: {field_label}",
        description=(
            f"'{field_label}' field was rejected by admin. "
            f"Reason: {reason} "
            "Please correct the value and resubmit."
        ),
        related_field_id=field.id,
    )
    db.add(checklist_item)

    write_audit(
        db,
        current_user.id,
        "field.l2_rejected",
        "extracted_field",
        field.id,
        {
            "canonical_key": field.canonical_key,
            "reason": reason,
        },
    )

    db.commit()
    db.refresh(field)

    return _build_admin_response(field, db)
