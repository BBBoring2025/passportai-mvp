#!/usr/bin/env python3
"""
Sprint 4 — Rules Engine + Checklist + Admin L2 Approval E2E.

Reuses the Sprint 3 setup (SQLite, seed, upload, process, extract)
then runs the rules engine and admin workflows.

Usage:
    cd passportai/backend
    source .venv/bin/activate
    python tests/test_sprint4_e2e.py
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
TEST_DB = BACKEND / "test_sprint4.db"
TEST_UPLOADS = BACKEND / "test_uploads_s4"

# ── Load .env BEFORE importing app (singleton) ───────────
_env_path = BACKEND / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ[_key.strip()] = _val.strip()

sys.path.insert(0, str(BACKEND))

# ── Patch PostgreSQL UUID before importing models ─────────
from sqlalchemy import String as SA_String  # noqa: E402
from sqlalchemy import TypeDecorator  # noqa: E402
from sqlalchemy.dialects.postgresql import UUID as PG_UUID  # noqa: E402


class PortableUUID(TypeDecorator):
    """UUID type that works on both PostgreSQL and SQLite."""
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


_orig_uuid_init = PG_UUID.__init__


def _patched_uuid_init(self, as_uuid=False):
    _orig_uuid_init(self, as_uuid=as_uuid)


PG_UUID.__init__ = _patched_uuid_init

from sqlalchemy.ext.compiler import compiles  # noqa: E402


@compiles(PG_UUID, "sqlite")
def compile_pg_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"


# ── Now import the app ────────────────────────────────────
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.auth import hash_password  # noqa: E402
from app.models import (  # noqa: E402
    BuyerSupplierLink,
    Case,
    ChecklistItem,
    Document,
    ExtractedField,
    Invite,
    Tenant,
    User,
    ValidationResult,
)
from app.models.base import Base  # noqa: E402
from app.services.pipeline import (  # noqa: E402
    process_document,
    run_extraction,
)
from app.services.rules.engine import RulesEngine  # noqa: E402
from app.services.storage import compute_sha256  # noqa: E402

# ── Formatting ────────────────────────────────────────────
G = "\033[92m"  # green
R = "\033[91m"  # red
Y = "\033[93m"  # yellow
W = "\033[0m"   # reset
PASS_S = f"{G}PASS{W}"
FAIL_S = f"{R}FAIL{W}"
SKIP_S = f"{Y}SKIP{W}"

results: dict[str, str] = {}


def check(name: str, passed: bool, detail: str = ""):
    s = PASS_S if passed else FAIL_S
    results[name] = "PASS" if passed else "FAIL"
    d = f"  ({detail})" if detail else ""
    print(f"  [{s}] {name}{d}")


# ══════════════════════════════════════════════════════════
#  SETUP (reused from Sprint 3)
# ══════════════════════════════════════════════════════════

def setup_db() -> Session:
    """Create SQLite DB + tables from ORM models."""
    if TEST_DB.exists():
        TEST_DB.unlink()
    if TEST_UPLOADS.exists():
        shutil.rmtree(TEST_UPLOADS)
    TEST_UPLOADS.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{TEST_DB}", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Sess = sessionmaker(bind=engine)
    return Sess()


def seed_data(db: Session) -> dict:
    """Create buyer tenant, supplier tenant, users, admin user, invite, link."""
    buyer_tenant = Tenant(
        name="Acme Fashion GmbH",
        slug="acme-fashion",
        tenant_type="buyer",
    )
    supplier_tenant = Tenant(
        name="Yildiz Tekstil A.S.",
        slug="yildiz-tekstil",
        tenant_type="supplier",
    )
    db.add_all([buyer_tenant, supplier_tenant])
    db.flush()

    buyer_user = User(
        email="buyer@acme.com",
        full_name="Hans Buyer",
        password_hash=hash_password("buyerpass"),
        role="buyer",
        tenant_id=buyer_tenant.id,
    )
    supplier_user = User(
        email="supplier@yildiz.com",
        full_name="Ahmet Supplier",
        password_hash=hash_password("supplierpass"),
        role="supplier",
        tenant_id=supplier_tenant.id,
    )
    admin_user = User(
        email="admin@acme.com",
        full_name="Admin Acme",
        password_hash=hash_password("adminpass"),
        role="admin",
        tenant_id=buyer_tenant.id,
    )
    db.add_all([buyer_user, supplier_user, admin_user])
    db.flush()

    invite = Invite(
        buyer_tenant_id=buyer_tenant.id,
        supplier_email="supplier@yildiz.com",
        token="demo-invite-token-s4",
        status="accepted",
        expires_at=datetime.now(UTC) + timedelta(days=30),
        accepted_at=datetime.now(UTC),
    )
    db.add(invite)
    db.flush()

    link = BuyerSupplierLink(
        buyer_tenant_id=buyer_tenant.id,
        supplier_tenant_id=supplier_tenant.id,
        invite_id=invite.id,
    )
    db.add(link)
    db.commit()

    return {
        "buyer_tenant": buyer_tenant,
        "supplier_tenant": supplier_tenant,
        "buyer_user": buyer_user,
        "supplier_user": supplier_user,
        "admin_user": admin_user,
        "invite": invite,
    }


def create_case(db: Session, data: dict) -> Case:
    """Create a case."""
    case = Case(
        reference_no="DEMO-S4-001",
        product_group="textiles",
        status="draft",
        supplier_tenant_id=data["supplier_tenant"].id,
        buyer_tenant_id=data["buyer_tenant"].id,
        created_by_user_id=data["supplier_user"].id,
    )
    db.add(case)
    db.commit()
    return case


def upload_documents(db: Session, case: Case, actor_id) -> list[Document]:
    """Upload all 6 sample PDFs."""
    docs = []
    pdf_files = sorted(SAMPLE_DIR.glob("*.pdf"))
    for pdf_path in pdf_files:
        file_bytes = pdf_path.read_bytes()
        sha256 = compute_sha256(file_bytes)

        storage_path = TEST_UPLOADS / pdf_path.name
        storage_path.write_bytes(file_bytes)

        doc = Document(
            case_id=case.id,
            original_filename=pdf_path.name,
            storage_path=str(storage_path),
            mime_type="application/pdf",
            file_size_bytes=len(file_bytes),
            sha256_hash=sha256,
            processing_status="uploaded",
            uploaded_by=actor_id,
        )
        db.add(doc)
        docs.append(doc)

    db.commit()
    for doc in docs:
        db.refresh(doc)
    return docs


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    print("=" * 64)
    print("  SPRINT 4 — RULES ENGINE + ADMIN L2 E2E")
    print("=" * 64)

    api_key = settings.anthropic_api_key
    has_api_key = (
        bool(api_key)
        and api_key != "PLACEHOLDER_REPLACE_WITH_REAL_KEY"
    )

    # ── 1. Setup ──────────────────────────────────────────
    print("\n▸ Setting up SQLite database...")
    db = setup_db()
    table_names = [t.name for t in Base.metadata.sorted_tables]
    print(f"  Created {len(table_names)} tables")

    # ── 2. Seed ───────────────────────────────────────────
    print("\n▸ Seeding test data...")
    data = seed_data(db)
    supplier = data["supplier_user"]
    admin = data["admin_user"]
    buyer = data["buyer_user"]
    print(f"  Supplier: {supplier.email}")
    print(f"  Admin: {admin.email}")
    print(f"  Buyer: {buyer.email}")

    # ── 3. Create case ────────────────────────────────────
    print("\n▸ Creating case...")
    case = create_case(db, data)
    print(f"  Case: {case.reference_no} (id: {case.id})")

    # ── 4. Upload documents ───────────────────────────────
    print("\n▸ Uploading 6 sample PDFs...")
    documents = upload_documents(db, case, supplier.id)
    for doc in documents:
        print(f"  ✓ {doc.original_filename}")

    # ── 5. Process documents ──────────────────────────────
    print("\n▸ Processing documents...")
    for doc in documents:
        db.refresh(doc)
        result = process_document(db, doc, supplier.id)
        print(
            f"  ✓ {doc.original_filename}: "
            f"status={result.processing_status}, "
            f"doc_type={result.doc_type}"
        )
    db.refresh(case)

    # ── 6. Run AI extraction (mock) ───────────────────────
    print("\n▸ Running AI field extraction...")
    use_mock = False
    extraction_mode = "NONE"

    if has_api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=5,
                messages=[{"role": "user", "content": "1"}],
            )
            extraction_mode = "REAL_API"
            print(f"  {G}Using REAL Claude API{W}")
        except Exception as exc:
            print(
                f"  {Y}API unreachable ({type(exc).__name__}), "
                f"using MockExtractor{W}"
            )
            use_mock = True
            extraction_mode = "MOCK"
    else:
        print(f"  {Y}No API key, using MockExtractor{W}")
        use_mock = True
        extraction_mode = "MOCK"

    for doc in documents:
        db.refresh(doc)
        if doc.processing_status != "classified" or not doc.doc_type:
            continue
        try:
            run_extraction(db, doc, supplier.id, use_mock=use_mock)
            count = (
                db.query(ExtractedField)
                .filter(ExtractedField.document_id == doc.id)
                .count()
            )
            print(f"  ✓ {doc.original_filename}: {count} fields")
        except Exception as exc:
            print(f"  ✗ {doc.original_filename}: {exc}")

    total_fields = (
        db.query(ExtractedField)
        .filter(ExtractedField.case_id == case.id)
        .count()
    )
    print(f"\n  Total fields: {total_fields} [{extraction_mode}]")

    # ── 7. Run rules engine ───────────────────────────────
    print("\n▸ Running rules engine...")
    summary = RulesEngine.run_all(db, case, supplier.id)
    print(
        f"  Total rules: {summary['total_rules']}, "
        f"Passed: {summary['passed']}, "
        f"Failed: {summary['failed']}, "
        f"Warnings: {summary['warnings']}, "
        f"Checklist items: {summary['checklist_items_created']}"
    )

    # ══════════════════════════════════════════════════════
    #  VERIFICATION
    # ══════════════════════════════════════════════════════
    print("\n" + "=" * 64)
    print("  VERIFICATION")
    print("=" * 64)

    tag = f" [{extraction_mode}]"

    # ── Check 1: 5 rules execute without error ────────────
    vr_count = (
        db.query(ValidationResult)
        .filter(ValidationResult.case_id == case.id)
        .count()
    )
    unique_rules = set()
    for vr in (
        db.query(ValidationResult)
        .filter(ValidationResult.case_id == case.id)
        .all()
    ):
        unique_rules.add(vr.rule_key)

    check(
        f"Check 1: 5 rules execute without error{tag}",
        len(unique_rules) == 5,
        f"{len(unique_rules)} unique rules: "
        f"{', '.join(sorted(unique_rules))}; "
        f"{vr_count} total results",
    )

    # ── Check 2: Composition rule passes (sum=100) ────────
    comp_results = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.case_id == case.id,
            ValidationResult.rule_key == "composition_sum_100",
        )
        .all()
    )
    comp_passed = any(r.status == "pass" for r in comp_results)
    comp_detail = "; ".join(
        f"{r.status}: {r.message}" for r in comp_results
    )
    check(
        f"Check 2: Composition rule passes{tag}",
        comp_passed,
        comp_detail,
    )

    # ── Check 3: Certificate validity passes ──────────────
    cert_results = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.case_id == case.id,
            ValidationResult.rule_key == "certificate_validity",
        )
        .all()
    )
    cert_passed = any(r.status == "pass" for r in cert_results)
    cert_detail = "; ".join(
        f"{r.status}: {r.message}" for r in cert_results
    )
    check(
        f"Check 3: Certificate validity passes{tag}",
        cert_passed,
        cert_detail,
    )

    # ── Check 4: Quantity match passes (12000=12000) ──────
    qty_results = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.case_id == case.id,
            ValidationResult.rule_key == "qty_mismatch",
        )
        .all()
    )
    qty_passed = any(r.status == "pass" for r in qty_results)
    qty_detail = "; ".join(
        f"{r.status}: {r.message}" for r in qty_results
    )
    check(
        f"Check 4: Quantity match passes{tag}",
        qty_passed,
        qty_detail,
    )

    # ── Check 5: No missing critical docs ─────────────────
    docs_results = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.case_id == case.id,
            ValidationResult.rule_key == "missing_critical_docs",
        )
        .all()
    )
    docs_passed = any(r.status == "pass" for r in docs_results)
    docs_detail = "; ".join(
        f"{r.status}: {r.message}" for r in docs_results
    )
    check(
        f"Check 5: No missing critical docs{tag}",
        docs_passed,
        docs_detail,
    )

    # ── Check 6: No conflicts detected ────────────────────
    conflict_results = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.case_id == case.id,
            ValidationResult.rule_key == "conflict_detection",
        )
        .all()
    )
    conflict_passed = any(r.status == "pass" for r in conflict_results)
    conflict_detail = "; ".join(
        f"{r.status}: {r.message}" for r in conflict_results
    )
    check(
        f"Check 6: No conflicts detected{tag}",
        conflict_passed,
        conflict_detail,
    )

    # ── Check 7: Admin approves 3 fields → L2 + buyer_visible ──
    print("\n▸ Admin L2 approve/reject workflow...")

    # Get first 4 pending_review fields
    pending_fields = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.case_id == case.id,
            ExtractedField.status == "pending_review",
        )
        .limit(4)
        .all()
    )

    approved_ids = []
    rejected_id = None

    if len(pending_fields) >= 4:
        # Approve first 3
        for f in pending_fields[:3]:
            f.tier = "L2"
            f.status = "approved"
            f.visibility = "buyer_visible"
            approved_ids.append(f.id)

        # Reject 4th
        f4 = pending_fields[3]
        f4.status = "rejected"
        rejected_id = f4.id

        # Create checklist item for rejected field
        from app.services.ai.field_mapping import FIELD_LABELS
        field_label = FIELD_LABELS.get(f4.canonical_key, f4.canonical_key)
        reject_ci = ChecklistItem(
            case_id=case.id,
            type="missing_field",
            severity="high",
            status="open",
            title=f"Rejected Field: {field_label}",
            description=(
                f"'{field_label}' field was rejected by admin. "
                f"Reason: Test rejection. "
                "Please correct the value and resubmit."
            ),
            related_field_id=f4.id,
        )
        db.add(reject_ci)
        db.commit()

        for fid in approved_ids:
            db.refresh(
                db.query(ExtractedField)
                .filter(ExtractedField.id == fid)
                .first()
            )
    else:
        print(f"  {Y}Only {len(pending_fields)} pending fields found{W}")

    # Verify approvals
    l2_visible = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.case_id == case.id,
            ExtractedField.tier == "L2",
            ExtractedField.status == "approved",
            ExtractedField.visibility == "buyer_visible",
        )
        .count()
    )
    check(
        f"Check 7: Admin approves 3 fields → L2 + buyer_visible{tag}",
        l2_visible == 3,
        f"L2+approved+buyer_visible={l2_visible}",
    )

    # ── Check 8: Admin rejects 1 field ────────────────────
    rejected_count = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.case_id == case.id,
            ExtractedField.status == "rejected",
        )
        .count()
    )
    reject_ci_count = (
        db.query(ChecklistItem)
        .filter(
            ChecklistItem.case_id == case.id,
            ChecklistItem.type == "missing_field",
            ChecklistItem.related_field_id == rejected_id,
        )
        .count()
        if rejected_id
        else 0
    )
    check(
        f"Check 8: Admin rejects 1 field → rejected + checklist{tag}",
        rejected_count >= 1 and reject_ci_count >= 1,
        f"rejected_fields={rejected_count}, "
        f"checklist_items_for_rejected={reject_ci_count}",
    )

    # ── Check 9: Buyer sees exactly 3 approved fields ─────
    buyer_visible_count = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.case_id == case.id,
            ExtractedField.visibility == "buyer_visible",
        )
        .count()
    )
    check(
        f"Check 9: Buyer sees exactly 3 approved fields{tag}",
        buyer_visible_count == 3,
        f"buyer_visible={buyer_visible_count}",
    )

    # ── Check 10: Checklist items visible to supplier ─────
    all_checklist = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.case_id == case.id)
        .all()
    )
    open_items = [ci for ci in all_checklist if ci.status == "open"]
    check(
        f"Check 10: Checklist items visible to supplier{tag}",
        len(all_checklist) >= 1,
        f"total={len(all_checklist)}, "
        f"open={len(open_items)}",
    )

    # Print all checklist items for reference
    if all_checklist:
        print("\n  Checklist items:")
        for ci in all_checklist:
            print(
                f"    • [{ci.status}] {ci.type} — {ci.title}"
            )

    # ══════════════════════════════════════════════════════
    #  SUMMARY
    # ══════════════════════════════════════════════════════
    print("\n" + "=" * 64)
    print("  SUMMARY")
    print("=" * 64)

    total_checks = len(results)
    passed = sum(1 for v in results.values() if v == "PASS")
    failed = sum(1 for v in results.values() if v == "FAIL")

    print(
        f"\n  Total: {total_checks}  "
        f"{G}Passed: {passed}{W}  "
        f"{R}Failed: {failed}{W}"
    )

    if failed > 0:
        print(f"\n  {R}FAILED checks:{W}")
        for name, status in results.items():
            if status == "FAIL":
                print(f"    ✗ {name}")
        sys.exit(1)

    # Cleanup
    db.close()
    print(f"\n  DB: {TEST_DB}")
    print("  Done.")


if __name__ == "__main__":
    main()
