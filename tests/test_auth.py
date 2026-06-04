import pytest
from fastapi import HTTPException

from plozen_knowledge_api import config, main


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda path=".env": None)
    main.settings.cache_clear()
    yield
    main.settings.cache_clear()


def test_api_key_required_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KNOWLEDGE_API_KEY", raising=False)
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED_DEV", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        main.require_api_key(None)

    assert exc_info.value.status_code == 401


def test_api_key_accepts_matching_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_API_KEY", "local-test-key")

    assert main.require_api_key("local-test-key") is None


def test_api_key_rejects_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_API_KEY", "local-test-key")

    with pytest.raises(HTTPException) as exc_info:
        main.require_api_key("wrong-key")

    assert exc_info.value.status_code == 401


def test_unauthenticated_dev_requires_explicit_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KNOWLEDGE_API_KEY", raising=False)
    monkeypatch.setenv("ALLOW_UNAUTHENTICATED_DEV", "true")

    assert main.require_api_key(None) is None


def test_upload_source_uri_includes_content_hash() -> None:
    first = main.build_upload_source_uri("../README.md", "first content")
    second = main.build_upload_source_uri("../README.md", "second content")

    assert first.startswith("upload://")
    assert first.endswith("/README.md")
    assert second.endswith("/README.md")
    assert first != second
