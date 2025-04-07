"""Create Chainlit tables: threads, steps, elements, feedbacks

Revision ID: c8216b666f9e
Revises: 105a5ba553bd
Create Date: 2025-04-05 20:28:26.286799

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
import uuid
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c8216b666f9e"
down_revision = '105a5ba553bd'
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration changes.

    Add or modify database structures here.

    Example:
    op.add_column("users", sa.Column("new_column", sa.String(length=255), nullable=True))
    op.create_index("ix_users_new_column", "users", ["new_column"])
    """
    # THREADS table
    op.create_table(
        'threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('createdAt', sa.Text()),
        sa.Column('name', sa.Text()),
        sa.Column('userId', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('userIdentifier', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text())),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['userId'], ['users.id'], ondelete='CASCADE')
    )

    # STEPS table
    op.create_table(
        'steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('threadId', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parentId', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('streaming', sa.Boolean(), nullable=False),
        sa.Column('waitForAnswer', sa.Boolean()),
        sa.Column('isError', sa.Boolean()),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text())),
        sa.Column('input', sa.Text()),
        sa.Column('output', sa.Text()),
        sa.Column('createdAt', sa.Text()),
        sa.Column('command', sa.Text()),
        sa.Column('start', sa.Text()),
        sa.Column('end', sa.Text()),
        sa.Column('generation', postgresql.JSONB()),
        sa.Column('showInput', sa.Text()),
        sa.Column('language', sa.Text()),
        sa.Column('indent', sa.Integer()),
        sa.ForeignKeyConstraint(['threadId'], ['threads.id'], ondelete='CASCADE')
    )

    # ELEMENTS table
    op.create_table(
        'elements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('threadId', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.Text()),
        sa.Column('url', sa.Text()),
        sa.Column('chainlitKey', sa.Text()),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('display', sa.Text()),
        sa.Column('objectKey', sa.Text()),
        sa.Column('size', sa.Text()),
        sa.Column('page', sa.Integer()),
        sa.Column('language', sa.Text()),
        sa.Column('forId', postgresql.UUID(as_uuid=True)),
        sa.Column('mime', sa.Text()),
        sa.Column('props', postgresql.JSONB()),
        sa.ForeignKeyConstraint(['threadId'], ['threads.id'], ondelete='CASCADE')
    )

    # FEEDBACKS table
    op.create_table(
        'feedbacks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('forId', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('threadId', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text()),
        sa.ForeignKeyConstraint(['threadId'], ['threads.id'], ondelete='CASCADE')
    )


def downgrade():
    """Rollback migration changes.

    Undo changes made in upgrade().

    Example:
    op.drop_index("ix_users_new_column", table_name="users")
    op.drop_column("users", "new_column")
    """
    op.drop_table('feedbacks')
    op.drop_table('elements')
    op.drop_table('steps')
    op.drop_table('threads')
