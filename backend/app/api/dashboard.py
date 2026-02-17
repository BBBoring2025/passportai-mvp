"""Buyer dashboard, case metrics, and readiness report endpoints for Sprint 5."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_role
from app.database import get_db
from app.models.buyer_supplier_link import BuyerSupplierLink
from app.models.case import Case
from app.models.evidence_anchor import EvidenceAnchor
from app.models.extracted_field import ExtractedField
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.dashboard import (
    AggregateMetrics,
    BuyerDashboardResponse,
    CaseMetricsResponse,
    ReadinessReport,
    ReadinessReportField,
    SupplierMetrics,
)
from app.services.ai.field_mapping import FIELD_LABELS
from app.services.metrics import compute_case_metrics

router = APIRouter(tags=["dashboard"])


# ── GET /dashboard/buyer ──────────────────────────────────────


@router.get(
    "/dashboard/buyer",
    response_model=BuyerDashboardResponse,
)
def buyer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("buyer", "admin")),
):
    """Buyer dashboard — linked suppliers with aggregated metrics."""
    # Find all linked suppliers
    links = (
        db.query(BuyerSupplierLink)
        .filter(
            BuyerSupplierLink.buyer_tenant_id
            == current_user.tenant_id
        )
        .all()
    )

    suppliers: list[SupplierMetrics] = []
    total_conflicts = 0
    coverage_values: list[float] = []
    days_values: list[float] = []

    for link in links:
        supplier_tenant = (
            db.query(Tenant)
            .filter(Tenant.id == link.supplier_tenant_id)
            .first()
        )
        if not supplier_tenant:
            continue

        # Find the latest case for this supplier-buyer pair
        latest_case = (
            db.query(Case)
            .filter(
                Case.supplier_tenant_id == link.supplier_tenant_id,
                Case.buyer_tenant_id == current_user.tenant_id,
            )
            .order_by(Case.created_at.desc())
            .first()
        )

        if not latest_case:
            suppliers.append(
                SupplierMetrics(
                    tenant_name=supplier_tenant.name,
                    tenant_id=supplier_tenant.id,
                    status="no_case",
                )
            )
            continue

        metrics = compute_case_metrics(db, latest_case)

        sm = SupplierMetrics(
            tenant_name=supplier_tenant.name,
            tenant_id=supplier_tenant.id,
            latest_case_id=latest_case.id,
            coverage_pct=metrics.evidence_coverage_pct,
            conflict_rate=metrics.conflict_rate,
            days_to_ready=metrics.days_to_ready_l1,
            l1_count=metrics.l1_fields,
            l2_count=metrics.l2_fields,
            field_count=metrics.total_fields,
            status=latest_case.status,
        )
        suppliers.append(sm)

        # Accumulate for aggregates
        coverage_values.append(metrics.evidence_coverage_pct)
        conflict_fields = (
            db.query(ExtractedField)
            .filter(
                ExtractedField.case_id == latest_case.id,
                ExtractedField.status == "conflict",
            )
            .count()
        )
        total_conflicts += conflict_fields
        if metrics.days_to_ready_l1 is not None:
            days_values.append(metrics.days_to_ready_l1)

    aggregate = AggregateMetrics(
        total_suppliers=len(suppliers),
        avg_coverage=(
            round(sum(coverage_values) / len(coverage_values), 1)
            if coverage_values
            else 0.0
        ),
        total_conflicts=total_conflicts,
        avg_days_to_ready=(
            round(sum(days_values) / len(days_values), 1)
            if days_values
            else None
        ),
    )

    return BuyerDashboardResponse(
        suppliers=suppliers,
        aggregate=aggregate,
    )


# ── GET /cases/{id}/metrics ───────────────────────────────────


@router.get(
    "/cases/{case_id}/metrics",
    response_model=CaseMetricsResponse,
)
def case_metrics(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-case metrics — accessible by supplier, buyer, or admin."""
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

    return compute_case_metrics(db, case)


# ── GET /reports/case/{id} ────────────────────────────────────


@router.get(
    "/reports/case/{case_id}",
    response_model=ReadinessReport,
)
def case_readiness_report(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("buyer", "admin")),
):
    """Readiness report — buyer only, only buyer_visible fields."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    # Buyer tenant isolation
    if case.buyer_tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Only buyer_visible fields — data minimization
    fields = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.case_id == case_id,
            ExtractedField.visibility == "buyer_visible",
        )
        .all()
    )

    # Build report fields
    report_fields: list[ReadinessReportField] = []
    for f in fields:
        anchor_count = (
            db.query(EvidenceAnchor)
            .filter(EvidenceAnchor.field_id == f.id)
            .count()
        )
        report_fields.append(
            ReadinessReportField(
                canonical_key=f.canonical_key,
                label=FIELD_LABELS.get(
                    f.canonical_key, f.canonical_key
                ),
                value=f.value,
                unit=f.unit,
                tier=f.tier,
                status=f.status,
                confidence=f.confidence,
                evidence_count=anchor_count,
            )
        )

    # Get tenant names
    supplier_tenant = (
        db.query(Tenant)
        .filter(Tenant.id == case.supplier_tenant_id)
        .first()
    )
    buyer_tenant = (
        db.query(Tenant)
        .filter(Tenant.id == case.buyer_tenant_id)
        .first()
    )

    metrics = compute_case_metrics(db, case)

    return ReadinessReport(
        case_id=case.id,
        reference_no=case.reference_no,
        supplier_name=(
            supplier_tenant.name if supplier_tenant else "Unknown"
        ),
        buyer_name=(
            buyer_tenant.name if buyer_tenant else "Unknown"
        ),
        generated_at=datetime.now(UTC),
        metrics=metrics,
        fields=report_fields,
    )
