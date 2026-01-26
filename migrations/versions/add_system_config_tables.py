"""Add system_config and system_config_history tables

Revision ID: add_system_config_001
Revises: restore_uniques_dropped_by_325
Create Date: 2026-01-26 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_system_config_001'
down_revision: Union[str, None] = 'restore_uniques_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create system_config table
    op.create_table(
        'system_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.String(length=5000), nullable=False),
        sa.Column('value_type', sa.String(length=20), nullable=False, server_default='string'),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_system_config_key'), 'system_config', ['key'], unique=True)
    op.create_index(op.f('ix_system_config_value_type'), 'system_config', ['value_type'], unique=False)
    op.create_index(op.f('ix_system_config_category'), 'system_config', ['category'], unique=False)
    op.create_index(op.f('ix_system_config_is_active'), 'system_config', ['is_active'], unique=False)
    
    # Create system_config_history table
    op.create_table(
        'system_config_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('old_value', sa.String(length=5000), nullable=True),
        sa.Column('new_value', sa.String(length=5000), nullable=False),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('change_reason', sa.String(length=500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['config_id'], ['system_config.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_system_config_history_config_id'), 'system_config_history', ['config_id'], unique=False)
    op.create_index(op.f('ix_system_config_history_key'), 'system_config_history', ['key'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_system_config_history_key'), table_name='system_config_history')
    op.drop_index(op.f('ix_system_config_history_config_id'), table_name='system_config_history')
    op.drop_table('system_config_history')
    op.drop_index(op.f('ix_system_config_is_active'), table_name='system_config')
    op.drop_index(op.f('ix_system_config_category'), table_name='system_config')
    op.drop_index(op.f('ix_system_config_value_type'), table_name='system_config')
    op.drop_index(op.f('ix_system_config_key'), table_name='system_config')
    op.drop_table('system_config')
