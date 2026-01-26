"""Add policy table

Revision ID: add_policy_table
Revises: 8d6de0d76cce
Create Date: 2026-01-25 20:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = 'add_policy_table_001'
down_revision = '8d6de0d76cce'
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration changes."""
    op.create_table('policy',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('policy_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('effect', sa.Enum('ALLOW', 'DENY', 'CONDITIONAL_ALLOW', name='policyeffect'), nullable=False),
    sa.Column('action_pattern', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('resource_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('owner', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_policy_policy_id'), 'policy', ['policy_id'], unique=True)
    op.create_index(op.f('ix_policy_action_pattern'), 'policy', ['action_pattern'], unique=False)
    op.create_index(op.f('ix_policy_resource_type'), 'policy', ['resource_type'], unique=False)
    op.create_index(op.f('ix_policy_priority'), 'policy', ['priority'], unique=False)
    op.create_index(op.f('ix_policy_enabled'), 'policy', ['enabled'], unique=False)


def downgrade():
    """Rollback migration changes."""
    op.drop_index(op.f('ix_policy_enabled'), table_name='policy')
    op.drop_index(op.f('ix_policy_priority'), table_name='policy')
    op.drop_index(op.f('ix_policy_resource_type'), table_name='policy')
    op.drop_index(op.f('ix_policy_action_pattern'), table_name='policy')
    op.drop_index(op.f('ix_policy_policy_id'), table_name='policy')
    op.drop_table('policy')
    op.execute('DROP TYPE IF EXISTS policyeffect')
