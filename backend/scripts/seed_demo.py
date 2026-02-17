#!/usr/bin/env python3
"""
Demo seed for Sprint 5 — realistic multi-supplier data for MassChallenge.

Creates:
- 1 buyer (Nordic Fashion Group GmbH) + buyer + admin users
- 3 suppliers with different readiness:
  A) Yildiz Tekstil  — 6 docs, all extracted, all L2 approved → HIGH
  B) Ozkan Tekstil   — 3 docs (invoice, packing, bom), partial → MEDIUM
  C) Demir Tekstil   — 1 doc (invoice only), 1 conflict → LOW

Usage:
    cd passportai/backend
    source .venv/bin/activate
    python -m scripts.seed_demo
"""

from __future__ import annotations

import os
import shutil
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"
SAMPLE_DIR = ROOT / "sample_docs"
DEMO_DB = BACKEND / "demo.db"
DEMO_UPLOADS = BACKEND / "demo_uploads"

# ── Load .env ─────────────────────────────────────────────
_env_path = BACKEND / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ[_key.strip()] = _val.strip()

sys.path.insert(0, str(BACKEND))

# ── SQLite UUID patch ─────────────────────────────────────
from sqlalchemy import String as SA_String  # noqa: E402
from sqlalchemy import TypeDecorator  # noqa: E402
from sqlalchemy.dialects.postgresql import UUID as PG_UUID  # noqa: E402


class PortableUUID(TypeDecorator):
    impl = SA_String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
        return value


_orig = PG_UUID.__init__


def _patched(self, as_uuid=False):
    _orig(self, as_uuid=as_uuid)


PG_UUID.__init__ = _patched

from sqlalchemy.ext.compiler import compiles  # noqa: E402


@compiles(PG_UUID, "sqlite")
def compile_pg_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"


# ── Imports ───────────────────────────────────────────────
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.core.auth import hash_password  # noqa: E402
from app.models import (  # noqa: E402
    BuyerSupplierLink,
    Case,
    Document,
    ExtractedField,
    Invite,
    Tenant,
    User,
)
from app.models.base import Base  # noqa: E402
from app.services.pipeline import process_document, run_extraction  # noqa: E402
from app.services.rules.engine import RulesEngine  # noqa: E402
from app.services.storage import compute_sha256  # noqa: E402

G = "\033[92m"
Y = "\033[93m"
W = "\033[0m"


def setup_db() -> Session:
    if DEMO_DB.exists():
        DEMO_DB.unlink()
    if DEMO_UPLOADS.exists():
        shutil.rmtree(DEMO_UPLOADS)
    DEMO_UPLOADS.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{DEMO_DB}", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


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


def upload_docs(
    db: Session,
    case: Case,
    actor_id: uuid.UUID,
    filenames: list[str],
) -> list[Document]:
    docs = []
    for fn in filenames:
        pdf_path = SAMPLE_DIR / fn
        if not pdf_path.exists():
            print(f"  {Y}SKIP: {fn} not found{W}")
            continue
        file_bytes = pdf_path.read_bytes()
        sha256 = compute_sha256(file_bytes)
        storage = DEMO_UPLOADS / f"{case.reference_no}_{fn}"
        storage.write_bytes(file_bytes)
        doc = Document(
            case_id=case.id,
            original_filename=fn,
            storage_path=str(storage),
            mime_type="application/pdf",
            file_size_bytes=len(file_bytes),
            sha256_hash=sha256,
            processing_status="uploaded",
            uploaded_by=actor_id,
        )
        db.add(doc)
        docs.append(doc)
    db.commit()
    for d in docs:
        db.refresh(d)
    return docs


