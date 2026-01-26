"""Restore unique constraints dropped by 325a7c535a18

Migration 325 (add_audit_log) dropped several unique constraints and indexes.
Permission/role name uniques are kept via ix_permission_name, ix_role_name
(325 only drops _key constraints). This migration restores:
- admin_user provider_id unique index (325 explicitly drops it)
- role_permission (role_id, permission_id) unique
- team_member (team_id, user_id) unique

Revision ID: restore_uniques_001
Revises: add_job_table_001
Create Date: 2026-01-25

"""
from alembic import op

revision = "restore_uniques_001"
down_revision = "add_job_table_001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_admin_user_provider_id",
        "admin_user",
        ["provider_id"],
        unique=True,
    )
    op.create_unique_constraint(
        "uq_role_permission",
        "role_permission",
        ["role_id", "permission_id"],
    )
    op.create_unique_constraint(
        "uq_team_member",
        "team_member",
        ["team_id", "user_id"],
    )


def downgrade():
    op.drop_constraint("uq_team_member", "team_member", type_="unique")
    op.drop_constraint("uq_role_permission", "role_permission", type_="unique")
    op.drop_index("ix_admin_user_provider_id", table_name="admin_user")
