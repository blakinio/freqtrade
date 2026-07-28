from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest

from materialize_starter import _safe_extract


def test_safe_extract_rejects_parent_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    extraction_root = tmp_path / "root"
    extraction_root.mkdir()
    with ZipFile(archive_path, "w") as bundle:
        bundle.writestr("../escape.txt", "unsafe")

    with ZipFile(archive_path) as bundle, pytest.raises(SystemExit, match="unsafe archive path"):
        _safe_extract(bundle, extraction_root)

    assert not (tmp_path / "escape.txt").exists()


def test_safe_extract_allows_normal_members(tmp_path: Path) -> None:
    archive_path = tmp_path / "safe.zip"
    extraction_root = tmp_path / "root"
    extraction_root.mkdir()
    with ZipFile(archive_path, "w") as bundle:
        bundle.writestr("configs/example.yaml", "version: 1\n")

    with ZipFile(archive_path) as bundle:
        _safe_extract(bundle, extraction_root)

    assert (extraction_root / "configs/example.yaml").read_text() == "version: 1\n"
