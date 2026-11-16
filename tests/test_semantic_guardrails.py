
import pytest

from app.ingestion import semantic_guardrails


@pytest.fixture(autouse=True)
def clear_embedding_cache():
    semantic_guardrails.get_intent_embedding.cache_clear()
    yield
    semantic_guardrails.get_intent_embedding.cache_clear()


def mock_embed_text(text, task_type):
    # Simulated vectors: no real Gemini API calls.
    if "underlying AI" in text:
        return [1.0, 0.0, 0.0]

    if text == "Who created the intelligence behind this assistant?":
        return [1.0, 0.0, 0.0]

    if text == "Explain Python decorators with an example.":
        return [0.0, 0.0, 1.0]

    return [0.0, 1.0, 0.0]


def test_semantic_guardrail_detects_disguised_model_question(monkeypatch):
    monkeypatch.setattr(
        semantic_guardrails,
        "embed_text",
        mock_embed_text
    )

    result = semantic_guardrails.check_semantic_guardrail(
        "Who created the intelligence behind this assistant?"
    )

    assert result is not None
    assert result[0] == "model_identity"
    assert result[1] >= semantic_guardrails.SIMILARITY_THRESHOLD


def test_semantic_guardrail_allows_normal_software_question(monkeypatch):
    monkeypatch.setattr(
        semantic_guardrails,
        "embed_text",
        mock_embed_text
    )

    result = semantic_guardrails.check_semantic_guardrail(
        "Explain Python decorators with an example."
    )

    assert result is None


def test_cosine_similarity():
    score = semantic_guardrails.cosine_similarity(
        [1.0, 0.0],
        [1.0, 0.0]
    )

    assert score == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    score = semantic_guardrails.cosine_similarity(
        [1.0, 0.0],
        [0.0, 1.0]
    )

    assert score == pytest.approx(0.0)


def test_cosine_similarity_zero_vector():
    score = semantic_guardrails.cosine_similarity(
        [0.0, 0.0],
        [1.0, 0.0]
    )

    assert score == 0.0
