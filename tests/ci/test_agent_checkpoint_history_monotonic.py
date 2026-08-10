from __future__ import annotations

from tools.agents.validate_checkpoint_history import Snapshot, _assert_monotonic


SHA_A = "a" * 40
SHA_B = "b" * 40


def _snapshot(
    *, commit: str, history: dict[str, dict[str, int]], path: str = "docs/agents/tasks/active/task.md"
) -> Snapshot:
    return Snapshot(
        task_id="FTAI-test",
        path=path,
        commit=commit,
        checkpoint_version=2,
        observation_counters_by_sha=history,
    )


def test_monotonic_history_accepts_growth_and_new_sha() -> None:
    previous = _snapshot(
        commit="1" * 40,
        history={SHA_A: {"ci": 2, "review": 1}},
    )
    current = _snapshot(
        commit="2" * 40,
        history={
            SHA_A: {"ci": 2, "review": 2},
            SHA_B: {"ci": 1, "review": 0},
        },
    )

    assert _assert_monotonic(previous, current) == []


def test_monotonic_history_rejects_coordinated_counter_rewrite() -> None:
    previous = _snapshot(
        commit="1" * 40,
        history={SHA_A: {"ci": 2, "review": 1}},
    )
    current = _snapshot(
        commit="2" * 40,
        history={SHA_A: {"ci": 0, "review": 0}},
    )

    errors = _assert_monotonic(previous, current)

    assert any("decreased ci observations" in error for error in errors)
    assert any("decreased review observations" in error for error in errors)


def test_monotonic_history_rejects_eviction_of_prior_sha() -> None:
    previous = _snapshot(
        commit="1" * 40,
        history={
            SHA_A: {"ci": 2, "review": 1},
            SHA_B: {"ci": 1, "review": 2},
        },
    )
    current = _snapshot(
        commit="2" * 40,
        history={SHA_B: {"ci": 1, "review": 2}},
    )

    errors = _assert_monotonic(previous, current)

    assert any(f"removed prior observation history for {SHA_A}" in error for error in errors)
