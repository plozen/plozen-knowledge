from __future__ import annotations

import os
from dataclasses import dataclass


def normalize_base_url(value: str | None) -> str:
    base_url = (value or "http://127.0.0.1:8100").strip().rstrip("/")
    if not base_url:
        return "http://127.0.0.1:8100"
    return base_url


@dataclass(frozen=True)
class McpSettings:
    knowledge_api_base_url: str
    knowledge_api_key: str | None
    request_timeout_seconds: float = 20.0


def get_mcp_settings() -> McpSettings:
    timeout = float(os.getenv("KNOWLEDGE_API_TIMEOUT_SECONDS", "20"))
    return McpSettings(
        knowledge_api_base_url=normalize_base_url(os.getenv("KNOWLEDGE_API_BASE_URL")),
        knowledge_api_key=os.getenv("KNOWLEDGE_API_KEY") or None,
        request_timeout_seconds=timeout,
    )

