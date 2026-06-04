from __future__ import annotations

import httpx

from plozen_knowledge_mcp.client import KnowledgeApiClient, KnowledgeApiError


def test_search_sends_api_key_and_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/search"
        assert request.headers["X-Knowledge-Api-Key"] == "test-key"
        assert request.read() == b'{"query":"RAG","top_k":3,"filters":{"project":"PLOZEN"}}'
        return httpx.Response(200, json={"query": "RAG", "results": []})

    api_client = KnowledgeApiClient(
        base_url="http://knowledge.local",
        api_key="test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert api_client.search_knowledge(query="RAG", top_k=3, filters={"project": "PLOZEN"}) == {
        "query": "RAG",
        "results": [],
    }


def test_get_source_fetches_chunks() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/documents":
            return httpx.Response(200, json=[{"id": "src-1", "title": "Source"}])
        if request.url.path == "/documents/src-1/chunks":
            return httpx.Response(200, json=[{"id": "chunk-1", "content": "Chunk"}])
        return httpx.Response(404, json={"detail": "not found"})

    api_client = KnowledgeApiClient(
        base_url="http://knowledge.local",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert api_client.get_source("src-1") == {
        "source": {"id": "src-1", "title": "Source"},
        "chunks": [{"id": "chunk-1", "content": "Chunk"}],
    }


def test_get_source_raises_for_missing_source() -> None:
    api_client = KnowledgeApiClient(
        base_url="http://knowledge.local",
        http_client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=[]))),
    )

    try:
        api_client.get_source("missing")
    except KnowledgeApiError as exc:
        assert "Document source not found" in str(exc)
    else:
        raise AssertionError("Expected KnowledgeApiError")

