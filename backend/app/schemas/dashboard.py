"""Pydantic schemas for Sprint 5: buyer dashboard, metrics, reports."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

# ── Supplier-level metrics (one row in buyer dashboard) ───────


class SupplierMetrics(BaseModel):
    tenant_name: str
    tenant_id: uuid.UUID
    latest_case_id: uuid.UUID | None = None
    coverage_pct: float = 0.0
    conflict_rate: float = 0.0
    days_to_ready: float | None = None
    l1_count: int = 0
    l2_count: int = 0
    field_count: int = 0
    status: str = "no_case"


# ── Aggregate metrics (top-level summary cards) ──────────────


class AggregateMetrics(BaseModel):
    total_suppliers: int = 0
    avg_coverage: float = 0.0
    total_conflicts: int = 0
    avg_days_to_ready: float | None = None


# ── Buyer dashboard response ─────────────────────────────────


class BuyerDashboardResponse(BaseModel):
    suppliers: list[SupplierMetrics]
    aggregate: AggregateMetrics


# ── Per-case metrics ─────────────────────────────────────────


class CaseMetricsResponse(BaseModel):
    case_id: uuid.UUID
    evidence_coverage_pct: float = 0.0
    conflict_rate: float = 0.0
    days_to_ready_l1: float | None = None
    days_to_ready_l2: float | None = None
    total_fields: int = 0
    l1_fields: int = 0
    l2_fields: int = 0
    buyer_visible_fields: int = 0
    required_fields_present: int = 0
    required_fields_total: int = 4
    checklist_open: int = 0
    checklist_done: int = 0


# ── Readiness report ─────────────────────────────────────────


class ReadinessReportField(BaseModel):
    canonical_key: str
    label: str
    value: str
    unit: str | None = None
    tier: str
    status: str
    confidence: float | None = None
    evidence_count: int = 0


class ReadinessReport(BaseModel):
    case_id: uuid.UUID
    reference_no: str
    supplier_name: str
    buyer_name: str
    generated_at: datetime
    metrics: CaseMetricsResponse
    fields: list[ReadinessReportField]
