# Repository generated based on model fields.

import uuid
from typing import List

from sqlalchemy import text
from sqlmodel import select
from swx_api.core.database.db import SessionDep
from swx_api.app.models.qa_article import QaArticle, QaArticleCreate, QaArticleUpdate


class QaArticleRepository:

    @staticmethod
    def retrieve_all_qa_article_search_resources(db: SessionDep, payload: dict) -> List[dict]:
        question = payload["qa_article"]
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

        results = db.execute(sql, {"question": question, "vectorizer_id": vectorizer_id})
        return {
            "question": question,
            "chunks": [
                {
                    "text": result[0],
                    "source": result[1],
                    "url": result[2],
                    "score": round(float(result[3]), 4)
                }
                for result in results
            ]
        }

    @staticmethod
    def retrieve_all_qa_article_resources(db: SessionDep, skip: int = 0, limit: int = 100):
        """Retrieve all qa_article resources with pagination."""
        query = select(QaArticle).offset(skip).limit(limit)
        return db.exec(query).all()

    @staticmethod
    def retrieve_qa_article_by_id(db: SessionDep, id: uuid.UUID):
        """Retrieve a single qa_article resource by ID."""
        return db.get(QaArticle, id)

    @staticmethod
    def create_new_qa_article(db: SessionDep, data: QaArticleCreate):
        """Create a new qa_article resource in the database."""
        obj = QaArticle(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update_existing_qa_article(db: SessionDep, id: uuid.UUID, data: QaArticleUpdate):
        """Update an existing qa_article resource."""
        obj = db.get(QaArticle, id)
        if not obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_existing_qa_article(db: SessionDep, id: uuid.UUID):
        """Delete an existing qa_article resource."""
        obj = db.get(QaArticle, id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True
