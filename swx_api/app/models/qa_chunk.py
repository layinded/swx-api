# This model was generated using swx CLI.
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlmodel import SQLModel, Field

from swx_api.core.models.base import Base


class QaChunkBase(SQLModel):
    url: Optional[str] = Field(default=None)
    source: Optional[str] = Field(default=None)
    content: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    chunk: Optional[str] = Field(default=None)
    embedding_uuid: Optional[str] = Field(default=None)
    chunk_seq: Optional[str] = Field(default=None)


class QaChunk(QaChunkBase, table=False):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: Optional[str] = Field(default=None)


class QaChunkPublic(QaChunk):
    pass

class QaChunkResult(BaseModel):
    text: str
    source: Optional[str]
    url: Optional[str]
    score: float


class QAResponse(BaseModel):
    question: str
    chunks: List[QaChunkResult]
