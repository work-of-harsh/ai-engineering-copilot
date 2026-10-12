
import json
import math
from pathlib import Path

from app.ingestion.embeddings import embed_text


def cosine_similarity(vector_a, vector_b):
    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(sum(a * a for a in vector_a))
    magnitude_b = math.sqrt(sum(b * b for b in vector_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def search_repository(query: str, top_k: int = 3):
    index_path = Path("data/index.json")

    if not index_path.exists():
        raise FileNotFoundError(
            "Search index not found. Run python scripts\\build_index.py first."
        )

    with index_path.open("r", encoding="utf-8") as file:
        indexed_chunks = json.load(file)

    query_vector = embed_text(
        query,
        task_type="RETRIEVAL_QUERY",
    )

    results = []

    for chunk in indexed_chunks:
        score = cosine_similarity(
            query_vector,
            chunk["embedding"],
        )

        results.append({
            "path": chunk["path"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "content": chunk["content"],
            "score": score,
        })

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:max(1, top_k)]
