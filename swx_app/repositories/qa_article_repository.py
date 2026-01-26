from typing import List, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from swx_app.models.qa_article import QaArticle, QaArticleCreate, QaArticleUpdate

async def retrieve_all_qa_article_search_resources(db: AsyncSession, question: str) -> dict:
    """Retrieve top chunks for a question using vector search."""
    vectorizer_id = 1
    sql = text("""
                SELECT
                    chunk,
                    source,
                    url,
                    1 - (
                        embedding <#> ai.vectorizer_embed(:vectorizer_id, :question, 'text')
                    ) AS score
                FROM qa_chunk
                ORDER BY score DESC
                LIMIT 5;
            """)

    result = await db.execute(sql, {"question": question, "vectorizer_id": vectorizer_id})
    results = result.fetchall()
    return {
        "question": question,
        "chunks": [
            {
                "text": row[0],
                "source": row[1],
                "url": row[2],
                "score": round(float(row[3]), 4)
            }
            for row in results
        ]
    }

async def retrieve_all_qa_article_resources(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[QaArticle]:
    """Retrieve all qa_article resources with pagination."""
    query = select(QaArticle).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def retrieve_qa_article_by_id(db: AsyncSession, id: UUID) -> Optional[QaArticle]:
    """Retrieve a single qa_article resource by ID."""
    return await db.get(QaArticle, id)

async def create_new_qa_article(db: AsyncSession, data: QaArticleCreate) -> QaArticle:
    """Create a new qa_article resource in the database."""
    obj = QaArticle(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def update_existing_qa_article(db: AsyncSession, id: UUID, data: QaArticleUpdate) -> Optional[QaArticle]:
    """Update an existing qa_article resource."""
    obj = await db.get(QaArticle, id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj

async def delete_existing_qa_article(db: AsyncSession, id: UUID) -> bool:
    """Delete an existing qa_article resource."""
    obj = await db.get(QaArticle, id)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True

async def execute_ollama_generate(db: AsyncSession, prompt: str, host: str = "http://host.docker.internal:11434") -> Optional[str]:
    """Execute Ollama generation using pgai."""
    sql = text("""
        SELECT ai.ollama_generate(
            model := 'phi',
            prompt := :prompt,
            host := :host,
            keep_alive := '5m'
        ) AS result
    """)
    result = await db.execute(sql, {"prompt": prompt, "host": host})
    scalar_result = result.scalar()
    return str(scalar_result) if scalar_result else None

async def retrieve_top_chunks(db: AsyncSession, question: str, limit: int = 3) -> List[dict]:
    """Retrieve top chunks for RAG."""
    vectorizer_id = 1
    sql = text("""
        SELECT chunk, source, url,
        1 - (embedding <#> ai.vectorizer_embed(:vectorizer_id, :question, 'text')) AS score
        FROM qa_chunk
        ORDER BY score DESC
        LIMIT :limit
    """)
    result = await db.execute(sql, {"vectorizer_id": vectorizer_id, "question": question, "limit": limit})
    results = result.fetchall()
    return [{"text": r[0], "source": r[1], "url": r[2], "score": float(r[3])} for r in results]
