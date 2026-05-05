"""Add check_in_time and check_out_time columns to bookings

Revision ID: 001_add_checkin_checkout_times
Revises: 
Create Date: 2026-05-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_checkin_checkout_times'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add check_in_time column
    op.add_column('bookings', sa.Column('check_in_time', sa.DateTime(), nullable=True))
    # Add check_out_time column
    op.add_column('bookings', sa.Column('check_out_time', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove columns on downgrade
    op.drop_column('bookings', 'check_out_time')
    op.drop_column('bookings', 'check_in_time')
