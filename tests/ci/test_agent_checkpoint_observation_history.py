from __future__ import annotations

from pathlib import Path

from tools.agents.checkpoint import parse_checkpoint, validate_checkpoint


SHA_A = "a" * 40
SHA_B = "b" * 40


def _checkpoint_text(
    *,
    version: int,
    head: str,
    ci: int | None = None,
    review: int | None = None,
    history: str = "",
) -> str:
    counters = ""
    if version == 2:
        assert ci is not None
        assert review is not None
        counters = (
            f"ci_checks_for_current_head: {ci}\n"
            f"review_checks_for_current_head: {review}\n"
            "observation_counters_by_sha:\n"
            f"{history}"
        )

    return f"""# Test task

## Context checkpoint

```yaml
checkpoint_version: {version}
updated_at: 2026-08-10T20:30:00Z
head: {head}
branch: test/checkpoint-history
pr: 1451
status: validating
{counters}context_routes:
  - checkpoint observation history
owned_paths:
  - tools/agents/checkpoint.py
proven:
  - exact-head observation counters are persisted
  - prior exact-head history remains present
derived:
  - returning to a prior SHA must reuse its counters
unknown: []
conflicts: []
first_failure:
  marker: same-SHA polling budget could reset
  evidence: regression fixture
rejected_hypotheses:
  - reset counters on owner invocation
changed_paths:
  - tools/agents/checkpoint.py
validation:
  - command: checkpoint regression
    result: PASS
    evidence: network-free validator
blockers: []
next_action: Run exact-head validation.
```
"""


def _write_task(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "task.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_checkpoint_v2_reuses_prior_sha_history_after_a_b_a(tmp_path: Path) -> None:
    history = (
        f"  {SHA_A}:\n"
        "    ci: 2\n"
        "    review: 1\n"
        f"  {SHA_B}:\n"
        "    ci: 1\n"
        "    review: 2\n"
    )
    path = _write_task(
        tmp_path,
        _checkpoint_text(version=2, head=SHA_A, ci=2, review=1, history=history),
    )

    data = parse_checkpoint(path)

    assert data is not None
    assert validate_checkpoint(data, path) == []
    assert data["observation_counters_by_sha"] == {
        SHA_A: {"ci": "2", "review": "1"},
        SHA_B: {"ci": "1", "review": "2"},
    }


def test_checkpoint_v2_rejects_reset_for_previously_observed_sha(tmp_path: Path) -> None:
    history = (
        f"  {SHA_A}:\n"
        "    ci: 2\n"
        "    review: 1\n"
        f"  {SHA_B}:\n"
        "    ci: 1\n"
        "    review: 2\n"
    )
    path = _write_task(
        tmp_path,
        _checkpoint_text(version=2, head=SHA_A, ci=0, review=0, history=history),
    )

    data = parse_checkpoint(path)

    assert data is not None
    errors = validate_checkpoint(data, path)
    assert any("ci_checks_for_current_head does not match" in error for error in errors)
    assert any("review_checks_for_current_head does not match" in error for error in errors)


def test_checkpoint_v1_remains_readable_for_legacy_records(tmp_path: Path) -> None:
    path = _write_task(tmp_path, _checkpoint_text(version=1, head=SHA_A))

    data = parse_checkpoint(path)

    assert data is not None
    assert validate_checkpoint(data, path) == []
