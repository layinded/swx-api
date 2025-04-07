# Service generated based on repository and model.

import uuid
from swx_api.core.database.db import SessionDep
from swx_api.app.repositories.qa_article_repository import QaArticleRepository
from swx_api.app.models.qa_article import QaArticleCreate, QaArticleUpdate


class QaArticleService:

    @staticmethod
    def retrieve_all_qa_article_search_resources(db: SessionDep, payload: dict):
        """Service layer: retrieve all qa_article resources."""
        return QaArticleRepository.retrieve_all_qa_article_search_resources(db, payload)

    @staticmethod
    def retrieve_all_qa_article_resources(db: SessionDep, skip: int = 0, limit: int = 100):
        """Service layer: retrieve all qa_article resources."""
        return QaArticleRepository.retrieve_all_qa_article_resources(db, skip=skip, limit=limit)

    @staticmethod
    def retrieve_qa_article_by_id(db: SessionDep, id: uuid.UUID):
        """Service layer: retrieve a single qa_article resource by ID."""
        return QaArticleRepository.retrieve_qa_article_by_id(db, id)

    @staticmethod
    def create_new_qa_article(db: SessionDep, data: QaArticleCreate):
        """Service layer: create a new qa_article resource."""
        return QaArticleRepository.create_new_qa_article(db, data)

    @staticmethod
    def update_existing_qa_article(db: SessionDep, id: uuid.UUID, data: QaArticleUpdate):
        """Service layer: update an existing qa_article resource."""
        return QaArticleRepository.update_existing_qa_article(db, id, data)

    @staticmethod
    def delete_existing_qa_article(db: SessionDep, id: uuid.UUID):
        """Service layer: delete an existing qa_article resource."""
        return QaArticleRepository.delete_existing_qa_article(db, id)
