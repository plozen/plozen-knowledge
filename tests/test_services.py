from plozen_knowledge_api.chunking import MarkdownChunker
from plozen_knowledge_api.embeddings import FakeEmbeddingProvider
from plozen_knowledge_api.services import KnowledgeService


def test_chunk_count_matches_embedding_count() -> None:
    chunker = MarkdownChunker(chunk_size=30, chunk_overlap=5)
    provider = FakeEmbeddingProvider(dimensions=32)

    chunks = chunker.chunk("# Title\n\nRAG search API.\n\n" + "token " * 80)
    embeddings = provider.embed_texts([chunk.content for chunk in chunks])

    assert len(chunks) == len(embeddings)
    assert all(len(vector) == 32 for vector in embeddings)


def test_ingest_skips_before_embedding_when_source_unchanged() -> None:
    class StubRepository:
        def get_unchanged_source(self, *, source_uri: str, source_hash: str):
            return {
                "source_id": "existing-source-id",
                "status": "skipped",
                "chunk_count": 3,
                "source_hash": source_hash,
            }

    class FailingEmbeddingProvider:
        dimensions = 1536

        def embed_texts(self, texts: list[str]):
            raise AssertionError("embedding should not be called for unchanged source")

        def embed_query(self, text: str):
            raise AssertionError("query embedding not used in ingest")

    service = KnowledgeService(
        repository=StubRepository(),
        chunker=MarkdownChunker(),
        embedding_provider=FailingEmbeddingProvider(),
    )

    result = service.ingest_document(
        source_type="manual_note",
        source_uri="manual://unchanged",
        title="Unchanged",
        content="# Unchanged\n\nSame content",
        metadata={},
    )

    assert result["status"] == "skipped"
    assert result["chunk_count"] == 3
