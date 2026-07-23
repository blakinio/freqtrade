import json
from pathlib import Path


BASELINE = Path("tests/ai_platform/portal/simulator/visual_acceptance_baseline.json")


def test_visual_acceptance_baseline_covers_critical_portal_surfaces() -> None:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert payload["data_mode"] == "fixture"
    assert payload["environment"] == "test"
    assert set(payload["routes"]) >= {"/", "/bots", "/bots/new", "/terminal", "/denied"}
    assert {viewport["name"] for viewport in payload["viewports"]} == {"desktop", "mobile"}
    assert "environment-badge-visible" in payload["required_invariants"]
    assert "no-browser-runtime-origin" in payload["required_invariants"]
