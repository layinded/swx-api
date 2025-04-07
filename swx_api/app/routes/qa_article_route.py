# Route generated based on controller and model.

import uuid

from fastapi import APIRouter, Request, Query
from sqlalchemy import text

from swx_api.app.controllers.qa_article_controller import QaArticleController
from swx_api.app.models.qa_article import QaArticleCreate, QaArticleUpdate, QaArticlePublic
from swx_api.app.models.qa_chunk import QAResponse
from swx_api.core.database.db import SessionDep

router = APIRouter(prefix="/qa_article")


@router.post("/ask")
def ask_with_rag(payload: dict, db: SessionDep):
    question = payload["question"]
    vectorizer_id = 1

    # Step 1: Retrieve top chunks
    sql_chunks = text("""
        SELECT chunk, source, url,
        1 - (embedding <#> ai.vectorizer_embed(:vectorizer_id, :question, 'text')) AS score
        FROM qa_chunk
        ORDER BY score DESC
        LIMIT 3
    """)
    results = db.execute(sql_chunks, {"vectorizer_id": vectorizer_id, "question": question}).fetchall()

    # Step 2: Build prompt from retrieved chunks
    context = "\n".join([f"{i + 1}. {r[0]}" for i, r in enumerate(results)])
    final_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    # Step 3: Generate answer with Ollama
    sql_llm = text("""
        SELECT ai.ollama_generate(
            model := 'phi',
            prompt := :prompt,
            host := :host
        )
    """)
    host = "http://host.docker.internal:11434"
    answer = db.execute(sql_llm, {"prompt": final_prompt, "host": host}).scalar()

    return {"answer": answer,
            "chunks": [{"text": r[0], "url": r[2], "source": r[1], "score": float(r[3])} for r in results]}


@router.post("/ollama/generate")
def generate_ollama_response(payload: dict, db: SessionDep):
    prompt = payload.get("prompt")
    sql = text("""
        SELECT ai.ollama_generate(
            model := 'phi',
            prompt := :prompt,
            host := 'http://host.docker.internal:11434',
            keep_alive := '5m',
            system_prompt := NULL,
            template := NULL,
            context := NULL,
            "verbose" := FALSE
        ) AS result
    """)
    result = db.execute(sql, {"prompt": prompt}).scalar()
    return {"response": result}


@router.post("/search", response_model=QAResponse)
def get_search(request: Request, db: SessionDep, payload: dict):
    return QaArticleController.retrieve_all_qa_article_search_resources(request, db, payload)


@router.get("/", response_model=list[QaArticlePublic],
            summary="Get all qa_article",
            description="Retrieve all qa_article resources with optional pagination")
def get_all(request: Request, db: SessionDep,
            skip: int = Query(0, description="Number of items to skip"),
            limit: int = Query(100, description="Maximum number of items to return")):
    return QaArticleController.retrieve_all_qa_article_resources(request, db, skip=skip, limit=limit)


@router.get("/{id}", response_model=QaArticlePublic,
            summary="Get qa_article by ID",
            description="Retrieve a single qa_article resource by its unique identifier")
def get_by_id(request: Request, id: uuid.UUID, db: SessionDep):
    return QaArticleController.retrieve_qa_article_by_id(request, id, db)


@router.post("/", response_model=QaArticlePublic, status_code=201,
             summary="Create new qa_article",
             description="Create a new qa_article resource")
def create(request: Request, data: QaArticleCreate, db: SessionDep):
    return QaArticleController.create_new_qa_article(request, data, db)


@router.put("/{id}", response_model=QaArticlePublic,
            summary="Update qa_article",
            description="Update an existing qa_article resource by ID")
def update(request: Request, id: uuid.UUID, data: QaArticleUpdate, db: SessionDep):
    return QaArticleController.update_existing_qa_article(request, id, data, db)


@router.delete("/{id}", status_code=204,
               summary="Delete qa_article",
               description="Delete an existing qa_article resource by ID")
def delete(request: Request, id: uuid.UUID, db: SessionDep):
    return QaArticleController.delete_existing_qa_article(request, id, db)
