# This model was generated using swx CLI.

from typing import Optional
from sqlmodel import SQLModel, Field
from swx_api.core.models.base import Base
from datetime import datetime
from uuid import UUID, uuid4

class QaArticleBase(Base):
    url: Optional[str] = Field(default=None)
    source: Optional[str] = Field(default=None)
    content: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QaArticle(QaArticleBase, table=True):
    __tablename__ = "qa_article"
    __table_args__ = {"extend_existing": True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: Optional[str] = Field(default=None)


class QaArticleCreate(SQLModel):
    title: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    content: Optional[str] = None
    created_at: Optional[datetime] = None


class QaArticleUpdate(SQLModel):
    title: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    content: Optional[str] = None
    created_at: Optional[datetime] = None


class QaArticlePublic(QaArticle):
    pass
