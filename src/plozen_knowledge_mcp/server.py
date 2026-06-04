from __future__ import annotations

from functools import lru_cache
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import KnowledgeApiClient
from .config import get_mcp_settings

mcp = FastMCP("PLOZEN Knowledge")


@lru_cache
def client() -> KnowledgeApiClient:
    settings = get_mcp_settings()
    return KnowledgeApiClient(
        base_url=settings.knowledge_api_base_url,
        api_key=settings.knowledge_api_key,
        timeout_seconds=settings.request_timeout_seconds,
    )


def clamp_top_k(value: int) -> int:
    return min(max(value, 1), 20)


def compact_search_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": payload.get("query"),
        "top_k": payload.get("top_k"),
        "match_count": payload.get("match_count"),
        "latency_ms": payload.get("latency_ms"),
        "results": [
            {
                "chunk_id": item.get("chunk_id"),
                "source_id": item.get("source_id"),
                "source_type": item.get("source_type"),
                "source_uri": item.get("source_uri"),
                "title": item.get("title"),
                "chunk_index": item.get("chunk_index"),
                "score": item.get("score"),
                "distance": item.get("distance"),
                "metadata": item.get("metadata") or {},
                "content": item.get("content"),
            }
            for item in payload.get("results", [])
        ],
    }


def source_status(source: dict[str, Any]) -> str:
    metadata = source.get("metadata") or {}
    chunk_count = int(source.get("chunk_count") or 0)
    if chunk_count > 0 or metadata.get("rag_status") == "vector":
        return "vector"
    return metadata.get("rag_status") or "loaded"


def compact_source(source: dict[str, Any]) -> dict[str, Any]:
    metadata = source.get("metadata") or {}
    return {
        "id": source.get("id"),
        "source_type": source.get("source_type"),
        "source_uri": source.get("source_uri"),
        "title": source.get("title"),
        "status": source_status(source),
        "chunk_count": source.get("chunk_count", 0),
        "character_count": metadata.get("character_count"),
        "metadata": metadata,
        "updated_at": source.get("updated_at"),
    }


@mcp.tool()
def search_knowledge(
    query: str,
    top_k: int = 5,
    source_type: str | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """Search PLOZEN Knowledge chunks with pgvector-backed semantic search."""
    filters = {
        key: value
        for key, value in {
            "source_type": source_type,
            "project": project,
        }.items()
        if value
    }
    payload = client().search_knowledge(query=query, top_k=clamp_top_k(top_k), filters=filters)
    return compact_search_response(payload)


@mcp.tool()
def list_sources(
    limit: int = 20,
    status: str | None = None,
    source_type: str | None = None,
) -> dict[str, Any]:
    """List document sources registered in PLOZEN Knowledge."""
    sources = [compact_source(source) for source in client().list_sources()]
    if status:
        sources = [source for source in sources if source["status"] == status]
    if source_type:
        sources = [source for source in sources if source["source_type"] == source_type]

    safe_limit = min(max(limit, 1), 100)
    return {
        "count": len(sources),
        "limit": safe_limit,
        "sources": sources[:safe_limit],
    }


@mcp.tool()
def get_source(source_id: str, include_chunks: bool = True, chunk_limit: int = 20) -> dict[str, Any]:
    """Get one document source and optional chunks by source id."""
    payload = client().get_source(source_id, include_chunks=include_chunks)
    safe_limit = min(max(chunk_limit, 1), 100)
    return {
        "source": compact_source(payload["source"]),
        "chunks": [
            {
                "id": chunk.get("id"),
                "chunk_index": chunk.get("chunk_index"),
                "token_count": chunk.get("token_count"),
                "metadata": chunk.get("metadata") or {},
                "content": chunk.get("content"),
            }
            for chunk in payload["chunks"][:safe_limit]
        ],
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

