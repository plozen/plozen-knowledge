# 이 파일은 MCP와 CLI에서 사용할 PLOZEN Knowledge API HTTP 호출을 감싼다.
# KnowledgeApiClient는 요청을 보내고, KnowledgeApiError는 API 실패를 표현한다.
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
        # 테스트에서는 주입받은 http_client를 쓰고, 실제 실행에서는 자체 httpx.Client를 만든다.
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        # 이 객체가 직접 만든 HTTP client만 닫아서 외부 주입 client의 생명주기를 건드리지 않는다.
        if self._owns_client:
            self._client.close()

    def search_knowledge(
        self,
        *,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Knowledge API의 /search 엔드포인트로 의미 검색 요청을 보낸다.
        return self._request(
            "POST",
            "/search",
            json={
                "query": query,
                "top_k": top_k,
                "filters": filters or {},
            },
        )

    def ingest_document(
        self,
        *,
        source_type: str,
        source_uri: str,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Knowledge API의 /documents/ingest 엔드포인트로 문서 본문과 metadata를 보낸다.
        return self._request(
            "POST",
            "/documents/ingest",
            json={
                "source_type": source_type,
                "source_uri": source_uri,
                "title": title,
                "content": content,
                "metadata": metadata or {},
            },
        )

    def list_sources(self) -> list[dict[str, Any]]:
        # 등록된 document source 목록을 조회하고 API 응답 형태를 검증한다.
        payload = self._request("GET", "/documents")
        if not isinstance(payload, list):
            raise KnowledgeApiError("Knowledge API /documents response must be a list")
        return payload

    def get_source(self, source_id: str, *, include_chunks: bool = True) -> dict[str, Any]:
        # source 목록에서 대상 문서를 찾고, 필요하면 chunk 목록까지 함께 가져온다.
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
        # 공통 HTTP 요청 처리로 API key 헤더를 붙이고 4xx/5xx를 예외로 바꾼다.
        headers = dict(kwargs.pop("headers", {}) or {})
        if self.api_key:
            headers["X-Knowledge-Api-Key"] = self.api_key

        response = self._client.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
        if response.status_code >= 400:
            raise KnowledgeApiError(f"Knowledge API request failed: {response.status_code} {response.text}")
        return response.json()
