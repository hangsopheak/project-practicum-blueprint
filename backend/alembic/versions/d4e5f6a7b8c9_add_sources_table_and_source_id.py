"""add_sources_table_and_source_id

Revision ID: d4e5f6a7b8c9
Revises: cc7e0eccd8d8
Create Date: 2026-11-02 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'cc7e0eccd8d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create sources table and add source_id to job_listings."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(50) NOT NULL,
            platform_type VARCHAR(50) NOT NULL,
            url TEXT NOT NULL,
            logo_url TEXT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            scrape_interval_minutes INTEGER NOT NULL DEFAULT 60,
            last_scraped_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ix_sources_name ON sources(name);
        CREATE UNIQUE INDEX IF NOT EXISTS ix_sources_code ON sources(code);
        CREATE INDEX IF NOT EXISTS ix_sources_id ON sources(id);

        ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS ix_job_listings_source_id ON job_listings(source_id);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        DROP INDEX IF EXISTS ix_job_listings_source_id;
        ALTER TABLE job_listings DROP COLUMN IF EXISTS source_id;
        DROP TABLE IF EXISTS sources CASCADE;
    """)

