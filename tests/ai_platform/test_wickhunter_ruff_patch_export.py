from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


TARGETS = (
    "ai_platform/wickhunter",
    "tests/ai_platform_integration/test_wickhunter_vertical_slice.py",
)


def _run(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(
    os.environ.get("GITHUB_WORKFLOW") != "AI Platform CI",
    reason="diagnostic export is restricted to the AI Platform CI workflow",
)
def test_export_exact_wickhunter_ruff_repair() -> None:
    root = Path(__file__).resolve().parents[2]
    export_dir = Path("/tmp/wickhunter-ruff-export")
    export_dir.mkdir(parents=True, exist_ok=True)

    fix = _run(root, "ruff", "check", "--fix", *TARGETS)
    format_result = _run(root, "ruff", "format", *TARGETS)
    final_check = _run(root, "ruff", "check", *TARGETS)
    final_format = _run(root, "ruff", "format", "--check", *TARGETS)
    diff = _run(root, "git", "diff", "--", *TARGETS)

    patch_path = export_dir / "wickhunter-ruff.patch"
    report_path = export_dir / "wickhunter-ruff-report.txt"
    patch_path.write_text(diff.stdout, encoding="utf-8")
    report_path.write_text(
        "\n\n".join(
            (
                f"FIX RETURN CODE: {fix.returncode}\n{fix.stdout}\n{fix.stderr}",
                (
                    "FORMAT RETURN CODE: "
                    f"{format_result.returncode}\n{format_result.stdout}\n{format_result.stderr}"
                ),
                (
                    "FINAL CHECK RETURN CODE: "
                    f"{final_check.returncode}\n{final_check.stdout}\n{final_check.stderr}"
                ),
                (
                    "FINAL FORMAT RETURN CODE: "
                    f"{final_format.returncode}\n{final_format.stdout}\n{final_format.stderr}"
                ),
            )
        ),
        encoding="utf-8",
    )

    uploader_dir = Path("/tmp/wickhunter-upload-artifact")
    clone = _run(
        root,
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        "v4.6.2",
        "https://github.com/actions/upload-artifact.git",
        str(uploader_dir),
    )
    assert clone.returncode == 0, clone.stderr

    upload_environment = os.environ.copy()
    upload_environment.update(
        {
            "INPUT_NAME": f"wickhunter-ruff-{os.environ['GITHUB_RUN_ID']}",
            "INPUT_PATH": f"{patch_path}\n{report_path}",
            "INPUT_IF-NO-FILES-FOUND": "error",
            "INPUT_RETENTION-DAYS": "1",
            "INPUT_COMPRESSION-LEVEL": "0",
            "INPUT_OVERWRITE": "false",
            "INPUT_INCLUDE-HIDDEN-FILES": "false",
        }
    )
    upload = subprocess.run(
        ("node", str(uploader_dir / "dist/upload/index.js")),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        env=upload_environment,
    )
    assert upload.returncode == 0, upload.stderr
    assert final_check.returncode == 0, report_path.read_text(encoding="utf-8")
    assert final_format.returncode == 0, report_path.read_text(encoding="utf-8")
