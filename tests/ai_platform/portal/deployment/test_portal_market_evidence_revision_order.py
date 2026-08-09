from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
RUNTIME = ROOT / "deploy" / "synology" / "portal-oidc" / "market_evidence_runtime.py"


def test_market_evidence_selection_orders_revision_components_numerically() -> None:
    source = RUNTIME.read_text(encoding="utf-8")

    assert "const runOrder = (runId) =>" in source
    assert "BigInt(match[1])" in source
    assert "BigInt(match[2])" in source
    assert "BigInt(match[3])" in source
    assert ".sort(newestRunFirst);" in source
    assert ".sort()\n  .reverse();" not in source
