from pathlib import Path

from app.ingestion.scanner import scan_repository


def main():
    repository_path = Path("data") / "sample_repo"

    print("Scanning repository...")
    print("Path:", repository_path.resolve())
    print()

    try:
        files = scan_repository(str(repository_path))
    except (FileNotFoundError, NotADirectoryError) as exc:
        print("Scan failed:", exc)
        return

    for file_path in files:
        relative_path = file_path.relative_to(
            repository_path.resolve()
        )
        print("- {}".format(relative_path))

    print()
    print("Total supported files:", len(files))


if __name__ == "__main__":
    main()