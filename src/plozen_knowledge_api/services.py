from __future__ import annotations

from typing import Any

from .chunking import MarkdownChunker, hash_text
from .embeddings import EmbeddingProvider
from .repositories import KnowledgeRepository


class KnowledgeService:
    def __init__(
        self,
        *,
        repository: KnowledgeRepository,
        chunker: MarkdownChunker,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.repository = repository
        self.chunker = chunker
        self.embedding_provider = embedding_provider

    def ingest_document(
        self,
        *,
        source_type: str,
        source_uri: str,
        title: str,
        content: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        source_hash = hash_text(content)
        unchanged = self.repository.get_unchanged_source(
            source_uri=source_uri,
            source_hash=source_hash,
        )
        if unchanged:
            return unchanged

        chunks = self.chunker.chunk(content)
        if not chunks:
            raise ValueError("No chunks generated from content")

        embeddings = self.embedding_provider.embed_texts([chunk.content for chunk in chunks])
        return self.repository.upsert_source_chunks(
            source_type=source_type,
            source_uri=source_uri,
            title=title,
            content=content,
            metadata={
                **metadata,
                "content_hash": source_hash,
                "chunk_count": len(chunks),
            },
            chunks=chunks,
            embeddings=embeddings,
        )

    def stage_document(
        self,
        *,
        source_type: str,
        source_uri: str,
        title: str,
        content: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return self.repository.stage_source(
            source_type=source_type,
            source_uri=source_uri,
            title=title,
            content=content,
            metadata=metadata,
        )

    def vectorize_document(self, source_id: str) -> dict[str, Any]:
        source = self.repository.get_source(source_id)
        if not source:
            raise ValueError("Document source not found")

        metadata = dict(source.get("metadata") or {})
        content = metadata.get("raw_content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Document source has no staged raw content")

        chunks = self.chunker.chunk(content)
        if not chunks:
            raise ValueError("No chunks generated from content")

        embeddings = self.embedding_provider.embed_texts([chunk.content for chunk in chunks])
        return self.repository.upsert_source_chunks(
            source_type=source["source_type"],
            source_uri=source["source_uri"],
            title=source["title"],
            content=content,
            metadata={
                **metadata,
                "rag_status": "vector",
                "content_hash": hash_text(content),
                "character_count": len(content),
                "chunk_count": len(chunks),
            },
            chunks=chunks,
            embeddings=embeddings,
        )

    def search(self, *, query: str, top_k: int, filters: dict[str, Any]) -> dict[str, Any]:
        query_embedding = self.embedding_provider.embed_query(query)
        return self.repository.search(
            query_text=query,
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )
