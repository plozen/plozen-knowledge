from __future__ import annotations

from typing import Any

import httpx


class KnowledgeApiError(RuntimeError):
    """Raised when the Knowledge API rejects or fails a request."""


class KnowledgeApiClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        timeout_seconds: float = 20.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def search_knowledge(
        self,
        *,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/search",
            json={
                "query": query,
                "top_k": top_k,
                "filters": filters or {},
            },
        )

    def list_sources(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/documents")
        if not isinstance(payload, list):
            raise KnowledgeApiError("Knowledge API /documents response must be a list")
        return payload

    def get_source(self, source_id: str, *, include_chunks: bool = True) -> dict[str, Any]:
        sources = self.list_sources()
        source = next((item for item in sources if item.get("id") == source_id), None)
        if not source:
            raise KnowledgeApiError(f"Document source not found: {source_id}")

        chunks: list[dict[str, Any]] = []
        if include_chunks:
            payload = self._request("GET", f"/documents/{source_id}/chunks")
            if not isinstance(payload, list):
                raise KnowledgeApiError("Knowledge API chunks response must be a list")
            chunks = payload

        return {"source": source, "chunks": chunks}

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = dict(kwargs.pop("headers", {}) or {})
        if self.api_key:
            headers["X-Knowledge-Api-Key"] = self.api_key

        response = self._client.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
        if response.status_code >= 400:
            raise KnowledgeApiError(f"Knowledge API request failed: {response.status_code} {response.text}")
        return response.json()

