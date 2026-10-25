
import json
import math
import re
from pathlib import Path

from app.ingestion.embeddings import embed_text


STOP_WORDS = {
    "a", "an", "and", "are", "does", "for", "how",
    "in", "is", "it", "of", "on", "the", "this",
    "to", "what", "when", "where", "which", "why",
}


def cosine_similarity(vector_a, vector_b) -> float:
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def keyword_overlap_score(query: str, content: str) -> float:
    query_terms = {
        word
        for word in re.findall(r"[a-z_][a-z0-9_]*", query.lower())
        if word not in STOP_WORDS
    }

    if not query_terms:
        return 0.0

    content_terms = set(
        re.findall(r"[a-z_][a-z0-9_]*", content.lower())
    )

    matched_terms = query_terms.intersection(content_terms)

    return len(matched_terms) / len(query_terms)


def search_repository(query: str, top_k: int = 3) -> list:
    index_path = Path("data/index.json")

    if not index_path.exists():
        raise FileNotFoundError(
            "Repository index not found. Run "
            "'python -m scripts.build_index' first."
        )

    with index_path.open("r", encoding="utf-8") as file:
        index = json.load(file)

    query_embedding = embed_text(query, "RETRIEVAL_QUERY")
    scored_chunks = []

    for chunk in index:
        semantic_score = cosine_similarity(
            query_embedding, chunk["embedding"]
        )

        keyword_score = keyword_overlap_score(
            query, chunk.get("content", "")
        )

        result = dict(chunk)
        result.pop("embedding", None)

        # Preserve the original score for confidence checks.
        result["score"] = semantic_score
        result["keyword_score"] = keyword_score

        # Combine semantic relevance and exact-term overlap.
        result["hybrid_score"] = (
            0.8 * semantic_score + 0.2 * keyword_score
        )

        scored_chunks.append(result)

    scored_chunks.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )

    return scored_chunks[:max(0, top_k)]
