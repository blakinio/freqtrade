from copy import deepcopy

import pytest
from pydantic import ValidationError

from ai_platform.portal.paper_execution.contract import (
    ComparisonReasonCode,
    PaperExecutionProfile,
    compare_profiles,
)


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


def test_same_semantics_and_serialization_noise_have_same_digest() -> None:
    original = profile_data()
    noisy = json_round_trip_with_reversed_keys(original)
    noisy["fee"]["maker_rate"] = "0.00100"
    noisy["order_types"]["order_types"].reverse()
    assert (
        PaperExecutionProfile.model_validate(original).digest
        == PaperExecutionProfile.model_validate(noisy).digest
    )


def test_every_material_assumption_is_digest_bound() -> None:
    baseline = PaperExecutionProfile.model_validate(profile_data())
    top_level_changes = {
        "venue": "coinbase",
        "market_type": "margin",
    }
    for field, value in top_level_changes.items():
        changed = deepcopy(profile_data())
        changed[field] = value
        assert PaperExecutionProfile.model_validate(changed).digest != baseline.digest
    material_paths = [
        ("order_types", "order_types", ["limit"]),
        ("fee", "maker_rate", "0.003"),
        ("spread", "bps", "2"),
        ("slippage", "bps", "3"),
        ("latency", "fill_ms", 31),
        ("partial_fill", "minimum_fill_ratio", "0.5"),
        ("cancel_replace", "cancel_timeout_ms", 5001),
        ("stale_data", "maximum_age_ms", 1001),
        ("liquidity", "status", "unknown"),
        ("funding", "status", "unknown"),
        ("margin", "status", "unknown"),
        ("liquidation", "status", "unknown"),
        ("throttling", "requests_per_minute", 61),
    ]
    for section, field, value in material_paths:
        changed = deepcopy(profile_data())
        changed[section][field] = value
        assert PaperExecutionProfile.model_validate(changed).digest != baseline.digest


def test_limitation_declaration_is_digest_bound_but_order_is_not() -> None:
    left = profile_data()
    left["liquidity"]["limitations"].append(
        {"code": "DEPTH_UNAVAILABLE", "description": "Depth is unavailable."}
    )
    right = deepcopy(left)
    right["liquidity"]["limitations"].reverse()
    assert (
        PaperExecutionProfile.model_validate(left).digest
        == PaperExecutionProfile.model_validate(right).digest
    )
    right["liquidity"]["limitations"][0]["description"] = "Depth is approximated."
    assert (
        PaperExecutionProfile.model_validate(left).digest
        != PaperExecutionProfile.model_validate(right).digest
    )


def test_unknown_incompatible_version_fails_closed() -> None:
    data = profile_data()
    data["schema_version"] = "paper-execution-profile-v999"
    with pytest.raises(ValidationError):
        PaperExecutionProfile.model_validate(data)


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("fee", "maker_rate", "-0.1"),
        ("spread", "bps", "-1"),
        ("slippage", "bps", "-1"),
        ("latency", "fill_ms", -1),
    ],
)
def test_negative_execution_inputs_reject(section: str, field: str, value: object) -> None:
    data = profile_data()
    data[section][field] = value
    with pytest.raises(ValidationError):
        PaperExecutionProfile.model_validate(data)


def test_missing_material_value_has_no_silent_default() -> None:
    data = profile_data()
    del data["spread"]["bps"]
    with pytest.raises(ValidationError):
        PaperExecutionProfile.model_validate(data)


def test_unknown_assumption_requires_an_explicit_limitation() -> None:
    data = profile_data()
    data["liquidity"]["status"] = "unknown"
    data["liquidity"]["limitations"] = []
    with pytest.raises(ValidationError):
        PaperExecutionProfile.model_validate(data)


def test_non_numeric_execution_value_rejects() -> None:
    data = profile_data()
    data["spread"]["bps"] = "high"
    with pytest.raises(ValidationError):
        PaperExecutionProfile.model_validate(data)


def test_different_identities_are_not_silently_comparable() -> None:
    left = PaperExecutionProfile.model_validate(profile_data())
    data = profile_data()
    data["latency"]["fill_ms"] = 31
    comparison = compare_profiles(left, PaperExecutionProfile.model_validate(data))
    assert comparison.comparable is False
    assert comparison.identical is False
    assert ComparisonReasonCode.DIFFERENT_PROFILE_IDENTITY in comparison.reason_codes
    assert any(difference.path == "$.latency.fill_ms" for difference in comparison.differences)


def test_models_are_deeply_immutable() -> None:
    profile = PaperExecutionProfile.model_validate(profile_data())
    with pytest.raises(ValidationError):
        profile.latency.fill_ms = 99


def json_round_trip_with_reversed_keys(value: dict) -> dict:
    return {key: value[key] for key in reversed(value)}
