"""created_at columns to TIMESTAMP WITH TIME ZONE (UTC).

Revision ID: 0003_timestamptz
Revises: 0002_analysis_results
Create Date: 2026-03-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_timestamptz"
down_revision = "0002_analysis_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE "
            "USING created_at AT TIME ZONE 'UTC'"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE analysis_datasets ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE "
            "USING created_at AT TIME ZONE 'UTC'"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE analysis_results ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE "
            "USING created_at AT TIME ZONE 'UTC'"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE insight_blocks ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE "
            "USING created_at AT TIME ZONE 'UTC'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE "
            "USING (created_at AT TIME ZONE 'UTC')"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE analysis_datasets ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE "
            "USING (created_at AT TIME ZONE 'UTC')"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE analysis_results ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE "
            "USING (created_at AT TIME ZONE 'UTC')"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE insight_blocks ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE "
            "USING (created_at AT TIME ZONE 'UTC')"
        )
    )
