from __future__ import annotations

import fcntl
import json
import os
import signal
from collections.abc import Callable
from functools import partial
from pathlib import Path
from types import FrameType
from typing import Any, NoReturn, cast


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
    if getattr(deploy, "_portal_current_report_path", None) != path.resolve():
        return None
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
    def handle_termination(signum: int, frame: FrameType | None) -> None:
        if not getattr(deploy, "_portal_termination_handlers_active", False):
            previous_handlers = getattr(deploy, "_portal_previous_termination_handlers", {})
            _restore_termination_handlers(previous_handlers)
            previous = previous_handlers.get(signum, signal.SIG_DFL)
            if callable(previous):
                previous(signum, frame)
                return
            if previous == signal.SIG_IGN:
                return
            signal.raise_signal(signum)
            return
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
    deploy._portal_previous_termination_handlers = previous_handlers
    deploy._portal_termination_handlers_active = True
    handler = _termination_handler(deploy)
    for signum in _TERMINATION_SIGNALS:
        signal.signal(signum, handler)
    return previous_handlers


def _restore_termination_handlers(previous_handlers: dict[int, Any]) -> None:
    for signum, previous_handler in previous_handlers.items():
        signal.signal(signum, previous_handler)


def _block_termination_signals() -> set[signal.Signals]:
    return cast(
        set[signal.Signals],
        signal.pthread_sigmask(signal.SIG_BLOCK, _TERMINATION_SIGNALS),
    )


def _raise_pending_after_fallback(
    deploy: Any,
    args: Any,
    pending: BaseException,
    cause: BaseException,
) -> NoReturn:
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


def _release_current_report_lock(deploy: Any) -> None:
    lock_fd = getattr(deploy, "_portal_report_lock_fd", None)
    deploy._portal_report_lock_fd = None
    if isinstance(lock_fd, int):
        try:
            os.close(lock_fd)
        except OSError:
            pass


def _reserve_current_report_path(deploy: Any, args: Any) -> None:
    report_path = Path(args.report).resolve()
    lock_path = report_path.with_name(f".{report_path.name}.lock")
    lock_fd: int | None = None
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        lock_fd = os.open(lock_path, flags, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise deploy.DeploymentError(
                "protected deployment report path is already owned by another invocation"
            ) from exc
        deploy._portal_report_lock_fd = lock_fd
        lock_fd = None
    except deploy.DeploymentError:
        if lock_fd is not None:
            os.close(lock_fd)
        _release_current_report_lock(deploy)
        raise
    except OSError as exc:
        if lock_fd is not None:
            try:
                os.close(lock_fd)
            except OSError:
                pass
        _release_current_report_lock(deploy)
        raise deploy.DeploymentError(
            "protected deployment could not reserve current report evidence"
        ) from exc


def _clear_current_report_path(deploy: Any, args: Any) -> None:
    report_path = Path(args.report).resolve()
    try:
        if report_path.exists():
            if not report_path.is_file():
                raise deploy.DeploymentError(
                    "protected deployment report path is not a regular file"
                )
            report_path.unlink()
    except deploy.DeploymentError:
        raise
    except OSError as exc:
        raise deploy.DeploymentError(
            "protected deployment could not clear stale report evidence"
        ) from exc
    deploy._portal_current_report_path = report_path


def _guarded_deploy(
    deploy: Any,
    original_deploy: Callable[[Any], int],
    args: Any,
) -> int:
    deploy._portal_current_report_path = None
    previous_handlers: dict[int, Any] | None = None
    entry_mask = _block_termination_signals()
    try:
        _reserve_current_report_path(deploy, args)
        previous_handlers = _install_termination_handlers(deploy)
        try:
            signal.pthread_sigmask(signal.SIG_SETMASK, entry_mask)
            _clear_current_report_path(deploy, args)
            return_code = int(original_deploy(args))
            pending = _pending_cancellation(deploy)
            if pending is not None:
                deploy._portal_pending_cancellation = None
                raise pending
            return return_code
        except BaseException as exc:
            pending = _pending_cancellation(deploy)
            if pending is None:
                raise
            _raise_pending_after_fallback(deploy, args, pending, exc)
    finally:
        if previous_handlers is None:
            signal.pthread_sigmask(signal.SIG_SETMASK, entry_mask)
        try:
            _release_current_report_lock(deploy)
        except BaseException as exc:
            pending = _pending_cancellation(deploy)
            if pending is None:
                raise
            _raise_pending_after_fallback(deploy, args, pending, exc)
        finally:
            if previous_handlers is not None:
                deploy._portal_termination_handlers_active = False
                _restore_termination_handlers(previous_handlers)


def install(deploy: Any) -> None:
    """Persist cancellation evidence through canonical rollback, then re-raise cancellation."""

    original_run = deploy._run
    original_write_report = deploy._write_report
    original_deploy = deploy.deploy
    deploy._portal_pending_cancellation = None
    deploy._portal_current_report_path = None
    deploy._portal_report_lock_fd = None
    deploy._portal_previous_termination_handlers = {}
    deploy._portal_termination_handlers_active = False

    deploy._run = partial(_guarded_run, deploy, original_run)
    deploy._write_report = partial(_guarded_write_report, deploy, original_write_report)
    deploy.deploy = partial(_guarded_deploy, deploy, original_deploy)
