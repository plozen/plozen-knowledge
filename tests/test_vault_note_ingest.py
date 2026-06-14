# 이 파일은 선택한 Obsidian 노트 ingest의 경로 검증과 metadata 생성을 검증한다.
from __future__ import annotations

import pytest

from plozen_knowledge_api.vault_note_ingest import (
    collect_vault_note_documents,
    load_vault_note_document,
    normalize_vault_note_path,
)


def test_normalize_vault_note_path_rejects_unsafe_paths() -> None:
    with pytest.raises(ValueError):
        normalize_vault_note_path("/absolute/note.md")
    with pytest.raises(ValueError):
        normalize_vault_note_path("../secret.md")
    with pytest.raises(ValueError):
        normalize_vault_note_path("00-Inbox/raw.txt")


def test_load_vault_note_document_builds_metadata_from_selected_note(tmp_path) -> None:
    vault_root = tmp_path / "vault"
    note_path = vault_root / "02-Projects" / "전북청년마을만들기" / "spec" / "index-jeonbuk.md"
    note_path.parent.mkdir(parents=True)
    note_path.write_text("# 전북청년마을만들기\n\n프로젝트 지식입니다.", encoding="utf-8")

    document = load_vault_note_document(
        vault_root,
        "02-Projects/전북청년마을만들기/spec/index-jeonbuk.md",
        project="jeonbuk-young-village",
        domain="project-knowledge",
        knowledge_type="spec",
        visibility="internal",
    )

    assert document.source_uri == "obsidian://02-Projects/전북청년마을만들기/spec/index-jeonbuk.md"
    assert document.source_title == "전북청년마을만들기"
    assert document.metadata == {
        "project": "jeonbuk-young-village",
        "domain": "project-knowledge",
        "source": "obsidian",
        "vault_path": "02-Projects/전북청년마을만들기/spec/index-jeonbuk.md",
        "knowledge_type": "spec",
        "visibility": "internal",
        "filename": "index-jeonbuk.md",
        "character_count": len("# 전북청년마을만들기\n\n프로젝트 지식입니다."),
    }


def test_collect_vault_note_documents_preserves_input_order(tmp_path) -> None:
    vault_root = tmp_path / "vault"
    first = vault_root / "02-Projects" / "project" / "first.md"
    second = vault_root / "02-Projects" / "project" / "second.md"
    first.parent.mkdir(parents=True)
    first.write_text("# First\n\none", encoding="utf-8")
    second.write_text("# Second\n\ntwo", encoding="utf-8")

    documents = collect_vault_note_documents(
        vault_root,
        ["02-Projects/project/second.md", "02-Projects/project/first.md"],
        project="test-project",
        domain="project-knowledge",
        knowledge_type="spec",
    )

    assert [document.filename for document in documents] == ["second.md", "first.md"]
