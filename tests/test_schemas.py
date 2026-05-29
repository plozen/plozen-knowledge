import pytest
from pydantic import ValidationError

from plozen_knowledge_api.schemas import SearchRequest


def test_search_filters_reject_unknown_keys() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(
            query="rag",
            filters={"unsupported": "value"},
        )


def test_search_filters_allow_known_keys() -> None:
    request = SearchRequest(
        query="rag",
        filters={"source_type": "manual_note", "project": "PLOZEN Knowledge"},
    )

    assert request.filters.source_type == "manual_note"
    assert request.filters.project == "PLOZEN Knowledge"
