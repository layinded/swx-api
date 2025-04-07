"""Add pgai and pgvector extensions

Revision ID: 7997f79106f4
Revises: a3b0fbc291c4
Create Date: 2025-03-21 16:46:32.881197

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = "7997f79106f4"
down_revision = 'a3b0fbc291c4'
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration changes.

    Add or modify database structures here.

    Example:
    op.add_column("users", sa.Column("new_column", sa.String(length=255), nullable=True))
    op.create_index("ix_users_new_column", "users", ["new_column"])
    """
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS ai CASCADE;")


def downgrade():
    """Rollback migration changes.

    Undo changes made in upgrade().

    Example:
    op.drop_index("ix_users_new_column", table_name="users")
    op.drop_column("users", "new_column")
    """
    op.execute("DROP EXTENSION IF EXISTS ai;")
    op.execute("DROP EXTENSION IF EXISTS vector;")
