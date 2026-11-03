"""add_jev_classification_columns

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-02 12:00:00.000000

Adds Jev-powered job classification columns to job_listings.
All changes are additive (backward-compatible). Existing rows get NULL/defaults.

New columns:
  - job_category          VARCHAR(100) DEFAULT 'Unknown'
  - job_subcategory       VARCHAR(100) DEFAULT 'Unknown'
  - job_level             VARCHAR(50)  DEFAULT 'Unknown'
  - classification_confidence  FLOAT   DEFAULT NULL
  - classification_source VARCHAR(20)  DEFAULT 'rule'
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Jev classification columns to job_listings. Safe to re-run."""
    op.execute("""
        ALTER TABLE job_listings
            ADD COLUMN IF NOT EXISTS job_category          VARCHAR(100) NOT NULL DEFAULT 'Unknown',
            ADD COLUMN IF NOT EXISTS job_subcategory       VARCHAR(100) NOT NULL DEFAULT 'Unknown',
            ADD COLUMN IF NOT EXISTS job_level             VARCHAR(50)  NOT NULL DEFAULT 'Unknown',
            ADD COLUMN IF NOT EXISTS classification_confidence FLOAT DEFAULT NULL,
            ADD COLUMN IF NOT EXISTS classification_source VARCHAR(20)  NOT NULL DEFAULT 'rule';

        CREATE INDEX IF NOT EXISTS ix_job_listings_job_category
            ON job_listings(job_category);
        CREATE INDEX IF NOT EXISTS ix_job_listings_job_level
            ON job_listings(job_level);
    """)


def downgrade() -> None:
    """Remove Jev classification columns (rollback)."""
    op.execute("""
        DROP INDEX IF EXISTS ix_job_listings_job_category;
        DROP INDEX IF EXISTS ix_job_listings_job_level;
        ALTER TABLE job_listings
            DROP COLUMN IF EXISTS job_category,
            DROP COLUMN IF EXISTS job_subcategory,
            DROP COLUMN IF EXISTS job_level,
            DROP COLUMN IF EXISTS classification_confidence,
            DROP COLUMN IF EXISTS classification_source;
    """)

