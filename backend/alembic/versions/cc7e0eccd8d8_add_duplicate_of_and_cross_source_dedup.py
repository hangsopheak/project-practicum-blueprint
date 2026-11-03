"""add_duplicate_of_and_cross_source_dedup

Revision ID: cc7e0eccd8d8
Revises: 
Create Date: 2026-10-24 19:07:32.514515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc7e0eccd8d8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add duplicate_of, apply contacts, last_seen_at and unique constraint."""
    op.execute("""
        ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS duplicate_of INTEGER REFERENCES job_listings(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS ix_job_listings_duplicate_of ON job_listings(duplicate_of);
        ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS apply_email VARCHAR(255);
        ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS apply_phone VARCHAR(100);
        ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS apply_telegram VARCHAR(100);
        ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_job_listings_source_post_id'
            ) THEN
                ALTER TABLE job_listings ADD CONSTRAINT uq_job_listings_source_post_id UNIQUE (source, source_post_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        ALTER TABLE job_listings DROP CONSTRAINT IF EXISTS uq_job_listings_source_post_id;
        DROP INDEX IF EXISTS ix_job_listings_duplicate_of;
        ALTER TABLE job_listings DROP COLUMN IF EXISTS duplicate_of;
        ALTER TABLE job_listings DROP COLUMN IF EXISTS apply_email;
        ALTER TABLE job_listings DROP COLUMN IF EXISTS apply_phone;
        ALTER TABLE job_listings DROP COLUMN IF EXISTS apply_telegram;
        ALTER TABLE job_listings DROP COLUMN IF EXISTS last_seen_at;
    """)
