"""sprint1_cases_documents

Revision ID: b3f7a2e91d54
Revises: c24086d64ec8
Create Date: 2026-02-16 22:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3f7a2e91d54"
down_revision: str | None = "c24086d64ec8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Cases table: add new columns ---
    op.add_column(
        "cases",
        sa.Column(
            "buyer_tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=True,  # temporarily nullable for backfill
        ),
    )
    op.add_column(
        "cases",
        sa.Column("reference_no", sa.String(100), nullable=True),  # temporarily nullable
    )
    op.add_column(
        "cases",
        sa.Column(
            "product_group",
            sa.String(50),
            server_default=sa.text("'textiles'"),
            nullable=False,
        ),
    )
    op.add_column("cases", sa.Column("date_from", sa.Date(), nullable=True))
    op.add_column("cases", sa.Column("date_to", sa.Date(), nullable=True))

    # Rename description -> notes
    op.alter_column("cases", "description", new_column_name="notes")

    # Make title nullable
    op.alter_column("cases", "title", existing_type=sa.String(255), nullable=True)

    # Backfill existing rows (if any)
    op.execute("UPDATE cases SET reference_no = title WHERE reference_no IS NULL")
    op.execute(
        """
        UPDATE cases c SET buyer_tenant_id = (
            SELECT bsl.buyer_tenant_id FROM buyer_supplier_links bsl
            WHERE bsl.supplier_tenant_id = c.supplier_tenant_id LIMIT 1
        ) WHERE c.buyer_tenant_id IS NULL
        """
    )

    # Now enforce NOT NULL
    op.alter_column("cases", "reference_no", existing_type=sa.String(100), nullable=False)
    op.alter_column(
        "cases",
        "buyer_tenant_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    # --- Documents table: add new columns ---
    op.add_column("documents", sa.Column("sha256_hash", sa.String(64), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,  # temporarily nullable
        ),
    )

    # Backfill uploaded_by from case.created_by_user_id
    op.execute(
        """
        UPDATE documents d SET uploaded_by = (
            SELECT c.created_by_user_id FROM cases c WHERE c.id = d.case_id
        ) WHERE d.uploaded_by IS NULL
        """
    )
    op.alter_column(
        "documents",
        "uploaded_by",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    # --- Create audit_logs table ---
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")

    op.drop_column("documents", "uploaded_by")
    op.drop_column("documents", "sha256_hash")

    op.alter_column("cases", "title", existing_type=sa.String(255), nullable=False)
    op.alter_column("cases", "notes", new_column_name="description")
    op.drop_column("cases", "date_to")
    op.drop_column("cases", "date_from")
    op.drop_column("cases", "product_group")
    op.drop_column("cases", "reference_no")
    op.drop_column("cases", "buyer_tenant_id")
