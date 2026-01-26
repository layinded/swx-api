"""Add RBAC tables and admin_user table

Revision ID: add_rbac_admin_user
Revises: 105a5ba553bd
Create Date: 2024-12-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
import uuid
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_rbac_admin_user"
down_revision = "105a5ba553bd"
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration changes.

    Creates:
    - Permission table
    - Role table
    - RolePermission table (many-to-many)
    - UserRole table (many-to-many with optional team/resource scoping)
    - Team table
    - TeamMember table
    - AdminUser table (separate from User)
    """
    
    # Permission table
    op.create_table(
        "permission",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_permission_name", "permission", ["name"], unique=True)
    op.create_index("ix_permission_resource_type", "permission", ["resource_type"], unique=False)
    op.create_index("ix_permission_action", "permission", ["action"], unique=False)

    # Role table
    op.create_table(
        "role",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("is_system_role", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("domain", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_role_name", "role", ["name"], unique=True)
    op.create_index("ix_role_is_system_role", "role", ["is_system_role"], unique=False)
    op.create_index("ix_role_domain", "role", ["domain"], unique=False)

    # RolePermission table (many-to-many)
    op.create_table(
        "role_permission",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permission.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_index("ix_role_permission_role_id", "role_permission", ["role_id"], unique=False)
    op.create_index("ix_role_permission_permission_id", "role_permission", ["permission_id"], unique=False)

    # Team table (create before user_role to allow foreign key)
    op.create_table(
        "team",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_team_name", "team", ["name"], unique=False)
    op.create_index("ix_team_tenant_id", "team", ["tenant_id"], unique=False)

    # UserRole table (many-to-many with optional scoping)
    op.create_table(
        "user_role",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_role_user_id", "user_role", ["user_id"], unique=False)
    op.create_index("ix_user_role_role_id", "user_role", ["role_id"], unique=False)
    op.create_index("ix_user_role_team_id", "user_role", ["team_id"], unique=False)

    # TeamMember table
    op.create_table(
        "team_member",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_member"),
    )
    op.create_index("ix_team_member_team_id", "team_member", ["team_id"], unique=False)
    op.create_index("ix_team_member_user_id", "team_member", ["user_id"], unique=False)
    op.create_index("ix_team_member_role_id", "team_member", ["role_id"], unique=False)

    # AdminUser table (separate from User)
    op.create_table(
        "admin_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("auth_provider", sa.String(length=50), nullable=False, server_default="local"),
        sa.Column("provider_id", sa.String(length=255), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_admin_user_email", "admin_user", ["email"], unique=True)
    op.create_index("ix_admin_user_provider_id", "admin_user", ["provider_id"], unique=True)


def downgrade():
    """Rollback migration changes."""
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table("user_role")
    op.drop_table("team_member")
    op.drop_table("role_permission")
    op.drop_table("admin_user")
    op.drop_table("team")
    op.drop_table("role")
    op.drop_table("permission")
