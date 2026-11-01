from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SAMPLE_REPO = PROJECT_ROOT / "data" / "sample_repo"
BENCHMARK_CASES = PROJECT_ROOT / "data" / "benchmark_cases"


def resolve_supported_repo_root(repo_root=None):
    """
    Resolve a repository root.

    Only allow the original sample repository or a direct
    child of data/benchmark_cases.
    """

    if repo_root is None:
        candidate = SAMPLE_REPO.resolve()
    else:
        candidate = Path(repo_root).resolve()

    sample_repo = SAMPLE_REPO.resolve()
    benchmark_cases = BENCHMARK_CASES.resolve()

    if candidate != sample_repo:
        if candidate.parent != benchmark_cases:
            raise ValueError(
                "Repository must be sample_repo or a direct "
                "benchmark fixture directory."
            )

    if not candidate.is_dir():
        raise FileNotFoundError(
            "Repository directory does not exist."
        )

    if not (candidate / "tests").is_dir():
        raise ValueError(
            "Selected repository must contain a tests directory."
        )

    return candidate