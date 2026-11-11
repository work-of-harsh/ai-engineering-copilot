import json
from pathlib import Path

from app.ingestion.retriever import search_repository
from app.ingestion.repo_paths import (
    resolve_supported_repo_root,
    get_repository_index_path,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_FILE = (
    PROJECT_ROOT / "data" / "debugging_benchmark.json"
)


def normalize_path(path):
    return str(path).replace("\\", "/").lower()


def main():
    cases = json.loads(
        DATASET_FILE.read_text(encoding="utf-8")
    )

    results = []

    for case in cases:
        case_id = case["id"]

        fixture_root = resolve_supported_repo_root(
            PROJECT_ROOT / case["fixture_path"]
        )

        index_path = get_repository_index_path(
            fixture_root
        )

        if not index_path.is_file():
            print(
                case_id,
                "| MISSING INDEX:",
                index_path
            )
            continue

        query = "{} {}".format(
            case["name"],
            case["error_output"]
        )

        # Retrieve all chunks in this small fixture index.
        retrieved = search_repository(
        query,
        top_k=100,
        index_path=index_path,
        debugging_mode=True
        )
        print("  Top retrieved candidates:")

        for position, item in enumerate(retrieved[:3], start=1):
            print(
            "  Rank {}: {} | semantic={} | keyword={} | "
            "hybrid={} | ranking={}".format(
            position,
            item["path"],
            round(item["score"], 4),
            round(item["keyword_score"], 4),
            round(item["hybrid_score"], 4),
            round(item["ranking_score"], 4),
            )
            )
        expected_source = normalize_path(
            case["expected_source"]
        )

        rank = None

        for position, item in enumerate(
            retrieved,
            start=1
        ):
            if normalize_path(item["path"]) == expected_source:
                rank = position
                break

        hit_at_1 = rank is not None and rank <= 1
        hit_at_3 = rank is not None and rank <= 3

        reciprocal_rank = (
            1.0 / rank if rank is not None else 0.0
        )

        results.append({
            "id": case_id,
            "query": query,
            "expected_source": case["expected_source"],
            "rank": rank,
            "hit_at_1": hit_at_1,
            "hit_at_3": hit_at_3,
            "reciprocal_rank": reciprocal_rank,
        })

        print(
            "{} | rank={} | Hit@1={} | Hit@3={}".format(
                case_id,
                rank,
                hit_at_1,
                hit_at_3
            )
        )

    total = len(results)

    if total == 0:
        print("No cases could be evaluated.")
        return

    hit_rate_1 = sum(
        item["hit_at_1"] for item in results
    ) / total

    hit_rate_3 = sum(
        item["hit_at_3"] for item in results
    ) / total

    mrr = sum(
        item["reciprocal_rank"] for item in results
    ) / total

    report = {
        "total_evaluated": total,
        "hit_rate_at_1": round(hit_rate_1, 4),
        "hit_rate_at_3": round(hit_rate_3, 4),
        "mrr": round(mrr, 4),
        "results": results,
    }

    report_path = (
        PROJECT_ROOT
        / "reports"
        / "debugging_retrieval_latest.json"
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report_path.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8"
    )

    print("\n" + "=" * 55)
    print("DEBUGGING RETRIEVAL EVALUATION")
    print("=" * 55)
    print("Evaluated cases:", total)
    print("Hit Rate@1:", round(hit_rate_1 * 100, 2), "%")
    print("Hit Rate@3:", round(hit_rate_3 * 100, 2), "%")
    print("MRR:", round(mrr, 4))
    print("Report:", report_path)


if __name__ == "__main__":
    main()