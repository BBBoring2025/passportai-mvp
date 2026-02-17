#!/usr/bin/env python3
"""
Production seed — creates demo data in the REAL database (PostgreSQL).

Connects via DATABASE_URL (from .env or environment), no SQLite hacks.

Creates:
- 1 buyer (Nordic Fashion Group GmbH) + buyer user + admin user
- 3 suppliers with invites + BuyerSupplierLinks:
  A) Yildiz Tekstil  — HIGH readiness placeholder
  B) Ozkan Tekstil   — MEDIUM readiness placeholder
  C) Demir Tekstil   — LOW readiness placeholder

Usage:
    cd passportai/backend
    python -m scripts.seed_production
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.auth import hash_password
from app.database import SessionLocal
from app.models import (
    BuyerSupplierLink,
    Case,
    Invite,
    Tenant,
    User,
)

G = "\033[92m"
Y = "\033[93m"
R = "\033[91m"
W = "\033[0m"


def create_tenant(db: Session, name: str, slug: str, ttype: str) -> Tenant:
    t = Tenant(name=name, slug=slug, tenant_type=ttype)
    db.add(t)
    db.flush()
    return t


def create_user(
    db: Session,
    email: str,
    name: str,
    role: str,
    tenant_id: uuid.UUID,
) -> User:
    u = User(
        email=email,
        full_name=name,
        password_hash=hash_password("demo1234"),
        role=role,
        tenant_id=tenant_id,
    )
    db.add(u)
    db.flush()
    return u


def link_supplier(
    db: Session,
    buyer_tenant: Tenant,
    supplier_tenant: Tenant,
    supplier_email: str,
) -> None:
    inv = Invite(
        buyer_tenant_id=buyer_tenant.id,
        supplier_email=supplier_email,
        token=f"demo-{supplier_tenant.slug}",
        status="accepted",
        expires_at=datetime.now(UTC) + timedelta(days=30),
        accepted_at=datetime.now(UTC),
    )
    db.add(inv)
    db.flush()
    link = BuyerSupplierLink(
        buyer_tenant_id=buyer_tenant.id,
        supplier_tenant_id=supplier_tenant.id,
        invite_id=inv.id,
    )
    db.add(link)


def create_case(
    db: Session,
    ref: str,
    supplier_tenant: Tenant,
    buyer_tenant: Tenant,
    supplier_user: User,
    case_status: str = "draft",
) -> Case:
    c = Case(
        reference_no=ref,
        product_group="textiles",
        status=case_status,
        supplier_tenant_id=supplier_tenant.id,
        buyer_tenant_id=buyer_tenant.id,
        created_by_user_id=supplier_user.id,
    )
    db.add(c)
    db.commit()
    return c


def seed() -> None:
    """Seed demo data into the production database."""
    print("=" * 64)
    print("  PRODUCTION SEED — Demo Data")
    print("=" * 64)

    db = SessionLocal()
    try:
        # ── Check if already seeded ───────────────────────────
        existing = db.query(Tenant).filter(Tenant.slug == "nordic-fashion").first()
        if existing:
            print(f"\n{Y}Already seeded (nordic-fashion tenant exists). Skipping.{W}")
            return

        # ── Buyer ─────────────────────────────────────────────
        buyer_t = create_tenant(
            db, "Nordic Fashion Group GmbH", "nordic-fashion", "buyer"
        )
        buyer_u = create_user(
            db, "buyer@nordic.com", "Eva Nordstrom", "buyer", buyer_t.id
        )
        admin_u = create_user(
            db, "admin@nordic.com", "Karl Admin", "admin", buyer_t.id
        )
        db.commit()

        print(f"\n{G}Buyer:{W} {buyer_t.name}")
        print(f"  buyer: {buyer_u.email} / demo1234")
        print(f"  admin: {admin_u.email} / demo1234")

        # ── Supplier A: Yildiz Tekstil (HIGH) ─────────────────
        print(f"\n{'=' * 50}")
        print(f"{G}Supplier A: Yildiz Tekstil{W}")

        sa_t = create_tenant(
            db, "Yildiz Tekstil A.S.", "yildiz-tekstil", "supplier"
        )
        sa_u = create_user(
            db, "info@yildiz.com", "Ahmet Yildiz", "supplier", sa_t.id
        )
        link_supplier(db, buyer_t, sa_t, "info@yildiz.com")
        db.commit()

        case_a = create_case(db, "YT-2026-001", sa_t, buyer_t, sa_u, "draft")
        print(f"  User: {sa_u.email} / demo1234")
        print(f"  Case: {case_a.reference_no}")

        # ── Supplier B: Ozkan Tekstil (MEDIUM) ────────────────
        print(f"\n{'=' * 50}")
        print(f"{Y}Supplier B: Ozkan Tekstil{W}")

        sb_t = create_tenant(
            db, "Ozkan Tekstil Ltd.", "ozkan-tekstil", "supplier"
        )
        sb_u = create_user(
            db, "info@ozkan.com", "Mehmet Ozkan", "supplier", sb_t.id
        )
        link_supplier(db, buyer_t, sb_t, "info@ozkan.com")
        db.commit()

        case_b = create_case(db, "OZ-2026-001", sb_t, buyer_t, sb_u, "draft")
        print(f"  User: {sb_u.email} / demo1234")
        print(f"  Case: {case_b.reference_no}")

        # ── Supplier C: Demir Tekstil (LOW) ───────────────────
        print(f"\n{'=' * 50}")
        print(f"{R}Supplier C: Demir Tekstil{W}")

        sc_t = create_tenant(
            db, "Demir Tekstil San.", "demir-tekstil", "supplier"
        )
        sc_u = create_user(
            db, "info@demir.com", "Ali Demir", "supplier", sc_t.id
        )
        link_supplier(db, buyer_t, sc_t, "info@demir.com")
        db.commit()

        case_c = create_case(db, "DM-2026-001", sc_t, buyer_t, sc_u, "draft")
        print(f"  User: {sc_u.email} / demo1234")
        print(f"  Case: {case_c.reference_no}")

        # ── Summary ───────────────────────────────────────────
        print(f"\n{'=' * 64}")
        print("  SEED COMPLETE")
        print(f"{'=' * 64}")
        print("\n  Credentials (all passwords: demo1234):")
        print("    Buyer:      buyer@nordic.com")
        print("    Admin:      admin@nordic.com")
        print("    Supplier A: info@yildiz.com")
        print("    Supplier B: info@ozkan.com")
        print("    Supplier C: info@demir.com")
        print("\n  Cases created (status=draft):")
        print(f"    {case_a.reference_no} (Yildiz)")
        print(f"    {case_b.reference_no} (Ozkan)")
        print(f"    {case_c.reference_no} (Demir)")
        print(
            "\n  Suppliers can now upload documents via the UI."
            "\n  Admin can review & approve via the review queue."
        )

    finally:
        db.close()


if __name__ == "__main__":
    seed()
