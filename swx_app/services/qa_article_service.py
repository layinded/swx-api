from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from swx_app.repositories import qa_article_repository as repo
from swx_app.models.qa_article import QaArticle, QaArticleCreate, QaArticleUpdate

async def ask_rag_service(db: AsyncSession, question: str) -> dict:
    """Service layer for RAG-based question answering."""
    # 1. Retrieve top chunks
    chunks = await repo.retrieve_top_chunks(db, question, limit=3)
    
    # 2. Build prompt
    context = "\n".join([f"{i + 1}. {c['text']}" for i, c in enumerate(chunks)])
    final_prompt = f"Context:\n{context}\n\nQuestion: {question}"
    
    # 3. Generate answer
    answer = await repo.execute_ollama_generate(db, final_prompt)
    
    return {
        "answer": answer,
        "chunks": chunks
    }

async def ollama_generate_service(db: AsyncSession, prompt: str) -> dict:
    """Service layer for generic Ollama generation."""
    response = await repo.execute_ollama_generate(db, prompt)
    return {"response": response}

async def retrieve_all_qa_article_search_resources(db: AsyncSession, payload: dict) -> dict:
    """Service layer: retrieve all qa_article resources."""
    question = payload.get("qa_article", "")
    return await repo.retrieve_all_qa_article_search_resources(db, question)

async def retrieve_all_qa_article_resources(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[QaArticle]:
    """Service layer: retrieve all qa_article resources."""
    return await repo.retrieve_all_qa_article_resources(db, skip=skip, limit=limit)

async def retrieve_qa_article_by_id(db: AsyncSession, id: UUID) -> Optional[QaArticle]:
    """Service layer: retrieve a single qa_article resource by ID."""
    return await repo.retrieve_qa_article_by_id(db, id)

async def create_new_qa_article(db: AsyncSession, data: QaArticleCreate) -> QaArticle:
    """Service layer: create a new qa_article resource."""
    return await repo.create_new_qa_article(db, data)

async def update_existing_qa_article(db: AsyncSession, id: UUID, data: QaArticleUpdate) -> Optional[QaArticle]:
    """Service layer: update an existing qa_article resource."""
    return await repo.update_existing_qa_article(db, id, data)

async def delete_existing_qa_article(db: AsyncSession, id: UUID) -> bool:
    """Service layer: delete an existing qa_article resource."""
    return await repo.delete_existing_qa_article(db, id)
