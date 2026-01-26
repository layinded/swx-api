from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from swx_app.services import qa_article_service as service
from swx_app.models.qa_article import QaArticleCreate, QaArticleUpdate, QaArticlePublic
from swx_core.middleware.logging_middleware import logger
from swx_core.utils.language_helper import translate


async def ask_rag_controller(db: AsyncSession, question: str) -> dict:
    """Controller for RAG-based question answering."""
    try:
        return await service.ask_rag_service(db, question)
    except Exception as e:
        logger.error("Error in ask_rag_controller: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def ollama_generate_controller(db: AsyncSession, prompt: str) -> dict:
    """Controller for generic Ollama generation."""
    try:
        return await service.ollama_generate_service(db, prompt)
    except Exception as e:
        logger.error("Error in ollama_generate_controller: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def retrieve_all_qa_article_search_resources(request: Request, db: AsyncSession, payload: dict) -> dict:
    """Retrieve search results."""
    try:
        return await service.retrieve_all_qa_article_search_resources(db, payload)
    except Exception as e:
        logger.error("Error in retrieve_all_qa_article_search_resources: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def retrieve_all_qa_article_resources(request: Request, db: AsyncSession, skip: int = 0, limit: int = 100) -> \
List[QaArticlePublic]:
    """Retrieve all qa_article resources with pagination."""
    try:
        return await service.retrieve_all_qa_article_resources(db, skip=skip, limit=limit)
    except Exception as e:
        logger.error("Error in retrieve_all_qa_article_resources: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def retrieve_qa_article_by_id(request: Request, id: UUID, db: AsyncSession) -> QaArticlePublic:
    """Retrieve a single qa_article resource by its ID."""
    item = await service.retrieve_qa_article_by_id(db, id)
    if not item:
        raise HTTPException(status_code=404, detail=translate(request, "qa_article.not_found"))
    return item


async def create_new_qa_article(request: Request, data: QaArticleCreate, db: AsyncSession) -> QaArticlePublic:
    """Create a new qa_article resource."""
    try:
        return await service.create_new_qa_article(db, data)
    except Exception as e:
        logger.error("Error in create_new_qa_article: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def update_existing_qa_article(request: Request, id: UUID, data: QaArticleUpdate,
                                     db: AsyncSession) -> QaArticlePublic:
    """Update an existing qa_article resource."""
    item = await service.update_existing_qa_article(db, id, data)
    if not item:
        raise HTTPException(status_code=404, detail=translate(request, "qa_article.not_found"))
    return item


async def delete_existing_qa_article(request: Request, id: UUID, db: AsyncSession) -> None:
    """Delete an existing qa_article resource."""
    success = await service.delete_existing_qa_article(db, id)
    if not success:
        raise HTTPException(status_code=404, detail=translate(request, "qa_article.not_found"))
    return None
