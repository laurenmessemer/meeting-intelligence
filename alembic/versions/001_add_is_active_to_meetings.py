"""add is_active to meetings

Revision ID: 001_add_is_active
Revises: 
Create Date: 2025-01-27 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_add_is_active"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "meetings",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )
    op.create_index(
        "ix_meetings_is_active",
        "meetings",
        ["is_active"],
    )


def downgrade():
    op.drop_index("ix_meetings_is_active", table_name="meetings")
    op.drop_column("meetings", "is_active")