def process_and_extract(
    db: Session,
    docs: list[Document],
    actor_id: uuid.UUID,
) -> int:
    total_fields = 0
    for doc in docs:
        db.refresh(doc)
        process_document(db, doc, actor_id)
        db.refresh(doc)
        if doc.processing_status == "classified" and doc.doc_type:
            run_extraction(db, doc, actor_id, use_mock=True)
            count = (
                db.query(ExtractedField)
                .filter(ExtractedField.document_id == doc.id)
                .count()
            )
            total_fields += count
            print(f"    {doc.original_filename}: {doc.doc_type}, {count} fields")
    return total_fields


def approve_all_fields(db: Session, case: Case) -> int:
    """Admin approves all pending fields → L2, buyer_visible."""
    fields = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.case_id == case.id,
            ExtractedField.status == "pending_review",
        )
        .all()
    )
    for f in fields:
        f.tier = "L2"
        f.status = "approved"
        f.visibility = "buyer_visible"
    db.commit()
    return len(fields)


def approve_some_fields(
    db: Session,
    case: Case,
    keys_to_approve: list[str],
) -> int:
    """Admin approves only fields matching given canonical keys."""
    approved = 0
    for key in keys_to_approve:
        field = (
            db.query(ExtractedField)
            .filter(
                ExtractedField.case_id == case.id,
                ExtractedField.canonical_key == key,
                ExtractedField.status == "pending_review",
            )
            .first()
        )
        if field:
            field.tier = "L2"
            field.status = "approved"
            field.visibility = "buyer_visible"
            approved += 1
    db.commit()
    return approved


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    print("=" * 64)
    print("  DEMO SEED — MassChallenge Screenshots")
    print("=" * 64)

    db = setup_db()

    # ── Buyer ──────────────────────────────────────────────
    buyer_t = create_tenant(db, "Nordic Fashion Group GmbH", "nordic-fashion", "buyer")
    buyer_u = create_user(db, "buyer@nordic.com", "Eva Nordstrom", "buyer", buyer_t.id)
    admin_u = create_user(db, "admin@nordic.com", "Karl Admin", "admin", buyer_t.id)

    print(f"\n{G}Buyer:{W} {buyer_t.name}")
    print(f"  buyer: {buyer_u.email} / demo1234")
    print(f"  admin: {admin_u.email} / demo1234")

    # ── Supplier A: Yildiz Tekstil (HIGH) ─────────────────
    print(f"\n{'='*50}")
    print(f"{G}Supplier A: Yildiz Tekstil — HIGH readiness{W}")

    sa_t = create_tenant(db, "Yildiz Tekstil A.S.", "yildiz-tekstil", "supplier")
    sa_u = create_user(db, "info@yildiz.com", "Ahmet Yildiz", "supplier", sa_t.id)
    link_supplier(db, buyer_t, sa_t, "info@yildiz.com")
    db.commit()

    case_a = create_case(db, "YT-2026-001", sa_t, buyer_t, sa_u, "draft")
    docs_a = upload_docs(db, case_a, sa_u.id, [
        "01_commercial_invoice.pdf",
        "02_packing_list.pdf",
        "03_oekotex_certificate.pdf",
        "04_test_report_sgs.pdf",
        "05_sds_reactive_dye.pdf",
        "06_bom_material_declaration.pdf",
    ])
    print(f"  Uploaded {len(docs_a)} docs")
    fields_a = process_and_extract(db, docs_a, sa_u.id)
    print(f"  Total fields: {fields_a}")

    # Run validation
    summary_a = RulesEngine.run_all(db, case_a, sa_u.id)
    print(
        f"  Validation: {summary_a['passed']} pass, "
        f"{summary_a['failed']} fail, "
        f"{summary_a['warnings']} warn"
    )

    # Admin approves ALL
    approved_a = approve_all_fields(db, case_a)
    case_a.status = "ready_l2"
    db.commit()
    print(f"  Approved: {approved_a} fields → L2 + buyer_visible")
    print(f"  Case status: {case_a.status}")

    # ── Supplier B: Ozkan Tekstil (MEDIUM) ────────────────
    print(f"\n{'='*50}")
    print(f"{Y}Supplier B: Ozkan Tekstil — MEDIUM readiness{W}")

    sb_t = create_tenant(db, "Ozkan Tekstil Ltd.", "ozkan-tekstil", "supplier")
    sb_u = create_user(db, "info@ozkan.com", "Mehmet Ozkan", "supplier", sb_t.id)
    link_supplier(db, buyer_t, sb_t, "info@ozkan.com")
    db.commit()

    case_b = create_case(db, "OZ-2026-001", sb_t, buyer_t, sb_u, "draft")
    docs_b = upload_docs(db, case_b, sb_u.id, [
        "01_commercial_invoice.pdf",
        "02_packing_list.pdf",
        "06_bom_material_declaration.pdf",
    ])
    print(f"  Uploaded {len(docs_b)} docs")
    fields_b = process_and_extract(db, docs_b, sb_u.id)
    print(f"  Total fields: {fields_b}")

    # Run validation — will flag missing docs
    summary_b = RulesEngine.run_all(db, case_b, sb_u.id)
    print(
        f"  Validation: {summary_b['passed']} pass, "
        f"{summary_b['failed']} fail, "
        f"{summary_b['warnings']} warn"
    )

    # Admin approves only shipment fields
    approved_b = approve_some_fields(db, case_b, [
        "shipment.invoice_number",
        "shipment.invoice_date",
        "shipment.total_quantity",
    ])
    case_b.status = "ready_l1"
    db.commit()
    print(f"  Approved: {approved_b} fields → L2 + buyer_visible")
    print(f"  Case status: {case_b.status}")

    # ── Supplier C: Demir Tekstil (LOW) ───────────────────
    print(f"\n{'='*50}")
    print("\033[91mSupplier C: Demir Tekstil — LOW readiness\033[0m")

    sc_t = create_tenant(db, "Demir Tekstil San.", "demir-tekstil", "supplier")
    sc_u = create_user(db, "info@demir.com", "Ali Demir", "supplier", sc_t.id)
    link_supplier(db, buyer_t, sc_t, "info@demir.com")
    db.commit()

    case_c = create_case(db, "DM-2026-001", sc_t, buyer_t, sc_u, "draft")
    docs_c = upload_docs(db, case_c, sc_u.id, [
        "01_commercial_invoice.pdf",
    ])
    print(f"  Uploaded {len(docs_c)} docs")
    fields_c = process_and_extract(db, docs_c, sc_u.id)
    print(f"  Total fields: {fields_c}")

    # Manually set one field to conflict for variety
    first_field = (
        db.query(ExtractedField)
        .filter(ExtractedField.case_id == case_c.id)
        .first()
    )
    if first_field:
        first_field.status = "conflict"
        db.commit()
        print("  Set 1 field to conflict status")

    # No validation, no approvals
    print(f"  Case status: {case_c.status} (no validation)")

    # ── Summary ───────────────────────────────────────────
    print(f"\n{'='*64}")
    print("  DEMO DATA SUMMARY")
    print(f"{'='*64}")

    from app.services.metrics import compute_case_metrics

    for label, case in [
        ("A (Yildiz - HIGH)", case_a),
        ("B (Ozkan - MEDIUM)", case_b),
        ("C (Demir - LOW)", case_c),
    ]:
        db.refresh(case)
        m = compute_case_metrics(db, case)
        print(
            f"\n  {label}:"
            f"\n    Status: {case.status}"
            f"\n    Coverage: {m.evidence_coverage_pct}%"
            f"\n    Conflict rate: {m.conflict_rate}%"
            f"\n    Fields: {m.total_fields} (L1={m.l1_fields}, L2={m.l2_fields})"
            f"\n    Buyer visible: {m.buyer_visible_fields}"
        )

    db.close()
    print(f"\n  DB: {DEMO_DB}")
    print("  Done! Use these credentials to log in:")
    print("    Buyer:  buyer@nordic.com / demo1234")
    print("    Admin:  admin@nordic.com / demo1234")


if __name__ == "__main__":
    main()
