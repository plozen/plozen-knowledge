from plozen_knowledge_api.chunking import MarkdownChunker, count_tokens


def test_markdown_chunker_preserves_heading_metadata() -> None:
    text = """# PLOZEN Knowledge

PLOZEN RAG 시스템은 문서를 청킹하고 embedding으로 검색합니다.

## API

FastAPI는 ingest와 search endpoint를 제공합니다.
"""

    chunks = MarkdownChunker(chunk_size=40, chunk_overlap=5).chunk(text)

    assert chunks
    assert chunks[0].chunk_index == 0
    assert chunks[0].content_hash
    assert any("PLOZEN Knowledge" in chunk.metadata["section_path"] for chunk in chunks)


def test_markdown_chunker_splits_oversized_block() -> None:
    text = "# Long\n\n" + " ".join(f"token{i}" for i in range(120))

    chunks = MarkdownChunker(chunk_size=30, chunk_overlap=5).chunk(text)

    assert len(chunks) > 1
    assert all(chunk.token_count <= 35 for chunk in chunks)
    assert chunks[1].metadata["strategy"] == "hard_split"


def test_count_tokens_handles_korean_text() -> None:
    assert count_tokens("문서 청킹과 RAG 검색") >= 3
