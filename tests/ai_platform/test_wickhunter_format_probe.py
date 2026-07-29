from __future__ import annotations

import subprocess
from pathlib import Path


def test_emit_exact_ruff_format_diff() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [
            "ruff",
            "format",
            "--check",
            "--diff",
            "ai_platform/wickhunter/live_archive.py",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
