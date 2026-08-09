from __future__ import annotations

import pytest

from ai_platform.wickhunter.candidate_evaluation_identity import validate_evaluation_case_counts


def _evaluation() -> dict[str, object]:
    return {
        "case_count": 824,
        "split_counts": {"train": 565, "validation": 178, "test": 81},
    }


def test_evaluation_identity_accepts_case_count_bound_to_split_counts() -> None:
    validate_evaluation_case_counts(_evaluation())


def test_evaluation_identity_rejects_stale_total_source_count() -> None:
    payload = _evaluation()
    payload["case_count"] = 919

    with pytest.raises(ValueError, match="case count mismatch"):
        validate_evaluation_case_counts(payload)


@pytest.mark.parametrize("invalid_case_count", [0, -1, True, "824"])
def test_evaluation_identity_requires_positive_integer_case_count(
    invalid_case_count: object,
) -> None:
    payload = _evaluation()
    payload["case_count"] = invalid_case_count

    with pytest.raises(ValueError):
        validate_evaluation_case_counts(payload)


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

    with pytest.raises(ValueError):
        validate_evaluation_case_counts(payload)
