"""Seed script for development/testing.

Creates:
- 1 buyer tenant + 1 buyer user (buyer@test.com / test1234)
- 1 admin user (admin@test.com / test1234, same tenant)
- 1 supplier tenant + 1 supplier user (supplier@test.com / test1234)
- 1 BuyerSupplierLink between buyer and supplier
- 1 accepted invite

Usage:
    cd backend
    source .venv/bin/activate
    python -m scripts.seed_dev
"""

import secrets
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add backend root to path so we can import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.auth import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.buyer_supplier_link import BuyerSupplierLink  # noqa: E402
from app.models.invite import Invite  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.user import User  # noqa: E402


def seed():
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).filter(User.email == "buyer@test.com").first():
            print("Database already seeded. Skipping.")
            return

        # Buyer tenant + user
        buyer_tenant = Tenant(name="Acme Imports GmbH", slug="acme-imports", tenant_type="buyer")
        db.add(buyer_tenant)
        db.flush()

        buyer_user = User(
            email="buyer@test.com",
            full_name="Maria Buyer",
            password_hash=hash_password("test1234"),
            role="buyer",
            tenant_id=buyer_tenant.id,
        )
        db.add(buyer_user)

        # Admin user (belongs to buyer tenant)
        admin_user = User(
            email="admin@test.com",
            full_name="Alex Admin",
            password_hash=hash_password("test1234"),
            role="admin",
            tenant_id=buyer_tenant.id,
        )
        db.add(admin_user)

        # Invite for supplier (marked as accepted)
        invite = Invite(
            buyer_tenant_id=buyer_tenant.id,
            supplier_email="supplier@test.com",
            token=secrets.token_urlsafe(32),
            status="accepted",
            expires_at=datetime.now(UTC) + timedelta(days=30),
            accepted_at=datetime.now(UTC),
        )
        db.add(invite)
        db.flush()

        # Supplier tenant + user (simulates accepted invite)
        supplier_tenant = Tenant(
            name="Anatolian Textiles",
            slug="anatolian-textiles",
            tenant_type="supplier",
        )
        db.add(supplier_tenant)
        db.flush()

        supplier_user = User(
            email="supplier@test.com",
            full_name="Ahmet Supplier",
            password_hash=hash_password("test1234"),
            role="supplier",
            tenant_id=supplier_tenant.id,
        )
        db.add(supplier_user)

        # BuyerSupplierLink
        link = BuyerSupplierLink(
            buyer_tenant_id=buyer_tenant.id,
            supplier_tenant_id=supplier_tenant.id,
            invite_id=invite.id,
        )
        db.add(link)

        db.commit()

        print("Seed data created successfully!")
        print("  Buyer:    buyer@test.com / test1234")
        print("  Admin:    admin@test.com / test1234")
        print("  Supplier: supplier@test.com / test1234")
        print(f"  Invite:   {invite.token} (accepted)")
        print("  BuyerSupplierLink: Acme Imports <-> Anatolian Textiles")

    except Exception as e:
        db.rollback()
        print(f"Error seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
