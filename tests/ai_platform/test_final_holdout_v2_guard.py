from datetime import UTC, datetime

import pytest

from ai_platform.scripts.final_holdout_v2_guard import validate_final_holdout_v2_timing


def test_rejects_premature_trigger_pr_even_when_rerun_after_holdout() -> None:
    with pytest.raises(ValueError, match="trigger PR was created before"):
        validate_final_holdout_v2_timing(
            "2026-07-20T06:35:32Z",
            now_utc=datetime(2026, 10, 1, 0, 0, tzinfo=UTC),
        )


def test_rejects_execution_before_holdout_completion() -> None:
    with pytest.raises(ValueError, match="not yet complete"):
        validate_final_holdout_v2_timing(
            "2026-10-01T00:00:00Z",
            now_utc=datetime(2026, 9, 30, 23, 59, tzinfo=UTC),
        )


def test_accepts_trigger_and_execution_on_or_after_earliest_date() -> None:
    created_date, execution_date = validate_final_holdout_v2_timing(
        "2026-10-01T00:00:00Z",
        now_utc=datetime(2026, 10, 1, 0, 0, tzinfo=UTC),
    )

    assert created_date == "2026-10-01"
    assert execution_date == "2026-10-01"


def test_normalizes_trigger_timestamp_to_utc_before_date_check() -> None:
    with pytest.raises(ValueError, match="trigger PR was created before"):
        validate_final_holdout_v2_timing(
            "2026-10-01T00:30:00+02:00",
            now_utc=datetime(2026, 10, 1, 1, 0, tzinfo=UTC),
        )
