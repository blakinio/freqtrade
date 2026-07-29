from __future__ import annotations

import json
from pathlib import Path

from strategy_engine.dsl.validator import StrategyValidator
from strategy_engine.registry import FeatureRegistry


def test_strategy_lab_definitions_pass_registry_aware_validation() -> None:
    package_root = Path(__file__).resolve().parents[2]
    registry = FeatureRegistry.load(package_root / "configs" / "feature_registry.v1.yaml")
    validator = StrategyValidator(registry)

    for name in ("tv_supertrend_v1.json", "tv_squeeze_momentum_v1.json"):
        payload = json.loads((package_root / "strategies" / name).read_text(encoding="utf-8"))
        parsed = validator.validate(payload["dsl"])
        assert parsed.strategy_id == payload["strategy_id"]
        assert parsed.version == payload["strategy_version"]
