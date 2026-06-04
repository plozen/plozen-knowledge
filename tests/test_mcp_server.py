from __future__ import annotations

from plozen_knowledge_mcp.server import clamp_top_k, compact_metadata, compact_search_response, compact_source


def test_clamp_top_k_bounds_values() -> None:
    assert clamp_top_k(0) == 1
    assert clamp_top_k(5) == 5
    assert clamp_top_k(100) == 20


def test_compact_search_response_keeps_result_contract() -> None:
    payload = {
        "query": "RAG",
        "top_k": 1,
        "match_count": 1,
        "latency_ms": 12,
        "results": [
            {
                "chunk_id": "chunk-1",
                "source_id": "source-1",
                "source_type": "obsidian_note",
                "source_uri": "obsidian://note",
                "title": "Note",
                "chunk_index": 0,
                "score": 0.9,
                "distance": 0.1,
                "metadata": {"project": "PLOZEN"},
                "content": "검색 결과",
                "extra": "dropped",
            }
        ],
    }

    assert compact_search_response(payload) == {
        "query": "RAG",
        "top_k": 1,
        "match_count": 1,
        "latency_ms": 12,
        "results": [
            {
                "chunk_id": "chunk-1",
                "source_id": "source-1",
                "source_type": "obsidian_note",
                "source_uri": "obsidian://note",
                "title": "Note",
                "chunk_index": 0,
                "score": 0.9,
                "distance": 0.1,
                "metadata": {"project": "PLOZEN"},
                "content": "검색 결과",
            }
        ],
    }


def test_compact_source_derives_vector_status() -> None:
    assert compact_source({"id": "source-1", "chunk_count": 2, "metadata": {}})["status"] == "vector"
    assert compact_source({"id": "source-2", "chunk_count": 0, "metadata": {"rag_status": "loaded"}})["status"] == "loaded"


def test_compact_metadata_drops_raw_content() -> None:
    assert compact_metadata(
        {
            "filename": "note.md",
            "raw_content": "long source body",
            "character_count": 16,
        }
    ) == {
        "filename": "note.md",
        "character_count": 16,
    }
