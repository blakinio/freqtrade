#!/usr/bin/env python3
"""Apply the exact formatting/complexity repair diagnosed for PR #248."""

from __future__ import annotations

import sys
from pathlib import Path


EXPECTED_HEAD = "6e00a17e8783e978f51fe7efe5823efc27ed3bd9"
RUN_REQUEST = Path(
    "ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_run_request.py"
)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: diag_apply_rl_v2_paired_ci_repair.py <repo-root>")
    root = Path(sys.argv[1]).resolve()
    path = root / RUN_REQUEST
    text = path.read_text(encoding="utf-8")
    old = (
        "def _validate_contract() -> tuple[dict[str, Any], dict[str, Any], "
        "dict[str, Any], dict[str, Any]]:\n"
    )
    new = (
        "# Centralized intentionally: every immutable boundary is checked in one fail-closed guard.\n"
        "def _validate_contract(  # noqa: C901\n"
        ") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:\n"
    )
    if text.count(old) != 1:
        raise SystemExit("expected exactly one original _validate_contract signature")
    path.write_text(text.replace(old, new), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
