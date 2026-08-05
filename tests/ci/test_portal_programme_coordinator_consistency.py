import re
from pathlib import Path


PROGRAMME_PATH = Path("docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md")
COORDINATOR_PATH = Path(
    "docs/agents/tasks/active/FTAI-20260803-portal-remediation-program.md"
)


def _issue_states() -> dict[int, str]:
    states: dict[int, str] = {}
    for line in PROGRAMME_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| #"):
            continue
        columns = [column.strip() for column in line.strip("|").split("|")]
        states[int(columns[0].removeprefix("#"))] = columns[3]
    return states


def _current_issue() -> int:
    coordinator = COORDINATOR_PATH.read_text(encoding="utf-8")
    match = re.search(r"^current_child_task: .*?(\d+).*?$", coordinator, re.MULTILINE)
    assert match is not None, "coordinator must select exactly one issue"
    return int(match.group(1))


def test_current_child_is_not_terminal_or_waiting() -> None:
    states = _issue_states()
    current_issue = _current_issue()
    assert states[current_issue] in {"READY", "ACTIVE"}


def test_satisfied_dependencies_are_not_still_waiting() -> None:
    states = _issue_states()
    for issue, state in states.items():
        match = re.fullmatch(r"WAITING_ON_(\d+)", state)
        if match is None:
            continue
        dependency = int(match.group(1))
        assert states[dependency] != "COMPLETE", (
            f"Issue #{issue} still waits on completed Issue #{dependency}"
        )


def test_schema_foundation_completion_unblocks_logout_replay_work() -> None:
    states = _issue_states()
    coordinator = COORDINATOR_PATH.read_text(encoding="utf-8")
    programme = PROGRAMME_PATH.read_text(encoding="utf-8")

    assert states[1122] == "COMPLETE"
    assert states[1132] == "READY"
    assert _current_issue() == 1132
    assert re.search(r"^next_action: .*1132", coordinator, re.MULTILINE)
    next_action = programme.split("## Programme next action", maxsplit=1)[1]
    assert "#1132" in next_action
    assert "Create the durable Issue `#1122` task" not in next_action
