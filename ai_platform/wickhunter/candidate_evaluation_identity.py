from __future__ import annotations

from collections.abc import Mapping


EVALUATION_SPLITS = ("train", "validation", "test")


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def validate_evaluation_case_counts(payload: Mapping[str, object]) -> None:
    """Validate the integrity-bound evaluated-case total without hard-coded dataset cardinality."""

    case_count = _integer(payload.get("case_count"), field="evaluation case count")
    if case_count < 1:
        raise ValueError("candidate evaluation case count must be positive")

    split_counts = payload.get("split_counts")
    if not isinstance(split_counts, dict) or set(split_counts) != set(EVALUATION_SPLITS):
        raise ValueError("candidate evaluation split counts mismatch")

    split_total = 0
    for split_name in EVALUATION_SPLITS:
        split_count = _integer(
            split_counts.get(split_name),
            field=f"evaluation {split_name} case count",
        )
        if split_count < 0:
            raise ValueError("candidate evaluation split count must be non-negative")
        split_total += split_count

    if case_count != split_total:
        raise ValueError("candidate evaluation case count mismatch")
