from __future__ import annotations

from plozen_knowledge_api.repositories import merge_search_metadata


def test_merge_search_metadata_keeps_source_fields_and_nests_chunk_fields() -> None:
    metadata = merge_search_metadata(
        {
            "project": "jeonbuk-young-village",
            "vault_path": "02-Projects/project/spec.md",
            "knowledge_type": "spec",
        },
        {
            "heading": "개요",
            "line_start": 1,
        },
    )

    assert metadata == {
        "project": "jeonbuk-young-village",
        "vault_path": "02-Projects/project/spec.md",
        "knowledge_type": "spec",
        "chunk": {
            "heading": "개요",
            "line_start": 1,
        },
    }
