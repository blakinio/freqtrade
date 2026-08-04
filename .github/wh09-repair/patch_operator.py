# ruff: noqa: S102, S603
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from typing import Any

from patch_final_audit import BASE_PATCH_COMMIT, CURRENT_PRODUCT_HEAD, patch_bundle


BASE_PATCH_PATH = ".github/wh09-repair/patch_operator.py"


def _load_base_patch() -> Any:
    completed = subprocess.run(
        ["/usr/bin/git", "show", f"{BASE_PATCH_COMMIT}:{BASE_PATCH_PATH}"],
        check=True,
        capture_output=True,
        text=True,
    )
    namespace: dict[str, Any] = {
        "__name__": "wickhunter_wh09_base_patch",
        "__file__": f"{BASE_PATCH_COMMIT}:{BASE_PATCH_PATH}",
    }
    exec(compile(completed.stdout, namespace["__file__"], "exec"), namespace)
    patch = namespace.get("patch")
    if not callable(patch):
        raise SystemExit("pinned base operator patch is unavailable")
    return patch


def _pin_expected_product_head() -> None:
    environment_path = os.environ.get("GITHUB_ENV")
    if not environment_path:
        return
    with Path(environment_path).open("a", encoding="utf-8") as handle:
        handle.write(f"EXPECTED_TARGET_HEAD={CURRENT_PRODUCT_HEAD}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    base_patch = _load_base_patch()
    base_patch(args.path)
    patch_bundle(args.path.parent)
    _pin_expected_product_head()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
