from datetime import date, datetime, timezone


EARLIEST_EXECUTION_DATE = date(2026, 10, 1)


def _parse_github_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid GitHub pull-request created_at timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError("GitHub pull-request created_at timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def validate_final_holdout_v2_timing(
    pr_created_at: str,
    *,
    now_utc: datetime | None = None,
) -> tuple[str, str]:
    """Validate that both the trigger PR and execution occur after the holdout closes."""
    created_date = _parse_github_timestamp(pr_created_at).date()
    current = now_utc or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now_utc must include a timezone")
    today_utc = current.astimezone(timezone.utc).date()

    if created_date < EARLIEST_EXECUTION_DATE:
        raise ValueError(
            "Final validation trigger PR was created before the prospective holdout completed. "
            f"Earliest allowed trigger PR date is {EARLIEST_EXECUTION_DATE.isoformat()} UTC; "
            f"trigger PR creation date is {created_date.isoformat()} UTC. "
            "A premature trigger PR cannot be reused or rerun later to access holdout data."
        )

    if today_utc < EARLIEST_EXECUTION_DATE:
        raise ValueError(
            "Final holdout v2 is prospectively declared but not yet complete. "
            f"Earliest execution date is {EARLIEST_EXECUTION_DATE.isoformat()} UTC; "
            f"today is {today_utc.isoformat()} UTC. "
            "No holdout data may be downloaded or accessed."
        )

    return created_date.isoformat(), today_utc.isoformat()
