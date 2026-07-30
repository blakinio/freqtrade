from __future__ import annotations

from pathlib import Path

import pytest

from strategy_engine.registry import FeatureRegistry, RegistryError

ROOT = Path(__file__).resolve().parents[2]


def test_support_resistance_registry_entry_is_point_in_time_and_not_ai_approved() -> None:
    registry = FeatureRegistry.load(ROOT / "configs" / "feature_registry.v1.yaml")
    definition = registry.get("support_resistance.v1")

    assert definition.status == "experimental"
    assert definition.approved_for_ai is False
    assert definition.research_only is True
    assert definition.roles == ("trigger", "confirmation", "ml_feature")
    assert definition.dependencies == ("confirmed_pivot.v1",)
    assert definition.required_sources == ()
    assert definition.warmup == "depends_on_confirmed_pivot + min_confirmations"
    assert definition.timestamp_policy == (
        "event_time_at_latest_confirmed_pivot_available_after_all_source_pivots"
    )
    assert definition.normalization_policy == (
        "distance_to_level / atr; confirmations capped by parameter bounds"
    )
    assert definition.license_origin == "independent_generic_formula"


def test_support_resistance_registry_parameters_and_dependency_order_are_deterministic() -> None:
    registry = FeatureRegistry.load(ROOT / "configs" / "feature_registry.v1.yaml")

    assert registry.validate_parameters("support_resistance.v1", {}) == {
        "min_confirmations": 2,
        "tolerance_bps": 25.0,
    }
    assert registry.resolve_dependencies(("support_resistance.v1",)) == (
        "confirmed_pivot.v1",
        "support_resistance.v1",
    )

    with pytest.raises(RegistryError, match="below minimum"):
        registry.validate_parameters("support_resistance.v1", {"min_confirmations": 0})
    with pytest.raises(RegistryError, match="above maximum"):
        registry.validate_parameters("support_resistance.v1", {"tolerance_bps": 1000.1})
