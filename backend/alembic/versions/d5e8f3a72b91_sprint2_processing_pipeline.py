"""sprint2_processing_pipeline

Revision ID: d5e8f3a72b91
Revises: b3f7a2e91d54
Create Date: 2026-02-16 23:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5e8f3a72b91"
down_revision: str | None = "b3f7a2e91d54"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Create document_pages table ---
    op.create_table(
        "document_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extraction_method", sa.String(20), nullable=False),
        sa.Column("char_count", sa.Integer(), server_default="0"),
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
        sa.UniqueConstraint("document_id", "page_number", name="uq_document_page"),
    )

    # --- Add error columns to documents ---
    op.add_column("documents", sa.Column("error_code", sa.String(50), nullable=True))
    op.add_column("documents", sa.Column("error_message", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "error_message")
    op.drop_column("documents", "error_code")
    op.drop_table("document_pages")
