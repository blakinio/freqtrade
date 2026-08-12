from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from ai_platform.portal.paper_execution.contract import PaperExecutionProfile, compare_profiles


def profile_data() -> dict:
    supported = {"status": "supported", "model": "deterministic-v1", "limitations": []}
    unsupported = {
        "status": "unsupported",
        "model": None,
        "limitations": [
            {
                "code": "QUEUE_POSITION_UNAVAILABLE",
                "description": "Queue position is not observable.",
            }
        ],
    }
    return {
        "schema_version": "paper-execution-profile-v1",
        "backwards_compatibility": "exact-version-and-digest-only",
        "venue": "kraken",
        "market_type": "spot",
        "order_types": {**supported, "order_types": ["market", "limit"]},
        "fee": {**supported, "maker_rate": "0.0010", "taker_rate": "0.0020"},
        "spread": {**supported, "bps": "1.50"},
        "slippage": {**supported, "bps": "2.0"},
        "latency": {**supported, "submit_ms": 10, "acknowledge_ms": 20, "fill_ms": 30},
        "liquidity": {**unsupported, "max_participation_rate": None, "depth_levels": None},
        "partial_fill": {
            **supported,
            "policy": "deterministic_chunks",
            "minimum_fill_ratio": "0.25",
        },
        "cancel_replace": {**supported, "cancel_timeout_ms": 5000, "replace_latency_ms": 40},
        "stale_data": {**supported, "maximum_age_ms": 1000, "action": "suspend_execution"},
        "funding": {**unsupported, "rate_bps_per_interval": None, "interval_seconds": None},
        "margin": {**unsupported, "maximum_leverage": None, "maintenance_margin_rate": None},
        "liquidation": {**unsupported, "maintenance_buffer_rate": None, "price_source": None},
        "throttling": {**supported, "requests_per_minute": 60, "burst_size": 5},
    }


def test_all_or_none_requires_full_fill_ratio() -> None:
    data = profile_data()
    data["partial_fill"]["policy"] = "all_or_none"
    data["partial_fill"]["minimum_fill_ratio"] = "0.25"
    with pytest.raises(ValidationError):
        PaperExecutionProfile.model_validate(data)

    data["partial_fill"]["minimum_fill_ratio"] = "1"
    profile = PaperExecutionProfile.model_validate(data)
    assert str(profile.partial_fill.minimum_fill_ratio) == "1"


@pytest.mark.parametrize(
    ("section", "field"),
    [
        ("latency", "submit_ms"),
        ("latency", "acknowledge_ms"),
        ("latency", "fill_ms"),
        ("cancel_replace", "cancel_timeout_ms"),
        ("cancel_replace", "replace_latency_ms"),
        ("stale_data", "maximum_age_ms"),
        ("throttling", "requests_per_minute"),
        ("throttling", "burst_size"),
    ],
)
def test_boolean_integer_inputs_fail_closed(section: str, field: str) -> None:
    data = profile_data()
    data[section][field] = True
    with pytest.raises(ValidationError):
        PaperExecutionProfile.model_validate(data)


def test_comparison_sequence_evidence_is_recursively_immutable() -> None:
    left = PaperExecutionProfile.model_validate(profile_data())
    changed = deepcopy(profile_data())
    changed["order_types"]["order_types"] = ["limit"]
    right = PaperExecutionProfile.model_validate(changed)

    comparison = compare_profiles(left, right)
    difference = next(
        item for item in comparison.differences if item.path == "$.order_types.order_types"
    )
    assert isinstance(difference.left, tuple)
    with pytest.raises(TypeError):
        difference.left[0] = "mutated"


def test_comparison_limitation_evidence_is_recursively_immutable() -> None:
    left_data = profile_data()
    right_data = deepcopy(left_data)
    right_data["liquidity"]["limitations"][0]["description"] = "Changed disclosure."
    comparison = compare_profiles(
        PaperExecutionProfile.model_validate(left_data),
        PaperExecutionProfile.model_validate(right_data),
    )
    difference = next(
        item
        for item in comparison.differences
        if item.path == "$.liquidity.limitations"
    )
    assert isinstance(difference.left, tuple)
    assert isinstance(difference.left[0], tuple)
