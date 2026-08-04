# ruff: noqa: S102
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from typing import Any


BASE_PATCH_COMMIT = "bec0b0f8c424771e7b0c6fabf0ef623d8e2085bd"
BASE_PATCH_PATH = ".github/wh09-repair/patch_operator.py"
FINAL_PATCH_PATH = Path(__file__).with_name("patch_final_audit.txt")


def _execute_source(source: str, *, source_name: str) -> dict[str, Any]:
    namespace: dict[str, Any] = {
        "__name__": "wickhunter_wh09_repair_payload",
        "__file__": source_name,
    }
    exec(compile(source, source_name, "exec"), namespace)
    return namespace


def _load_base_patch() -> Any:
    completed = subprocess.run(
        ["/usr/bin/git", "show", f"{BASE_PATCH_COMMIT}:{BASE_PATCH_PATH}"],
        check=True,
        capture_output=True,
        text=True,
    )
    namespace = _execute_source(
        completed.stdout,
        source_name=f"{BASE_PATCH_COMMIT}:{BASE_PATCH_PATH}",
    )
    patch = namespace.get("patch")
    if not callable(patch):
        raise SystemExit("pinned base operator patch is unavailable")
    return patch


def _load_final_patch() -> tuple[str, Any]:
    namespace = _execute_source(
        FINAL_PATCH_PATH.read_text(encoding="utf-8"),
        source_name=str(FINAL_PATCH_PATH),
    )
    expected_head = namespace.get("CURRENT_PRODUCT_HEAD")
    patch_bundle = namespace.get("patch_bundle")
    if not isinstance(expected_head, str) or not callable(patch_bundle):
        raise SystemExit("final audit repair payload is invalid")
    return expected_head, patch_bundle


def _pin_expected_product_head(expected_head: str) -> None:
    environment_path = os.environ.get("GITHUB_ENV")
    if not environment_path:
        return
    with Path(environment_path).open("a", encoding="utf-8") as handle:
        handle.write(f"EXPECTED_TARGET_HEAD={expected_head}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    base_patch = _load_base_patch()
    expected_head, final_patch = _load_final_patch()
    base_patch(args.path)
    final_patch(args.path.parent)
    _pin_expected_product_head(expected_head)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
