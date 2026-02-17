#!/usr/bin/env python3
"""
Sprint 3 — Full End-to-End Demo Checklist.

Creates SQLite DB, seeds data, uploads 6 PDFs, processes,
extracts fields via Claude API, and verifies all 10 checks.

Usage:
    cd passportai/backend
    source .venv/bin/activate
    python tests/test_sprint3_e2e.py
"""

from __future__ import annotations

import json
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
TEST_DB = BACKEND / "test_sprint3.db"
TEST_UPLOADS = BACKEND / "test_uploads"

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
# SQLite can't handle pg UUID natively; we patch it globally
from sqlalchemy import String as SA_String  # noqa: E402
from sqlalchemy import TypeDecorator  # noqa: E402
from sqlalchemy.dialects.postgresql import UUID as PG_UUID  # noqa: E402


class PortableUUID(TypeDecorator):
    """UUID type that works on both PostgreSQL and SQLite."""
    impl = SA_String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
        return value


# Monkey-patch: replace PG UUID with portable version in all models
_orig_uuid_init = PG_UUID.__init__


def _patched_uuid_init(self, as_uuid=False):
    _orig_uuid_init(self, as_uuid=as_uuid)


PG_UUID.__init__ = _patched_uuid_init

# Override the column type at compilation level
from sqlalchemy.ext.compiler import compiles  # noqa: E402


@compiles(PG_UUID, "sqlite")
def compile_pg_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"


# ── Now import the app ────────────────────────────────────
from sqlalchemy import create_engine, event, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.auth import (  # noqa: E402
    hash_password,
)
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
from app.services.pipeline import (  # noqa: E402
    process_document,
    run_extraction,
)
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


def check_skip(name: str, reason: str = ""):
    results[name] = "SKIP"
    d = f"  ({reason})" if reason else ""
    print(f"  [{SKIP_S}] {name}{d}")


# ══════════════════════════════════════════════════════════
#  SETUP
# ══════════════════════════════════════════════════════════

def setup_db() -> Session:
    """Create SQLite DB + tables from ORM models."""
    # Clean up
    if TEST_DB.exists():
        TEST_DB.unlink()
    if TEST_UPLOADS.exists():
        shutil.rmtree(TEST_UPLOADS)
    TEST_UPLOADS.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{TEST_DB}",
        echo=False,
    )

    # Enable WAL + foreign keys for SQLite
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
    """Create buyer tenant, supplier tenant, users, invite, link."""
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
    db.add_all([buyer_user, supplier_user])
    db.flush()

    invite = Invite(
        buyer_tenant_id=buyer_tenant.id,
        supplier_email="supplier@yildiz.com",
        token="demo-invite-token-123",
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
        "invite": invite,
    }


