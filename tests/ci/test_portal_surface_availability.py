from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
LEDGER_INDEX = ROOT / "tools/portal_audit/ledger/index.json"
NAVIGATION_LEDGER = ROOT / "tools/portal_audit/ledger/navigation.json"
WEB_AVAILABILITY = ROOT / "ai_platform/portal/web/lib/product-surface-availability.json"
APP_SHELL = ROOT / "ai_platform/portal/web/components/app-shell.tsx"
NOTICE = ROOT / "ai_platform/portal/web/components/surface-availability-notice.tsx"
UNAVAILABLE_STATUSES = ("DISCONNECTED", "MISSING")


def _expected_projection() -> dict[str, Any]:
    index = json.loads(LEDGER_INDEX.read_text(encoding="utf-8"))
    rows = json.loads(NAVIGATION_LEDGER.read_text(encoding="utf-8"))
    unavailable: list[dict[str, str]] = []
    for row in rows:
        values = row.split("|", 10)
        assert len(values) == 11
        _, label, route, _, _, _, _, _, overall, issues, reason = values
        if overall in UNAVAILABLE_STATUSES:
            unavailable.append(
                {
                    "route": route,
                    "label": label,
                    "status": overall,
                    "issues": issues,
                    "reason": reason,
                }
            )
    return {
        "schema_version": "portal-product-surface-availability-v1",
        "source": "tools/portal_audit/ledger/navigation.json",
        "ledger_version": index["ledger_version"],
        "unavailable_overall_statuses": list(UNAVAILABLE_STATUSES),
        "surfaces": unavailable,
    }


def test_web_surface_availability_projection_matches_living_ledger() -> None:
    actual = json.loads(WEB_AVAILABILITY.read_text(encoding="utf-8"))

    assert actual == _expected_projection()
    assert actual["surfaces"]
    assert {surface["status"] for surface in actual["surfaces"]} <= set(UNAVAILABLE_STATUSES)


def test_portal_shell_exposes_projected_unavailable_state() -> None:
    shell = APP_SHELL.read_text(encoding="utf-8")
    notice = NOTICE.read_text(encoding="utf-8")

    assert 'import availability from "@/lib/product-surface-availability.json"' in shell
    assert "unavailableRoutes.has(item.href)" in shell
    assert '" · Unavailable"' in shell
    assert "<SurfaceAvailabilityNotice />" in shell

    assert 'import availability from "@/lib/product-surface-availability.json"' in notice
    assert "usePathname()" in notice
    assert "capability unavailable" in notice
    assert "not connected end to end in the canonical product runtime" in notice
