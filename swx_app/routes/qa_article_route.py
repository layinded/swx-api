# Route generated based on controller and model.

import uuid
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Request, Query
from swx_app.controllers import qa_article_controller as controller
from swx_app.models.qa_article import QaArticleCreate, QaArticleUpdate, QaArticlePublic
from swx_app.models.qa_chunk import QAResponse
from swx_core.database.db import SessionDep

router = APIRouter(prefix="/qa_article")

class AskRequest(BaseModel):
    question: str

class GenerateRequest(BaseModel):
    prompt: str

@router.post("/ask")
async def ask_with_rag(payload: AskRequest, db: SessionDep):
    return await controller.ask_rag_controller(db, payload.question)

@router.post("/ollama/generate")
async def generate_ollama_response(payload: GenerateRequest, db: SessionDep):
    return await controller.ollama_generate_controller(db, payload.prompt)

@router.post("/search", response_model=QAResponse)
async def get_search(request: Request, db: SessionDep, payload: dict):
    return await controller.retrieve_all_qa_article_search_resources(request, db, payload)

@router.get("/", response_model=List[QaArticlePublic],
            summary="Get all qa_article",
            description="Retrieve all qa_article resources with optional pagination")
async def get_all(request: Request, db: SessionDep,
            skip: int = Query(0, description="Number of items to skip"),
            limit: int = Query(100, description="Maximum number of items to return")):
    return await controller.retrieve_all_qa_article_resources(request, db, skip=skip, limit=limit)

@router.get("/{id}", response_model=QaArticlePublic,
            summary="Get qa_article by ID",
            description="Retrieve a single qa_article resource by its unique identifier")
async def get_by_id(request: Request, id: uuid.UUID, db: SessionDep):
    return await controller.retrieve_qa_article_by_id(request, id, db)

@router.post("/", response_model=QaArticlePublic, status_code=201,
             summary="Create new qa_article",
             description="Create a new qa_article resource")
async def create(request: Request, data: QaArticleCreate, db: SessionDep):
    return await controller.create_new_qa_article(request, data, db)

@router.put("/{id}", response_model=QaArticlePublic,
            summary="Update qa_article",
            description="Update an existing qa_article resource by ID")
async def update(request: Request, id: uuid.UUID, data: QaArticleUpdate, db: SessionDep):
    return await controller.update_existing_qa_article(request, id, data, db)

@router.delete("/{id}", status_code=204,
               summary="Delete qa_article",
               description="Delete an existing qa_article resource by ID")
async def delete(request: Request, id: uuid.UUID, db: SessionDep):
    return await controller.delete_existing_qa_article(request, id, db)
