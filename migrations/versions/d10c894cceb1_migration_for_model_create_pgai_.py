"""Migration for model create pgAI vectorizer for qa_article

Revision ID: d10c894cceb1
Revises: cbd2b33666b6
Create Date: 2025-04-05 17:04:02.317335

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = "d10c894cceb1"
down_revision = 'cbd2b33666b6'
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration changes.

    Add or modify database structures here.

    Example:
    op.add_column("users", sa.Column("new_column", sa.String(length=255), nullable=True))
    op.create_index("ix_users_new_column", "users", ["new_column"])
    """
    conn = op.get_bind()
    
    # Check if ai extension and required functions exist
    check_ai = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_extension WHERE extname = 'ai'
        )
    """)).scalar()
    
    if not check_ai:
        print("⚠️  pgai extension not found, skipping vectorizer creation")
        return
    
    # Check if embedding_ollama function exists
    check_func = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'ai' AND p.proname = 'embedding_ollama'
        )
    """)).scalar()
    
    if not check_func:
        print("⚠️  ai.embedding_ollama function not found, skipping vectorizer creation")
        return
    
    # Check if vectorizer already exists
    check_vectorizer = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM ai.vectorizer WHERE destination_table = 'qa_chunk'
        )
    """)).scalar()
    
    if check_vectorizer:
        print("ℹ️  Vectorizer for qa_article already exists, skipping")
        return
    
    # Create vectorizer if all checks pass
    try:
        op.execute(text("""
            SELECT ai.create_vectorizer(
                'qa_article'::regclass,
                destination => 'qa_chunk',
                embedding => ai.embedding_ollama(
                    'nomic-embed-text',
                    768,
                    base_url := 'http://host.docker.internal:11434'
                ),
                processing => jsonb_build_object(
                    'config_type', 'processing',
                    'implementation', 'default',
                    'input_column', 'content'
                ),
                chunking => ai.chunking_recursive_character_text_splitter(
                    'content',
                    800,
                    200,
                    ARRAY['.', '?', '!', '\n', ' ']
                )
            );
        """))
        print("✅ Vectorizer created successfully")
    except Exception as e:
        print(f"⚠️  Failed to create vectorizer: {e}")
        print("   Migration will continue without vectorizer")


def downgrade():
    """Rollback migration changes.

    Undo changes made in upgrade().

    Example:
    op.drop_index("ix_users_new_column", table_name="users")
    op.drop_column("users", "new_column")
    """
    pass
