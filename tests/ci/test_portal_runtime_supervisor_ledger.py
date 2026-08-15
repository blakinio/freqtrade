from __future__ import annotations

import json
from pathlib import Path


def test_runtime_supervisor_ledger_uses_open_product_composition_issue() -> None:
    index = json.loads(Path("tools/portal_audit/ledger/index.json").read_text())
    assert index["ledger_version"] == "2026-08-15.1"

    rows = json.loads(Path("tools/portal_audit/ledger/backend_modules.json").read_text())
    runtime_supervisor = [row for row in rows if row.startswith("runtime_supervisor|")]
    assert runtime_supervisor == [
        "runtime_supervisor|DISCONNECTED|#1099|generation-bound PAPER lifecycle supervisor "
        "is component-only and not product-composed"
    ]
