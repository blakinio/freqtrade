from __future__ import annotations

from copy import deepcopy

import pytest

from ai_platform.wickhunter.candidate_activation import (
    CandidateActivationError,
    _verify_evaluation_identity,
)


EVALUATION_SHA256 = "a" * 64


def _manifest() -> dict[str, object]:
    return {"evaluation_sha256": EVALUATION_SHA256}


def _evaluation() -> dict[str, object]:
    return {
        "evaluation_sha256": EVALUATION_SHA256,
        "case_count": 824,
        "split_counts": {"train": 565, "validation": 178, "test": 81},
        "protected_holdout_accessed": False,
        "automatic_promotion_enabled": False,
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "execution_enabled": False,
        "live_capital_authorized": False,
        "orders_submitted": 0,
    }


def test_evaluation_identity_accepts_case_count_bound_to_split_counts() -> None:
    _verify_evaluation_identity(_evaluation(), manifest=_manifest())


def test_evaluation_identity_rejects_stale_total_source_count() -> None:
    payload = _evaluation()
    payload["case_count"] = 919

    with pytest.raises(CandidateActivationError, match="case count mismatch"):
        _verify_evaluation_identity(payload, manifest=_manifest())


@pytest.mark.parametrize("invalid_case_count", [0, -1, True, "824"])
def test_evaluation_identity_requires_positive_integer_case_count(
    invalid_case_count: object,
) -> None:
    payload = _evaluation()
    payload["case_count"] = invalid_case_count

    with pytest.raises(CandidateActivationError):
        _verify_evaluation_identity(payload, manifest=_manifest())


@pytest.mark.parametrize(
    "split_counts",
    [
        {"train": 565, "validation": 178},
        {"train": 565, "validation": 178, "test": 81, "holdout": 0},
        {"train": 565, "validation": 178, "test": True},
        {"train": 565, "validation": 178, "test": -1},
    ],
)
def test_evaluation_identity_rejects_invalid_split_counts(
    split_counts: dict[str, object],
) -> None:
    payload = _evaluation()
    payload["split_counts"] = split_counts

    with pytest.raises(CandidateActivationError):
        _verify_evaluation_identity(payload, manifest=_manifest())


def test_evaluation_identity_preserves_zero_authority_guard() -> None:
    payload = deepcopy(_evaluation())
    payload["execution_enabled"] = True

    with pytest.raises(CandidateActivationError, match="unsafe authority field: execution_enabled"):
        _verify_evaluation_identity(payload, manifest=_manifest())


def test_evaluation_identity_preserves_manifest_binding() -> None:
    manifest = _manifest()
    manifest["evaluation_sha256"] = "b" * 64

    with pytest.raises(CandidateActivationError, match="does not match candidate manifest"):
        _verify_evaluation_identity(_evaluation(), manifest=manifest)