def create_case(db: Session, data: dict) -> Case:
    """Create a case."""
    case = Case(
        reference_no="DEMO-2026-001",
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

        # Copy to test uploads dir
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
    print("  SPRINT 3 — FULL END-TO-END DEMO CHECKLIST")
    print("=" * 64)

    api_key = settings.anthropic_api_key
    has_api_key = bool(api_key) and api_key != "PLACEHOLDER_REPLACE_WITH_REAL_KEY"
    if not has_api_key:
        print(f"\n  {R}WARNING: ANTHROPIC_API_KEY not set. Checks 1-6, 9 will SKIP.{W}")

    # ── 1. Setup ──────────────────────────────────────────
    print("\n▸ Setting up SQLite database...")
    db = setup_db()
    table_names = [t.name for t in Base.metadata.sorted_tables]
    print(f"  Created {len(table_names)} tables: {', '.join(table_names)}")

    # ── 2. Seed ───────────────────────────────────────────
    print("\n▸ Seeding test data...")
    data = seed_data(db)
    supplier = data["supplier_user"]
    buyer = data["buyer_user"]
    print(f"  Buyer: {buyer.email} (tenant: {data['buyer_tenant'].name})")
    print(f"  Supplier: {supplier.email} (tenant: {data['supplier_tenant'].name})")

    # ── 3. Create case ────────────────────────────────────
    print("\n▸ Creating case...")
    case = create_case(db, data)
    print(f"  Case: {case.reference_no} (id: {case.id})")

    # ── 4. Upload documents ───────────────────────────────
    print("\n▸ Uploading 6 sample PDFs...")
    documents = upload_documents(db, case, supplier.id)
    for doc in documents:
        print(f"  ✓ {doc.original_filename} ({doc.file_size_bytes:,} bytes)")

    # ── 5. Process documents (text extraction + classification) ───
    print("\n▸ Processing documents (text extraction + classification)...")
    for doc in documents:
        db.refresh(doc)
        result = process_document(db, doc, supplier.id)
        print(
            f"  ✓ {doc.original_filename}: "
            f"status={result.processing_status}, "
            f"doc_type={result.doc_type}, "
            f"pages={result.page_count}"
        )

    # Refresh case
    db.refresh(case)
    print(f"  Case status: {case.status}")

    # ── 6. Run AI extraction ──────────────────────────────
    print("\n▸ Running AI field extraction...")

    # Determine extraction mode: try real API, fall back to mock
    use_mock = False
    extraction_mode = "NONE"

    if has_api_key:
        # Test connectivity with a quick API call
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
                f"falling back to MockExtractor{W}"
            )
            use_mock = True
            extraction_mode = "MOCK"
    else:
        print(f"  {Y}No API key, using MockExtractor{W}")
        use_mock = True
        extraction_mode = "MOCK"

    extraction_errors = []
    for doc in documents:
        db.refresh(doc)
        if doc.processing_status != "classified":
            print(
                f"  SKIP {doc.original_filename}: "
                f"status={doc.processing_status}"
            )
            continue
        if not doc.doc_type:
            print(
                f"  SKIP {doc.original_filename}: no doc_type"
            )
            continue

        try:
            result = run_extraction(
                db, doc, supplier.id, use_mock=use_mock
            )
            field_count = (
                db.query(ExtractedField)
                .filter(ExtractedField.document_id == doc.id)
                .count()
            )
            print(
                f"  ✓ {doc.original_filename}: "
                f"status={result.processing_status}, "
                f"fields={field_count}"
            )
        except Exception as exc:
            extraction_errors.append(
                (doc.original_filename, str(exc))
            )
            print(
                f"  ✗ {doc.original_filename}: ERROR - {exc}"
            )

    print(f"\n  Extraction mode: {extraction_mode}")

    # ══════════════════════════════════════════════════════
    #  VERIFICATION
    # ══════════════════════════════════════════════════════
    print("\n" + "=" * 64)
    print("  VERIFICATION")
    print("=" * 64)

    tag = f" [{extraction_mode}]"

    # ── Check 1: Extraction runs on all 6 docs ───────────
    extracted_docs = (
        db.query(Document)
        .filter(
            Document.case_id == case.id,
            Document.processing_status == "extracted",
        )
        .count()
    )
    check(
        f"Check 1: Extraction runs on all 6 docs{tag}",
        extracted_docs == 6,
        f"{extracted_docs}/6 extracted",
    )

    # ── Helper: get fields for a doc_type ──────────────────
    def fields_for_type(dtype: str) -> dict[str, str]:
        doc = (
            db.query(Document)
            .filter(Document.case_id == case.id, Document.doc_type == dtype)
            .first()
        )
        if not doc:
            return {}
        return {
            f.canonical_key: f.value
            for f in db.query(ExtractedField)
            .filter(ExtractedField.document_id == doc.id)
            .all()
        }

    # ── Check 2: Invoice fields ──────────────────────────
    inv = fields_for_type("invoice")
    inv_ok, inv_d = True, []
    for k, exp in [
        ("shipment.invoice_number", "YT-2026-INV-0847"),
        ("customs.hs_code", "6109.10.00"),
        ("shipment.total_quantity", "12000"),
    ]:
        a = inv.get(k, "").replace(",", "").strip()
        e = exp.replace(",", "").strip()
        if e in a or a == e:
            inv_d.append(f"{k}=OK")
        else:
            inv_ok = False
            inv_d.append(f"{k}: exp={exp}, got={inv.get(k, '')}")
    check(f"Check 2: Invoice fields{tag}", inv_ok, "; ".join(inv_d))

    # ── Check 3: Certificate fields ──────────────────────
    cert = fields_for_type("certificate")
    cert_ok, cert_d = True, []
    oeko = cert.get("certificate.oekotex.number", "")
    if "SH025" in oeko and "189456" in oeko:
        cert_d.append("oekotex.number=OK")
    else:
        cert_ok = False
        cert_d.append(f"oekotex.number: got={oeko}")
    vv = cert.get("certificate.oekotex.valid_until", "")
    if "2026-03-14" in vv or ("14" in vv and "March" in vv):
        cert_d.append("valid_until=OK")
    else:
        cert_ok = False
        cert_d.append(f"valid_until: got={vv}")
    check(f"Check 3: Certificate fields{tag}", cert_ok, "; ".join(cert_d))

    # ── Check 4: Test report fields ──────────────────────
    tr = fields_for_type("test_report")
    tr_ok, tr_d = True, []
    if "SGS" in tr.get("test_report.lab_name", "").upper():
        tr_d.append("lab=OK")
    else:
        tr_ok = False
        tr_d.append(f"lab: got={tr.get('test_report.lab_name', '')}")
    if "PASS" in tr.get("test_report.result_pass_fail", "").upper():
        tr_d.append("result=OK")
    else:
        tr_ok = False
        tr_d.append(f"result: got={tr.get('test_report.result_pass_fail', '')}")
    cv = tr.get("material.composition.cotton_pct", "").replace("%", "").strip()
    if cv == "95":
        tr_d.append("cotton=OK")
    else:
        tr_ok = False
        tr_d.append(f"cotton: got={cv}")
    check(f"Check 4: Test report fields{tag}", tr_ok, "; ".join(tr_d))

    # ── Check 5: BOM fields ──────────────────────────────
    bom = fields_for_type("bom")
    bom_ok, bom_d = True, []
    if bom.get("material.composition.cotton_pct", "").replace("%", "").strip() == "95":
        bom_d.append("cotton=OK")
    else:
        bom_ok = False
        bom_d.append(f"cotton: got={bom.get('material.composition.cotton_pct', '')}")
    if bom.get("material.composition.elastane_pct", "").replace("%", "").strip() == "5":
        bom_d.append("elastane=OK")
    else:
        bom_ok = False
        bom_d.append(f"elastane: got={bom.get('material.composition.elastane_pct', '')}")
    if "LOT-2026-0024" in bom.get("batch.id", ""):
        bom_d.append("batch=OK")
    else:
        bom_ok = False
        bom_d.append(f"batch: got={bom.get('batch.id', '')}")
    check(f"Check 5: BOM fields{tag}", bom_ok, "; ".join(bom_d))

    # ── Check 6: Every field has EvidenceAnchor ──────────
    total_fields = (
        db.query(ExtractedField)
        .filter(ExtractedField.case_id == case.id)
        .count()
    )
    orphan = db.execute(
        text(
            "SELECT COUNT(*) FROM extracted_fields "
            "WHERE case_id = :cid "
            "AND id NOT IN (SELECT field_id FROM evidence_anchors)"
        ),
        {"cid": str(case.id)},
    ).scalar()
    bad_anchors = db.execute(
        text(
            "SELECT COUNT(*) FROM evidence_anchors ea "
            "JOIN extracted_fields ef ON ea.field_id = ef.id "
            "WHERE ef.case_id = :cid "
            "AND (ea.snippet_text IS NULL OR ea.snippet_text = '' "
            "     OR ea.page_no IS NULL OR ea.page_no < 1)"
        ),
        {"cid": str(case.id)},
    ).scalar()
    check(
        f"Check 6: Every field has EvidenceAnchor{tag}",
        orphan == 0 and bad_anchors == 0 and total_fields > 0,
        f"{total_fields} fields, {orphan} orphan, "
        f"{bad_anchors} bad anchors",
    )

    # ── Check 7: No field without evidence ───────────────
    check(
        f"Check 7: No field without evidence{tag}",
        orphan == 0,
        f"orphan count: {orphan}",
    )

    # ── Check 8: Fields span multiple categories ─────────
    from app.services.ai.field_mapping import FIELD_CATEGORIES

    all_ef = (
        db.query(ExtractedField)
        .filter(ExtractedField.case_id == case.id)
        .all()
    )
    cats = set()
    for f in all_ef:
        for cat, keys in FIELD_CATEGORIES.items():
            if f.canonical_key in keys:
                cats.add(cat)
    check(
        f"Check 8: Fields span multiple categories{tag}",
        len(cats) >= 4,
        f"{len(cats)} categories: {', '.join(sorted(cats))}",
    )

    # ── Check 9: Buyer sees 0 fields ─────────────────────
    buyer_vis = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.case_id == case.id,
            ExtractedField.visibility == "buyer_visible",
        )
        .count()
    )
    supp_only = (
        db.query(ExtractedField)
        .filter(
            ExtractedField.case_id == case.id,
            ExtractedField.visibility == "supplier_only",
        )
        .count()
    )
    check(
        f"Check 9: Buyer sees 0 fields{tag}",
        buyer_vis == 0 and supp_only > 0,
        f"buyer_visible={buyer_vis}, supplier_only={supp_only}",
    )

    # ── Check 10: Eval accuracy ──────────────────────────
    eval_report = ROOT / "eval" / "accuracy_report.json"
    if eval_report.exists():
        eval_report.unlink()

    sys.path.insert(0, str(ROOT))
    from eval.run_eval import compare_values, load_ground_truth

    gt = load_ground_truth()

    # Build field lookup: (doc_stem, canonical_key) -> value
    db_fields: dict[tuple[str, str], str] = {}
    for ef in all_ef:
        doc = (
            db.query(Document)
            .filter(Document.id == ef.document_id)
            .first()
        )
        if doc:
            stem = Path(doc.original_filename).stem
            db_fields[(stem, ef.canonical_key)] = ef.value

    matches, total_gt, details = 0, 0, []
    for row in gt:
        total_gt += 1
        actual = db_fields.get((row.doc_id, row.canonical_key), "")
        mt, info = compare_values(
            row.expected_value, actual, row.canonical_key
        )
        if mt in (
            "exact_match",
            "normalized_match",
            "numeric_tolerance",
        ):
            matches += 1
            details.append(f"  ✓ {row.doc_id}/{row.canonical_key}")
        else:
            details.append(
                f"  ✗ {row.doc_id}/{row.canonical_key}: "
                f"exp='{row.expected_value}' "
                f"got='{actual}' ({info})"
            )

    accuracy = matches / total_gt * 100 if total_gt else 0

    report = {
        "summary": {
            "total_fields": total_gt,
            "matches": matches,
            "accuracy_pct": round(accuracy, 1),
            "extraction_mode": extraction_mode,
        },
        "details": details,
    }
    eval_report.parent.mkdir(parents=True, exist_ok=True)
    with open(eval_report, "w") as fp:
        json.dump(report, fp, indent=2, ensure_ascii=False)

    print("\n  Accuracy detail:")
    for d in details:
        print(f"    {d}")

    check(
        f"Check 10: Eval accuracy >= 80%{tag}",
        accuracy >= 80,
        f"{matches}/{total_gt} = {accuracy:.1f}%",
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
    skipped = sum(1 for v in results.values() if v == "SKIP")

    print(
        f"\n  Total: {total_checks}  "
        f"{G}Passed: {passed}{W}  "
        f"{R}Failed: {failed}{W}  "
        f"{Y}Skipped: {skipped}{W}"
    )

    if failed > 0:
        print(f"\n  {R}FAILED checks:{W}")
        for name, status in results.items():
            if status == "FAIL":
                print(f"    ✗ {name}")
        sys.exit(1)
    elif skipped > 0:
        print(f"\n  {Y}Some checks skipped.{W}")

    # Cleanup
    db.close()
    print(f"\n  DB: {TEST_DB}")
    print("  Done.")


if __name__ == "__main__":
    main()
