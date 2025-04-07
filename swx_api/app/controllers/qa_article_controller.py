# Controller generated based on model fields.

from swx_api.core.database.db import SessionDep
from swx_api.app.services.qa_article_service import QaArticleService
from swx_api.app.models.qa_article import QaArticleCreate, QaArticleUpdate, QaArticlePublic
from fastapi import HTTPException, Request
from swx_api.core.middleware.logging_middleware import logger
from swx_api.core.utils.language_helper import translate
import uuid


class QaArticleController:

    @staticmethod
    def retrieve_all_qa_article_search_resources(request: Request, db: SessionDep, payload: dict):
        """Retrieve all qa_article resources with pagination."""
        try:
            return QaArticleService.retrieve_all_qa_article_search_resources(db, payload)

        except Exception as e:
            logger.error("Error in retrieve_all_qa_article_search_resources: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def retrieve_all_qa_article_resources(request: Request, db: SessionDep, skip: int = 0, limit: int = 100):
        """Retrieve all qa_article resources with pagination."""
        try:
            return QaArticleService.retrieve_all_qa_article_resources(db, skip=skip, limit=limit)
        except Exception as e:
            logger.error("Error in retrieve_all_qa_article_resources: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def retrieve_qa_article_by_id(request: Request, id: uuid.UUID, db: SessionDep):
        """Retrieve a single qa_article resource by its ID."""
        item = QaArticleService.retrieve_qa_article_by_id(db, id)
        if not item:
            raise HTTPException(status_code=404, detail=translate(request, f"qa_article.not_found"))
        return item

    @staticmethod
    def create_new_qa_article(request: Request, data: QaArticleCreate, db: SessionDep):
        """Create a new qa_article resource."""
        try:
            return QaArticleService.create_new_qa_article(db, data)
        except Exception as e:
            logger.error("Error in create_new_qa_article: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def update_existing_qa_article(request: Request, id: uuid.UUID, data: QaArticleUpdate, db: SessionDep):
        """Update an existing qa_article resource."""
        item = QaArticleService.update_existing_qa_article(db, id, data)
        if not item:
            raise HTTPException(status_code=404, detail=translate(request, f"qa_article.not_found"))
        return item

    @staticmethod
    def delete_existing_qa_article(request: Request, id: uuid.UUID, db: SessionDep):
        """Delete an existing qa_article resource."""
        success = QaArticleService.delete_existing_qa_article(db, id)
        if not success:
            raise HTTPException(status_code=404, detail=translate(request, f"qa_article.not_found"))
        return None
