"""add checkin/checkout timestamps, audit and permission tables

Revision ID: c1d2e3f4a5b6
Revises: 537a6d4fee05
Create Date: 2026-04-22 14:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c1d2e3f4a5b6"
down_revision = "537a6d4fee05"
branch_labels = None
depends_on = None


def upgrade():
    # Add timestamp columns to bookings if they don't exist (safe for environments
    # where the columns may already have been added by a dev script).
    bind = op.get_bind()
    db_name = bind.execute(sa.text("SELECT DATABASE()")).scalar()
    for col in ("check_in_time", "check_out_time"):
        exists = bind.execute(
            sa.text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = :db AND TABLE_NAME = 'bookings' AND COLUMN_NAME = :col"
            ),
            {"db": db_name, "col": col},
        ).scalar()
        if not exists:
            with op.batch_alter_table("bookings", schema=None) as batch_op:
                batch_op.add_column(sa.Column(col, sa.DateTime(), nullable=True))

    # Create audit_logs, permissions and role_permissions tables if missing
    for tbl, ddl in [
        (
            "audit_logs",
            lambda: op.create_table(
                "audit_logs",
                sa.Column("id", sa.Integer(), primary_key=True),
                sa.Column("user_id", sa.Integer(), nullable=True),
                sa.Column("booking_id", sa.Integer(), nullable=True),
                sa.Column("action", sa.String(length=120), nullable=False),
                sa.Column("details", sa.Text(), nullable=True),
                sa.Column(
                    "created_at",
                    sa.DateTime(),
                    nullable=False,
                    server_default=sa.func.now(),
                ),
                mysql_engine="InnoDB",
            ),
        ),
        (
            "permissions",
            lambda: op.create_table(
                "permissions",
                sa.Column("id", sa.Integer(), primary_key=True),
                sa.Column("name", sa.String(length=120), nullable=False, unique=True),
                sa.Column("description", sa.Text(), nullable=True),
                mysql_engine="InnoDB",
            ),
        ),
        (
            "role_permissions",
            lambda: op.create_table(
                "role_permissions",
                sa.Column("id", sa.Integer(), primary_key=True),
                sa.Column("role_name", sa.String(length=80), nullable=False),
                sa.Column("permission", sa.String(length=120), nullable=False),
                mysql_engine="InnoDB",
            ),
        ),
    ]:
        exists = bind.execute(
            sa.text(
                "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :tbl"
            ),
            {"db": db_name, "tbl": tbl},
        ).scalar()
        if not exists:
            ddl()
        else:
            # already exists
            pass


def downgrade():
    # Drop role_permissions and permissions
    op.drop_table("role_permissions")
    op.drop_table("permissions")

    # Drop audit_logs
    op.drop_table("audit_logs")

    # Remove columns from bookings
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.drop_column("check_out_time")
        batch_op.drop_column("check_in_time")
