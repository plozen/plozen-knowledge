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

    def search(self, *, query: str, top_k: int, filters: dict[str, Any]) -> dict[str, Any]:
        query_embedding = self.embedding_provider.embed_query(query)
        return self.repository.search(
            query_text=query,
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )
