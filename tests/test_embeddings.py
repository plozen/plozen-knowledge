from plozen_knowledge_api.embeddings import FakeEmbeddingProvider


def test_fake_embedding_is_stable_and_dimensioned() -> None:
    provider = FakeEmbeddingProvider(dimensions=16)

    first = provider.embed_query("PLOZEN RAG Knowledge")
    second = provider.embed_query("PLOZEN RAG Knowledge")

    assert first == second
    assert len(first) == 16


def test_fake_embedding_rewards_shared_tokens() -> None:
    provider = FakeEmbeddingProvider(dimensions=128)

    query = provider.embed_query("RAG knowledge search")
    related = provider.embed_query("knowledge search API for RAG")
    unrelated = provider.embed_query("monthly revenue report")

    related_dot = sum(a * b for a, b in zip(query, related, strict=True))
    unrelated_dot = sum(a * b for a, b in zip(query, unrelated, strict=True))

    assert related_dot > unrelated_dot
