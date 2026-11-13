
from app.ingestion.scanner import scan_repository


def test_scanner_includes_supported_files_and_excludes_others(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / ".venv").mkdir()

    (tmp_path / "app" / "payment.py").write_text(
        "def calculate_total():\n    return 100\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        "SECRET=example\n",
        encoding="utf-8",
    )
    (tmp_path / "image.png").write_bytes(b"fake image")
    (tmp_path / ".venv" / "ignored.py").write_text(
        "print('ignored')\n",
        encoding="utf-8",
    )

    files = scan_repository(str(tmp_path))
    relative_paths = [
        str(path.relative_to(tmp_path)).replace("\\", "/")
        for path in files
    ]

    assert "app/payment.py" in relative_paths
    assert ".env" not in relative_paths
    assert "image.png" not in relative_paths
    assert ".venv/ignored.py" not in relative_paths
