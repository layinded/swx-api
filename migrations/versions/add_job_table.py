"""add job table

Revision ID: add_job_table_001
Revises: add_policy_table_001
Create Date: 2026-01-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'add_job_table_001'
down_revision: Union[str, None] = 'add_policy_table_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create job table (sa.Enum with name='jobstatus' creates the PG type)
    # Do not CREATE TYPE explicitly; create_table creates it via the column.
    op.create_table(
        'job',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('job_type', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('status', sa.Enum('pending', 'queued', 'running', 'completed', 'failed', 'dead_letter', 'cancelled', name='jobstatus'), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_by', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_job_job_type', 'job', ['job_type'])
    op.create_index('ix_job_status', 'job', ['status'])
    op.create_index('ix_job_scheduled_at', 'job', ['scheduled_at'])
    op.create_index('ix_job_priority', 'job', ['priority'])
    op.create_index('idx_job_status_scheduled', 'job', ['status', 'scheduled_at'])
    op.create_index('idx_job_type_status', 'job', ['job_type', 'status'])


def downgrade() -> None:
    op.drop_index('idx_job_type_status', table_name='job')
    op.drop_index('idx_job_status_scheduled', table_name='job')
    op.drop_index('ix_job_priority', table_name='job')
    op.drop_index('ix_job_scheduled_at', table_name='job')
    op.drop_index('ix_job_status', table_name='job')
    op.drop_index('ix_job_job_type', table_name='job')
    op.drop_table('job')
    op.execute('DROP TYPE jobstatus')
