"""Validation + checklist endpoints for Sprint 4."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_role
from app.database import get_db
from app.models.case import Case
from app.models.checklist_item import ChecklistItem
from app.models.user import User
from app.models.validation_result import ValidationResult
from app.schemas.validation import (
    ChecklistItemResponse,
    UpdateChecklistItemRequest,
    ValidationResultResponse,
    ValidationSummary,
)
from app.services.audit import write_audit
from app.services.rules.engine import RulesEngine

router = APIRouter(tags=["validation"])


# ── POST /cases/{id}/run-validation ──────────────────────────


@router.post(
    "/cases/{case_id}/run-validation",
    response_model=ValidationSummary,
)
def run_case_validation(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("supplier")),
):
    """Run all validation rules on a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    # Tenant isolation
    if case.supplier_tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    summary = RulesEngine.run_all(db, case, current_user.id)

    # Fetch persisted results for response
    results = (
        db.query(ValidationResult)
        .filter(ValidationResult.case_id == case.id)
        .order_by(ValidationResult.created_at)
        .all()
    )

    result_responses = []
    for r in results:
        resp = ValidationResultResponse.model_validate(r)
        if r.related_field_ids:
            try:
                resp.related_field_ids = json.loads(
                    r.related_field_ids
                )
            except json.JSONDecodeError:
                resp.related_field_ids = None
        result_responses.append(resp)

    return ValidationSummary(
        case_id=case.id,
        total_rules=summary["total_rules"],
        passed=summary["passed"],
        failed=summary["failed"],
        warnings=summary["warnings"],
        checklist_items_created=summary["checklist_items_created"],
        results=result_responses,
    )


# ── GET /cases/{id}/checklist ────────────────────────────────


@router.get(
    "/cases/{case_id}/checklist",
    response_model=list[ChecklistItemResponse],
)
def list_case_checklist(
    case_id: uuid.UUID,
    status_filter: str | None = Query(
        default=None, alias="status"
    ),
    severity: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List checklist items for a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    # Tenant isolation
    if current_user.role == "supplier":
        if case.supplier_tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    elif current_user.role in ("buyer", "admin"):
        if case.buyer_tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

    query = db.query(ChecklistItem).filter(
        ChecklistItem.case_id == case_id
    )

    if status_filter:
        query = query.filter(
            ChecklistItem.status == status_filter
        )
    if severity:
        query = query.filter(
            ChecklistItem.severity == severity
        )

    items = query.order_by(
        ChecklistItem.created_at.desc()
    ).all()
    return items


# ── PATCH /checklist/{id} ────────────────────────────────────


@router.patch(
    "/checklist/{item_id}",
    response_model=ChecklistItemResponse,
)
def update_checklist_item(
    item_id: uuid.UUID,
    body: UpdateChecklistItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("supplier")),
):
    """Mark a checklist item as done (or reopen)."""
    item = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist item not found",
        )

    # Tenant isolation via case
    case = db.query(Case).filter(Case.id == item.case_id).first()
    if (
        not case
        or case.supplier_tenant_id != current_user.tenant_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if body.status not in ("done", "open", "reopened"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'done', 'open', or 'reopened'.",
        )

    item.status = body.status
    if body.status == "done":
        item.completed_at = datetime.now(UTC)
    elif body.status in ("open", "reopened"):
        item.completed_at = None

    write_audit(
        db,
        current_user.id,
        "checklist.item_updated",
        "checklist_item",
        item.id,
        {"new_status": body.status},
    )

    db.commit()
    db.refresh(item)
    return item
