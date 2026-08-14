from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[4]
SCRIPT_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "bootstrap_owner_membership.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "portal-oidc-owner-bootstrap.yml"
SPEC = importlib.util.spec_from_file_location("portal_oidc_owner_bootstrap", SCRIPT_PATH)
assert SPEC and SPEC.loader
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


def _request(sha: str) -> dict[str, object]:
    return {
        "request_id": bootstrap.REQUEST_ID,
        "environment": "synology-staging",
        "runner": "freqtrade-staging",
        "implementation_sha": sha,
        "target_username": bootstrap.TARGET_USERNAME,
        "target_tenant_id": bootstrap.TARGET_TENANT_ID,
        "target_role": bootstrap.TARGET_ROLE,
        "subject_mode": bootstrap.SUBJECT_MODE,
        "bootstrap_membership_authorized": True,
        "browser_acceptance_authorized": False,
        "public_ingress_authorized": True,
        "live_capital_authorized": False,
        "restore_authorized": False,
        "secret_values_in_request": False,
    }


def test_owner_bootstrap_request_is_exact_and_frozen(tmp_path: Path) -> None:
    sha = "a" * 40
    request_path = tmp_path / bootstrap.REQUEST_RELATIVE_PATH
    request_path.parent.mkdir(parents=True)
    request_path.write_text(json.dumps(_request(sha)), encoding="utf-8")

    assert bootstrap._load_request(request_path, sha) == _request(sha)

    payload = _request(sha)
    payload["browser_acceptance_authorized"] = True
    request_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(bootstrap.BootstrapError, match="frozen contract"):
        bootstrap._load_request(request_path, sha)


def test_exact_owner_lookup_accepts_only_active_akadmin_uuid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subject = "12345678-1234-4234-9234-1234567890ab"
    output = {
        "username": bootstrap.TARGET_USERNAME,
        "subject": subject.upper(),
        "display_name": "Portal Owner",
        "email": "owner@example.com",
        "is_active": True,
    }

    def fake_run(
        command: list[str],
        *,
        input_text: str | None = None,
        sensitive: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        del command, input_text, sensitive, check
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="__PORTAL_OWNER__" + json.dumps(output),
            stderr="",
        )

    monkeypatch.setattr(bootstrap, "_run", fake_run)

    assert bootstrap._lookup_exact_owner("authentik-server") == {
        "username": bootstrap.TARGET_USERNAME,
        "subject": subject,
        "display_name": "Portal Owner",
        "email": "owner@example.com",
    }


def test_subject_is_sent_over_stdin_and_only_hash_is_validated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subject = "12345678-1234-4234-9234-1234567890ab"
    identity = {
        "username": bootstrap.TARGET_USERNAME,
        "subject": subject,
        "display_name": "Portal Owner",
        "email": "owner@example.com",
    }
    observed: dict[str, Any] = {}
    expected_hash = bootstrap.hashlib.sha256(subject.encode("utf-8")).hexdigest()
    result_payload = {
        "status": "success",
        "created": True,
        "principal_id": "principal-id",
        "membership_id": "membership-id",
        "tenant_id": bootstrap.TARGET_TENANT_ID,
        "role": bootstrap.TARGET_ROLE,
        "issuer": "https://auth.molehill.cloud/application/o/freqtrade-portal/",
        "subject_sha256": expected_hash,
        "secret_values_recorded": False,
        "live_capital_authorized": False,
    }

    def fake_run(
        command: list[str],
        *,
        input_text: str | None = None,
        sensitive: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        observed.update(
            command=command,
            input_text=input_text,
            sensitive=sensitive,
            check=check,
        )
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="__PORTAL_BOOTSTRAP__" + json.dumps(result_payload),
            stderr="",
        )

    monkeypatch.setattr(bootstrap, "_run", fake_run)

    assert bootstrap._bootstrap_exact_owner(identity) == result_payload
    command = observed["command"]
    assert isinstance(command, list)
    assert subject not in " ".join(command)
    input_payload = json.loads(str(observed["input_text"]))
    assert input_payload["subject"] == subject
    assert observed["sensitive"] is True


def test_expired_owner_bootstrap_workflow_is_absent() -> None:
    assert not WORKFLOW_PATH.exists()
