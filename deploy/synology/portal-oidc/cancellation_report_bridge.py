from __future__ import annotations

import json
import signal
from collections.abc import Callable
from functools import partial
from pathlib import Path
from types import FrameType
from typing import Any, cast


_CANCELLATION_FAILURE_MESSAGE = "protected deployment cancellation requires rollback"
_FALLBACK_FAILURE_MESSAGE = "protected deployment cancellation recovery did not complete cleanly"
_TERMINATION_SIGNALS = (signal.SIGINT, signal.SIGTERM)


def _pending_cancellation(deploy: Any) -> BaseException | None:
    pending = getattr(deploy, "_portal_pending_cancellation", None)
    return pending if isinstance(pending, BaseException) else None


def _cancellation_metadata(pending: BaseException) -> dict[str, object]:
    return {
        "type": type(pending).__name__,
        "propagated_after_report": True,
    }


def _fallback_report(deploy: Any, args: Any, pending: BaseException) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "request_id": getattr(
            deploy,
            "REQUEST_ID",
            "portal-authentik-public-oidc-20260801-v1",
        ),
        "implementation_sha": str(args.expected_repository_sha),
        "status": "failed",
        "secret_values_recorded": False,
        "live_capital_authorized": False,
        "public_ingress_authorized": True,
        "restore_authorized": False,
        "identity_fixture_disabled": False,
        "membership_bootstrap": "not_authorized",
        "browser_acceptance": "not_executed",
        "failure": {
            "type": "CancellationRecoveryError",
            "message": _FALLBACK_FAILURE_MESSAGE,
        },
        "cancellation": _cancellation_metadata(pending),
    }


def _existing_canonical_report(deploy: Any, args: Any, path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("request_id") != getattr(deploy, "REQUEST_ID", None):
        return None
    if payload.get("implementation_sha") != str(args.expected_repository_sha):
        return None
    return cast(dict[str, Any], payload)


def _cancellation_report(
    deploy: Any,
    args: Any,
    pending: BaseException,
    path: Path,
) -> dict[str, Any]:
    report = _existing_canonical_report(deploy, args, path)
    if report is None:
        return _fallback_report(deploy, args, pending)
    report["status"] = "failed"
    report.setdefault(
        "failure",
        {
            "type": "CancellationRecoveryError",
            "message": _CANCELLATION_FAILURE_MESSAGE,
        },
    )
    return report


def _termination_exception(signum: int) -> BaseException:
    if signum == signal.SIGINT:
        return KeyboardInterrupt()
    return SystemExit(128 + signum)


def _termination_handler(deploy: Any) -> Callable[[int, FrameType | None], None]:
    def handle_termination(signum: int, _frame: FrameType | None) -> None:
        pending = _pending_cancellation(deploy)
        if pending is None:
            pending = _termination_exception(signum)
            deploy._portal_pending_cancellation = pending
        raise deploy.DeploymentError(_CANCELLATION_FAILURE_MESSAGE) from pending

    return handle_termination


def _guarded_run(
    deploy: Any,
    original_run: Callable[..., Any],
    command: list[str],
    *,
    cwd: Path | None = None,
    sensitive: bool = False,
    check: bool = True,
) -> Any:
    try:
        return original_run(
            command,
            cwd=cwd,
            sensitive=sensitive,
            check=check,
        )
    except BaseException as exc:
        if isinstance(exc, Exception):
            raise
        if _pending_cancellation(deploy) is None:
            deploy._portal_pending_cancellation = exc
        raise deploy.DeploymentError(_CANCELLATION_FAILURE_MESSAGE) from exc


def _guarded_write_report(
    deploy: Any,
    original_write_report: Callable[[Path, dict[str, Any]], str],
    path: Path,
    report: dict[str, Any],
) -> str:
    pending = _pending_cancellation(deploy)
    if pending is not None:
        report["status"] = "failed"
        report["cancellation"] = _cancellation_metadata(pending)
    return cast(str, original_write_report(path, report))


def _install_termination_handlers(deploy: Any) -> dict[int, Any]:
    previous_handlers: dict[int, Any] = {
        signum: signal.getsignal(signum) for signum in _TERMINATION_SIGNALS
    }
    handler = _termination_handler(deploy)
    for signum in _TERMINATION_SIGNALS:
        signal.signal(signum, handler)
    return previous_handlers


def _restore_termination_handlers(previous_handlers: dict[int, Any]) -> None:
    for signum, previous_handler in previous_handlers.items():
        signal.signal(signum, previous_handler)


def _raise_pending_after_fallback(
    deploy: Any,
    args: Any,
    pending: BaseException,
    cause: BaseException,
) -> None:
    report_path = Path(args.report).resolve()
    try:
        deploy._write_report(
            report_path,
            _cancellation_report(deploy, args, pending, report_path),
        )
    except Exception as report_exc:
        deploy._portal_pending_cancellation = None
        raise pending from report_exc
    deploy._portal_pending_cancellation = None
    raise pending from cause


def _guarded_deploy(
    deploy: Any,
    original_deploy: Callable[[Any], int],
    args: Any,
) -> int:
    previous_handlers = _install_termination_handlers(deploy)
    try:
        try:
            return_code = int(original_deploy(args))
        except BaseException as exc:
            pending = _pending_cancellation(deploy)
            if pending is None:
                raise
            _raise_pending_after_fallback(deploy, args, pending, exc)
    finally:
        _restore_termination_handlers(previous_handlers)

    pending = _pending_cancellation(deploy)
    if pending is not None:
        deploy._portal_pending_cancellation = None
        raise pending
    return return_code


def install(deploy: Any) -> None:
    """Persist cancellation evidence through canonical rollback, then re-raise cancellation."""

    original_run = deploy._run
    original_write_report = deploy._write_report
    original_deploy = deploy.deploy
    deploy._portal_pending_cancellation = None

    deploy._run = partial(_guarded_run, deploy, original_run)
    deploy._write_report = partial(_guarded_write_report, deploy, original_write_report)
    deploy.deploy = partial(_guarded_deploy, deploy, original_deploy)
