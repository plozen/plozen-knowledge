from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    source_type: str | None = None
    project: str | None = None

    model_config = {"extra": "forbid"}


class IngestDocumentRequest(BaseModel):
    source_type: str = Field(..., examples=["obsidian_note"])
    source_uri: str = Field(..., examples=["obsidian://PLOZEN/Knowledge.md"])
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestDocumentResponse(BaseModel):
    source_id: str
    status: str
    chunk_count: int
    source_hash: str


class DocumentSummary(BaseModel):
    id: str
    source_type: str
    source_uri: str
    title: str
    source_hash: str | None
    metadata: dict[str, Any]
    ingested_at: str
    updated_at: str
    chunk_count: int


class ChunkResponse(BaseModel):
    id: str
    source_id: str
    chunk_index: int
    content: str
    token_count: int
    content_hash: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    filters: SearchFilters = Field(default_factory=SearchFilters)


class SearchResult(BaseModel):
    chunk_id: str
    source_id: str
    source_type: str
    source_uri: str
    title: str
    chunk_index: int
    content: str
    token_count: int
    metadata: dict[str, Any]
    distance: float
    score: float


class SearchResponse(BaseModel):
    query: str
    top_k: int
    match_count: int
    latency_ms: int
    results: list[SearchResult]


class AuditLogResponse(BaseModel):
    id: str
    query_text: str
    tool_name: str
    top_k: int
    match_count: int
    filters: dict[str, Any]
    latency_ms: int | None
    result_chunk_ids: list[str]
    metadata: dict[str, Any]
    created_at: str
