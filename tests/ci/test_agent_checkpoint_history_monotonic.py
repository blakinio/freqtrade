from __future__ import annotations

from tools.agents import validate_checkpoint_history as history_validator
from tools.agents.validate_checkpoint_history import (
    Snapshot,
    _assert_monotonic,
    _is_task_record_path,
)


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


def _task_record_text(*, ci: int, review: int = 1) -> str:
    return f"""task_id: FTAI-test

## Context checkpoint

```yaml
checkpoint_version: 2
observation_counters_by_sha:
  {SHA_A}:
    ci: {ci}
    review: {review}
```
"""


def test_task_record_classifier_excludes_governance_template() -> None:
    assert _is_task_record_path("docs/agents/tasks/active/task.md")
    assert _is_task_record_path("docs/agents/tasks/archive/task.md")
    assert not _is_task_record_path("docs/agents/tasks/TASK_TEMPLATE.md")
    assert not _is_task_record_path("docs/agents/CONTEXT_HANDOFF.md")


def test_validate_history_seeds_monotonicity_from_pr_base(monkeypatch) -> None:
    base = "1" * 40
    head = "2" * 40
    path = "docs/agents/tasks/active/task.md"

    monkeypatch.setattr(
        history_validator,
        "_task_paths_between",
        lambda _base, _head: (path,),
    )
    monkeypatch.setattr(
        history_validator,
        "_git",
        lambda *args: f"{head}\n",
    )

    def fake_show(commit: str, candidate_path: str) -> str | None:
        assert candidate_path == path
        if commit == base:
            return _task_record_text(ci=2)
        if commit == head:
            return _task_record_text(ci=0)
        return None

    monkeypatch.setattr(history_validator, "_show", fake_show)

    errors = history_validator.validate_history(base, head)

    assert any("decreased ci observations" in error for error in errors)


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
