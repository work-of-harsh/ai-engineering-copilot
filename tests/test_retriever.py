
import pytest

from app.ingestion.retriever import cosine_similarity


def test_identical_vectors_have_similarity_one():
    assert cosine_similarity([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_orthogonal_vectors_have_similarity_zero():
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_zero_vector_returns_zero_similarity():
    assert cosine_similarity([0, 0], [1, 2]) == 0.0

def test_keyword_overlap_score():
    from app.ingestion.retriever import keyword_overlap_score

    assert keyword_overlap_score(
        "retry_count timeout_seconds",
        "retry_count: 3; timeout_seconds: 30",
    ) == 1.0

    assert keyword_overlap_score(
        "retry_count timeout_seconds",
        "payment amount tax rate",
    ) == 0.0

    assert keyword_overlap_score(
        "how is this explained",
        "payment amount tax rate",
    ) == 0.0



def test_hybrid_ranking_rewards_exact_keyword_matches(
    tmp_path, monkeypatch
):
    import json
    from app.ingestion import retriever

    monkeypatch.chdir(tmp_path)

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    index = [
        {
            "path": "app/payment.py",
            "start_line": 1,
            "end_line": 2,
            "content": "tax calculation",
            "embedding": [0.9, 0.435889894],
        },
        {
            "path": "config/payment.yaml",
            "start_line": 1,
            "end_line": 2,
            "content": "retry_count timeout_seconds",
            "embedding": [0.7, 0.714142843],
        },
    ]

    with (data_dir / "index.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(index, file)

    monkeypatch.setattr(
        retriever,
        "embed_text",
        lambda query, task_type: [1.0, 0.0],
    )

    results = retriever.search_repository(
        "retry_count timeout_seconds", top_k=2
    )

    assert results[0]["path"] == "config/payment.yaml"
    assert results[0]["keyword_score"] == 1.0
    assert results[0]["hybrid_score"] > results[1]["hybrid_score"]

    # The semantic score remains available separately.
    assert results[0]["score"] < results[1]["score"]
