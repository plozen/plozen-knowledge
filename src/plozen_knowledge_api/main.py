from __future__ import annotations

import hmac
from pathlib import PurePath
from functools import lru_cache

import uvicorn
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile

from .chunking import MarkdownChunker, hash_text
from .config import Settings, get_settings
from .database import Database
from .embeddings import build_embedding_provider
from .repositories import KnowledgeRepository
from .schemas import (
    AuditLogResponse,
    ChunkResponse,
    DocumentSummary,
    IngestDocumentRequest,
    IngestDocumentResponse,
    SearchRequest,
    SearchResponse,
)
from .services import KnowledgeService


@lru_cache
def settings() -> Settings:
    return get_settings()


@lru_cache
def service() -> KnowledgeService:
    current_settings = settings()
    database = Database(current_settings)
    repository = KnowledgeRepository(database)
    chunker = MarkdownChunker(
        chunk_size=current_settings.chunk_size,
        chunk_overlap=current_settings.chunk_overlap,
    )
    embedding_provider = build_embedding_provider(current_settings)
    return KnowledgeService(
        repository=repository,
        chunker=chunker,
        embedding_provider=embedding_provider,
    )


app = FastAPI(
    title="PLOZEN Knowledge API",
    version="0.1.0",
    description="RAG ingest, chunking, embedding, and pgvector search API.",
)


def require_api_key(x_knowledge_api_key: str | None = Header(default=None)) -> None:
    current_settings = settings()
    expected_key = current_settings.knowledge_api_key
    if expected_key and hmac.compare_digest(x_knowledge_api_key or "", expected_key):
        return
    if not expected_key and current_settings.allow_unauthenticated_dev:
        return
    raise HTTPException(status_code=401, detail="Invalid or missing API key")


def build_upload_source_uri(filename: str, content: str) -> str:
    safe_name = PurePath(filename).name or "uploaded-document"
    return f"upload://{hash_text(content)[:16]}/{safe_name}"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "plozen-knowledge-api"}


@app.post(
    "/documents/ingest",
    response_model=IngestDocumentResponse,
    dependencies=[Depends(require_api_key)],
)
def ingest_document(payload: IngestDocumentRequest) -> dict[str, object]:
    try:
        return service().ingest_document(
            source_type=payload.source_type,
            source_uri=payload.source_uri,
            title=payload.title,
            content=payload.content,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/documents/upload",
    response_model=IngestDocumentResponse,
    dependencies=[Depends(require_api_key)],
)
async def upload_document(
    file: UploadFile = File(...),
    source_type: str = Form("uploaded_file"),
    source_uri: str | None = Form(None),
    title: str | None = Form(None),
) -> dict[str, object]:
    filename = file.filename or "uploaded-document"
    if not filename.endswith((".md", ".txt")):
        raise HTTPException(status_code=400, detail="Only .md and .txt files are supported")

    raw_content = await file.read()
    try:
        content = raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text") from exc

    return service().ingest_document(
        source_type=source_type,
        source_uri=source_uri or build_upload_source_uri(filename, content),
        title=title or filename,
        content=content,
        metadata={"filename": filename, "content_type": file.content_type},
    )


@app.get(
    "/documents",
    response_model=list[DocumentSummary],
    dependencies=[Depends(require_api_key)],
)
def list_documents() -> list[dict[str, object]]:
    return service().repository.list_documents()


@app.get(
    "/documents/{source_id}/chunks",
    response_model=list[ChunkResponse],
    dependencies=[Depends(require_api_key)],
)
def list_chunks(source_id: str) -> list[dict[str, object]]:
    return service().repository.list_chunks(source_id)


@app.post(
    "/search",
    response_model=SearchResponse,
    dependencies=[Depends(require_api_key)],
)
def search(payload: SearchRequest) -> dict[str, object]:
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")
    return service().search(
        query=payload.query,
        top_k=payload.top_k,
        filters=payload.filters.model_dump(exclude_none=True),
    )


@app.get(
    "/search/audit-logs",
    response_model=list[AuditLogResponse],
    dependencies=[Depends(require_api_key)],
)
def list_audit_logs(limit: int = 20) -> list[dict[str, object]]:
    safe_limit = min(max(limit, 1), 100)
    return service().repository.list_audit_logs(limit=safe_limit)


if __name__ == "__main__":
    current_settings = settings()
    uvicorn.run(app, host=current_settings.api_host, port=current_settings.api_port)
