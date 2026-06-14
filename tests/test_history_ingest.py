# 이 파일은 History ingest의 파일 탐색, metadata, Knowledge API payload를 검증한다.
from __future__ import annotations

from datetime import date

import httpx

from plozen_knowledge_api.history_ingest import collect_history_documents, parse_history_filename
from plozen_knowledge_mcp.client import KnowledgeApiClient


def test_parse_history_filename_supports_session_agents() -> None:
    assert parse_history_filename("01-구글oauth하네스동기화-nexus.md") == (
        1,
        "구글oauth하네스동기화",
        "nexus",
    )
    assert parse_history_filename("00-구직구글연동-mason.md") == (
        0,
        "구직구글연동",
        "mason",
    )
    assert parse_history_filename("not-a-session.md") is None


def test_collect_history_documents_orders_by_date_and_file_order(tmp_path) -> None:
    vault_root = tmp_path / "vault"
    older = vault_root / "07-History" / "2026-06-11"
    newer = vault_root / "07-History" / "2026-06-12"
    older.mkdir(parents=True)
    newer.mkdir(parents=True)
    (newer / "01-later-nexus.md").write_text("# Later\n\nsecond", encoding="utf-8")
    (newer / "00-first-mason.md").write_text("# First\n\nfirst", encoding="utf-8")
    (older / "00-older-pulse.md").write_text("# Older\n\nolder", encoding="utf-8")
    (newer / "ignore.txt").write_text("ignore", encoding="utf-8")

    documents = collect_history_documents(vault_root, date_from=date(2026, 6, 12), limit=2)

    assert [document.filename for document in documents] == [
        "00-first-mason.md",
        "01-later-nexus.md",
    ]
    assert documents[0].source_uri == "obsidian://07-History/2026-06-12/00-first-mason.md"
    assert documents[0].source_title == "2026-06-12 first"
    assert documents[0].metadata == {
        "project": "PLOZEN",
        "domain": "session-history",
        "source": "obsidian",
        "vault_path": "07-History/2026-06-12/00-first-mason.md",
        "session_date": "2026-06-12",
        "filename": "00-first-mason.md",
        "character_count": len("# First\n\nfirst"),
        "agent": "mason",
        "order": 0,
    }


def test_collect_history_documents_filters_by_agent(tmp_path) -> None:
    vault_root = tmp_path / "vault"
    session_dir = vault_root / "07-History" / "2026-06-12"
    session_dir.mkdir(parents=True)
    (session_dir / "00-a-mason.md").write_text("mason", encoding="utf-8")
    (session_dir / "01-b-nexus.md").write_text("nexus", encoding="utf-8")

    documents = collect_history_documents(vault_root, agent="nexus")

    assert [document.filename for document in documents] == ["01-b-nexus.md"]


def test_ingest_document_sends_api_key_and_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/documents/ingest"
        assert request.headers["X-Knowledge-Api-Key"] == "test-key"
        assert request.read() == (
            b'{"source_type":"history_session",'
            b'"source_uri":"obsidian://07-History/2026-06-12/00-a-nexus.md",'
            b'"title":"2026-06-12 a",'
            b'"content":"# A",'
            b'"metadata":{"agent":"nexus"}}'
        )
        return httpx.Response(200, json={"source_id": "src-1", "status": "created"})

    api_client = KnowledgeApiClient(
        base_url="http://knowledge.local",
        api_key="test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert api_client.ingest_document(
        source_type="history_session",
        source_uri="obsidian://07-History/2026-06-12/00-a-nexus.md",
        title="2026-06-12 a",
        content="# A",
        metadata={"agent": "nexus"},
    ) == {"source_id": "src-1", "status": "created"}
