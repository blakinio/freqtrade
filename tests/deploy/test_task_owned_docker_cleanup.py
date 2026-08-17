from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path

MODULE_PATH = Path(__file__).parents[2] / "deploy" / "synology" / "task_owned_docker_cleanup.py"
spec = importlib.util.spec_from_file_location("task_owned_docker_cleanup", MODULE_PATH)
assert spec is not None and spec.loader is not None
cleanup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup_module)


def container(*, labels: dict[str, str], running: bool = False, status: str = "exited") -> dict:
    return {
        "Id": "a" * 64,
        "Name": "/temporary-test",
        "Config": {"Labels": labels},
        "State": {"Running": running, "Status": status},
    }


def eligible_labels(expires_at: str = "2026-08-16T00:00:00Z") -> dict[str, str]:
    return {
        cleanup_module.LIFECYCLE_LABEL: cleanup_module.EXPECTED_LIFECYCLE,
        cleanup_module.CLEANUP_LABEL: cleanup_module.EXPECTED_CLEANUP,
        cleanup_module.OWNER_TASK_LABEL: "FTAI-20260817-example",
        cleanup_module.EXPIRES_AT_LABEL: expires_at,
    }


def test_expired_stopped_task_owned_container_is_removable() -> None:
    decision = cleanup_module.decide(
        container(labels=eligible_labels()),
        datetime(2026, 8, 17, tzinfo=UTC),
    )
    assert decision.action == "remove"
    assert decision.reason == "expired_task_owned_temporary"


def test_expired_running_container_is_never_auto_removed() -> None:
    decision = cleanup_module.decide(
        container(labels=eligible_labels(), running=True, status="running"),
        datetime(2026, 8, 17, tzinfo=UTC),
    )
    assert decision.action == "keep"
    assert decision.reason == "expired_but_active"


def test_missing_owner_task_is_kept() -> None:
    labels = eligible_labels()
    labels.pop(cleanup_module.OWNER_TASK_LABEL)
    decision = cleanup_module.decide(container(labels=labels), datetime(2026, 8, 17, tzinfo=UTC))
    assert decision.action == "keep"
    assert decision.reason == "missing_owner_task"


def test_invalid_or_timezone_less_expiry_is_kept() -> None:
    for expires_at in ("not-a-date", "2026-08-16T00:00:00"):
        decision = cleanup_module.decide(
            container(labels=eligible_labels(expires_at)),
            datetime(2026, 8, 17, tzinfo=UTC),
        )
        assert decision.action == "keep"
        assert decision.reason == "invalid_expiry"


def test_future_expiry_is_kept() -> None:
    decision = cleanup_module.decide(
        container(labels=eligible_labels("2026-08-18T00:00:00Z")),
        datetime(2026, 8, 17, tzinfo=UTC),
    )
    assert decision.action == "keep"
    assert decision.reason == "not_expired"


def test_container_without_explicit_opt_in_is_kept() -> None:
    decision = cleanup_module.decide(
        container(labels={cleanup_module.OWNER_TASK_LABEL: "task"}),
        datetime(2026, 8, 17, tzinfo=UTC),
    )
    assert decision.action == "keep"
    assert decision.reason == "not_temporary"
