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

    client_dir = Path("/tmp/wickhunter-artifact-client")
    install = _run(
        root,
        "npm",
        "install",
        "--silent",
        "--no-audit",
        "--no-fund",
        "--prefix",
        str(client_dir),
        "@actions/artifact@6.2.2",
    )
    assert install.returncode == 0, install.stderr

    module_path = client_dir / "node_modules/@actions/artifact/lib/artifact.js"
    script_path = export_dir / "upload.mjs"
    script_path.write_text(
        "\n".join(
            (
                f'import {{DefaultArtifactClient}} from "{module_path.as_posix()}";',
                "const artifact = new DefaultArtifactClient();",
                "const result = await artifact.uploadArtifact(",
                '  `wickhunter-ruff-${process.env.GITHUB_RUN_ID}` ,',
                f'  ["{patch_path.as_posix()}", "{report_path.as_posix()}"],',
                "  {retentionDays: 1, compressionLevel: 0}",
                ");",
                "console.log(JSON.stringify(result));",
            )
        ),
        encoding="utf-8",
    )
    upload = _run(root, "node", str(script_path))
    assert upload.returncode == 0, upload.stderr
    assert final_check.returncode == 0, report_path.read_text(encoding="utf-8")
    assert final_format.returncode == 0, report_path.read_text(encoding="utf-8")
