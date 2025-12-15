"""add hubspot_company_id to meetings

Revision ID: f8614df3c2cd
Revises: 001_add_is_active
Create Date: 2025-12-15 13:23:32.615894

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8614df3c2cd'
down_revision = '001_add_is_active'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "meetings",
        sa.Column("hubspot_company_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_meetings_hubspot_company_id",
        "meetings",
        ["hubspot_company_id"],
    )    


def downgrade():
    op.drop_index("ix_meetings_hubspot_company_id", table_name="meetings")
    op.drop_column("meetings", "hubspot_company_id")

