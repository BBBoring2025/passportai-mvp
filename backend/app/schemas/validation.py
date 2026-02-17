"""Pydantic schemas for Sprint 4: validation, checklist, admin review."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

# ── Validation Results ─────────────────────────────────────


class ValidationResultResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    rule_key: str
    severity: str
    status: str
    message: str
    related_field_ids: list[str] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ValidationSummary(BaseModel):
    case_id: uuid.UUID
    total_rules: int
    passed: int
    failed: int
    warnings: int
    checklist_items_created: int
    results: list[ValidationResultResponse]


# ── Checklist Items ────────────────────────────────────────


class ChecklistItemResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    type: str
    severity: str
    status: str
    title: str
    description: str
    related_field_id: uuid.UUID | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateChecklistItemRequest(BaseModel):
    status: str  # "done" | "open" | "reopened"


# ── Admin Review ───────────────────────────────────────────


class AdminFieldResponse(BaseModel):
    """Extended field response for admin review queue."""

    id: uuid.UUID
    document_id: uuid.UUID
    case_id: uuid.UUID
    canonical_key: str
    value: str
    unit: str | None = None
    page: int
    snippet: str
    confidence: float | None = None
    tier: str
    status: str
    visibility: str
    created_from: str
    created_at: datetime
    # Denormalized for admin UI
    document_filename: str | None = None
    doc_type: str | None = None
    supplier_name: str | None = None
    case_reference_no: str | None = None

    model_config = {"from_attributes": True}


class FieldRejectRequest(BaseModel):
    reason: str | None = None
