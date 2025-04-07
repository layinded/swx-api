"""Rename user table to users and add Chainlit fields

Revision ID: 105a5ba553bd
Revises: d10c894cceb1
Create Date: 2025-04-05 22:14:48.491338

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "105a5ba553bd"
down_revision = 'd10c894cceb1'
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration changes.

    Add or modify database structures here.

    Example:
    op.add_column("users", sa.Column("new_column", sa.String(length=255), nullable=True))
    op.create_index("ix_users_new_column", "users", ["new_column"])
    """
    # Ensure table is renamed (skip if already renamed)
    conn = op.get_bind()
    result = conn.execute(text("SELECT to_regclass('users')")).scalar()  # ✅ fixed
    if result is None:
        op.rename_table('user', 'users')

    # Add new columns
    op.add_column('users', sa.Column('identifier', sa.Text(), unique=True))
    op.add_column('users', sa.Column('metadata', sa.dialects.postgresql.JSONB(), nullable=False, server_default='{}'))
    op.add_column('users', sa.Column('createdAt', sa.Text()))

    # Backfill identifier with email
    op.execute("""
            UPDATE users
            SET identifier = email
            WHERE identifier IS NULL;
        """)


def downgrade():
    """Rollback migration changes.

    Undo changes made in upgrade().

    Example:
    op.drop_index("ix_users_new_column", table_name="users")
    op.drop_column("users", "new_column")
    """
    # Drop the Chainlit-related fields
    op.drop_column('users', 'createdAt')
    op.drop_column('users', 'metadata')
    op.drop_column('users', 'identifier')

    # Optional: rename table back
    # op.rename_table('users', 'user')
