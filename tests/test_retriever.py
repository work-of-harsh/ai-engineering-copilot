
import pytest

from app.ingestion.retriever import cosine_similarity


def test_identical_vectors_have_similarity_one():
    assert cosine_similarity([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_orthogonal_vectors_have_similarity_zero():
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_zero_vector_returns_zero_similarity():
    assert cosine_similarity([0, 0], [1, 2]) == 0.0
