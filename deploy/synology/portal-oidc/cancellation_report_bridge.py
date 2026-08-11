from __future__ import annotations

from pathlib import Path
from typing import Any, cast


_CANCELLATION_FAILURE_MESSAGE = "protected deployment cancellation requires rollback"
_FALLBACK_FAILURE_MESSAGE = "protected deployment cancellation recovery did not complete cleanly"


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
        "request_id": getattr(deploy, "REQUEST_ID", "portal-authentik-public-oidc-20260801-v1"),
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


def install(deploy: Any) -> None:
    """Persist cancellation evidence through canonical rollback, then re-raise cancellation."""

    original_run = deploy._run
    original_write_report = deploy._write_report
    original_deploy = deploy.deploy
    deploy._portal_pending_cancellation = None

    def guarded_run(
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

    def write_report(path: Path, report: dict[str, Any]) -> str:
        pending = _pending_cancellation(deploy)
        if pending is not None:
            report["cancellation"] = _cancellation_metadata(pending)
        return cast(str, original_write_report(path, report))

    def guarded_deploy(args: Any) -> int:
        try:
            return_code = int(original_deploy(args))
        except BaseException as exc:
            pending = _pending_cancellation(deploy)
            if pending is None:
                raise
            try:
                deploy._write_report(
                    Path(args.report).resolve(),
                    _fallback_report(deploy, args, pending),
                )
            except Exception as report_exc:
                deploy._portal_pending_cancellation = None
                raise pending from report_exc
            deploy._portal_pending_cancellation = None
            raise pending from exc

        pending = _pending_cancellation(deploy)
        if pending is not None:
            deploy._portal_pending_cancellation = None
            raise pending
        return return_code

    deploy._run = guarded_run
    deploy._write_report = write_report
    deploy.deploy = guarded_deploy
