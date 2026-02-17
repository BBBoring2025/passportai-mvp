"""sprint3_extraction_evidence

Revision ID: e7f9a4b83c12
Revises: d5e8f3a72b91
Create Date: 2026-02-17 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7f9a4b83c12"
down_revision: str | None = "d5e8f3a72b91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Add columns to extracted_fields ---

    # case_id: nullable initially for backfill, then NOT NULL
    op.add_column(
        "extracted_fields",
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # Backfill case_id from documents table
    op.execute(
        """
        UPDATE extracted_fields ef
        SET case_id = d.case_id
        FROM documents d
        WHERE ef.document_id = d.id
        AND ef.case_id IS NULL
        """
    )

    # Now make case_id NOT NULL and add FK
    op.alter_column(
        "extracted_fields",
        "case_id",
        nullable=False,
    )
    op.create_foreign_key(
        "fk_extracted_fields_case_id",
        "extracted_fields",
        "cases",
        ["case_id"],
        ["id"],
    )

    op.add_column(
        "extracted_fields",
        sa.Column(
            "tier",
            sa.String(10),
            nullable=False,
            server_default="L1",
        ),
    )
    op.add_column(
        "extracted_fields",
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="pending_review",
        ),
    )
    op.add_column(
        "extracted_fields",
        sa.Column(
            "visibility",
            sa.String(30),
            nullable=False,
            server_default="supplier_only",
        ),
    )

    # Composite index for case-level field queries
    op.create_index(
        "ix_extracted_fields_case_key",
        "extracted_fields",
        ["case_id", "canonical_key"],
    )

    # --- Create evidence_anchors table ---
    op.create_table(
        "evidence_anchors",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("extracted_fields.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column("page_no", sa.Integer(), nullable=False),
        sa.Column("snippet_text", sa.Text(), nullable=False),
        sa.Column("bbox", sa.Text(), nullable=True),
        sa.Column("snippet_hash", sa.String(64), nullable=True),
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
    op.drop_table("evidence_anchors")
    op.drop_index(
        "ix_extracted_fields_case_key",
        table_name="extracted_fields",
    )
    op.drop_column("extracted_fields", "visibility")
    op.drop_column("extracted_fields", "status")
    op.drop_column("extracted_fields", "tier")
    op.drop_constraint(
        "fk_extracted_fields_case_id",
        "extracted_fields",
        type_="foreignkey",
    )
    op.drop_column("extracted_fields", "case_id")
