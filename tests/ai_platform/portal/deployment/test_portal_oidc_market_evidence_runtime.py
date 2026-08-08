from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "market_evidence_runtime.py"
SPEC = importlib.util.spec_from_file_location("portal_oidc_market_evidence_runtime", MODULE_PATH)
assert SPEC and SPEC.loader
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


IMAGE = "local/freqtrade-portal-web:test"


def _completed(command: list[str], stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")


def test_market_web_args_adds_canonical_read_only_mount_identity_and_group() -> None:
    def original(image: str, name: str, *, publish: bool) -> list[str]:
        del name, publish
        return ["docker", "run", "--group-add", "123", image]

    args = runtime._market_web_args(original, "456", IMAGE, "candidate", publish=False)

    assert args[-1] == IMAGE
    assert args.count("--group-add") == 2
    assert "456" in args
    assert (
        f"type=bind,src={runtime.MARKET_EVIDENCE_HOST_ROOT},"
        f"dst={runtime.MARKET_EVIDENCE_CONTAINER_ROOT},readonly"
    ) in args
    assert f"PORTAL_MARKET_EVIDENCE_DATA_ROOT={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}" in args
    assert f"PORTAL_MARKET_EVIDENCE_TENANT_ID={runtime.MARKET_EVIDENCE_TENANT_ID}" in args
    assert "ai.freqtrade.market-evidence=read-only" in args


def test_market_web_args_does_not_duplicate_existing_supplementary_group() -> None:
    def original(image: str, name: str, *, publish: bool) -> list[str]:
        del name, publish
        return ["docker", "run", "--group-add", "456", image]

    args = runtime._market_web_args(original, "456", IMAGE, "candidate", publish=False)

    assert args.count("--group-add") == 1


def test_docker_host_preflight_requires_valid_immutable_run_marker() -> None:
    run_id = "wickhunter-production-market-evidence-20260808-v2-r1"

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return _completed(
            command,
            f"noise\n{runtime.MARKET_EVIDENCE_PROBE_MARKER}{run_id}|321\n",
        )

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)

    assert runtime._docker_host_group(deploy, IMAGE) == (run_id, "321")

    def invalid_run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return _completed(
            command,
            f"{runtime.MARKET_EVIDENCE_PROBE_MARKER}latest|321\n",
        )

    deploy._run = invalid_run
    with pytest.raises(RuntimeError, match="invalid metadata"):
        runtime._docker_host_group(deploy, IMAGE)


def test_docker_host_preflight_requires_active_run_metadata_without_package() -> None:
    rendered = runtime._probe_script()

    assert '"incremental-state.json"' in rendered
    assert '"run-request.json"' in rendered
    assert '"manifest.json"' in rendered
    assert '"run-state.json"' in rendered
    assert '"verification-report.json"' in rendered


def test_tenant_authorization_probe_is_fail_closed() -> None:
    calls: list[list[str]] = []

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return _completed(command, "")

    deploy = SimpleNamespace(
        _run=run,
        DeploymentError=RuntimeError,
        CONTROL_CONTAINER="freqtrade-portal-control-plane",
    )

    with pytest.raises(RuntimeError, match="returned no marker"):
        runtime._assert_tenant_authorized(deploy)

    rendered = calls[0][-1]
    assert runtime.MARKET_EVIDENCE_TENANT_ID in rendered
    assert "MembershipStatus.ACTIVE.value" in rendered
    assert "IdentityPrincipalRow" in rendered
    assert "PrincipalStatus.ACTIVE.value" in rendered
    assert "IdentityPrincipalRow.principal_id == TenantMembershipRow.principal_id" in rendered
    for role in runtime.AUTHORIZED_ROLES:
        assert role in rendered


def test_running_container_verification_requires_exact_read_only_contract() -> None:
    inspect_payload: list[dict[str, Any]] = [
        {
            "Mounts": [
                {
                    "Type": "bind",
                    "Source": str(runtime.MARKET_EVIDENCE_HOST_ROOT),
                    "Destination": runtime.MARKET_EVIDENCE_CONTAINER_ROOT,
                    "RW": False,
                }
            ],
            "Config": {
                "Env": [
                    (f"PORTAL_MARKET_EVIDENCE_DATA_ROOT={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}"),
                    (f"PORTAL_MARKET_EVIDENCE_TENANT_ID={runtime.MARKET_EVIDENCE_TENANT_ID}"),
                ]
            },
            "HostConfig": {"GroupAdd": ["321"]},
        }
    ]

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return _completed(command, json.dumps(inspect_payload))

    deploy = SimpleNamespace(
        _run=run,
        DeploymentError=RuntimeError,
        PORTAL_CONTAINER="freqtrade-portal-web",
    )

    runtime._verify_running_container(deploy, "321")

    mounts = inspect_payload[0]["Mounts"]
    assert isinstance(mounts, list)
    mounts[0]["RW"] = True
    with pytest.raises(RuntimeError, match="canonical read-only bind"):
        runtime._verify_running_container(deploy, "321")


def test_install_injects_contract_for_candidate_and_final_web_then_restores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_args: list[list[str]] = []

    def base_args(image: str, name: str, *, publish: bool) -> list[str]:
        del name, publish
        return ["docker", "run", image]

    def deploy_web(image: str, suffix: str) -> tuple[str | None, str]:
        del suffix
        seen_args.append(deploy._web_run_args(image, "candidate", publish=False))
        seen_args.append(deploy._web_run_args(image, "final", publish=True))
        return None, "https://auth.example/authorize"

    deploy = SimpleNamespace(
        _deploy_web=deploy_web,
        _web_run_args=base_args,
        DeploymentError=RuntimeError,
    )

    monkeypatch.setattr(
        runtime,
        "_docker_host_group",
        lambda _deploy, _image: (
            "wickhunter-production-market-evidence-20260808-v2-r1",
            "321",
        ),
    )
    monkeypatch.setattr(runtime, "_assert_tenant_authorized", lambda _deploy: None)
    monkeypatch.setattr(runtime, "_verify_running_container", lambda _deploy, _gid: None)

    runtime.install(deploy)
    original_after_install = deploy._web_run_args
    deploy._deploy_web(IMAGE, "abc")

    assert deploy._web_run_args is original_after_install
    assert len(seen_args) == 2
    for args in seen_args:
        assert f"PORTAL_MARKET_EVIDENCE_TENANT_ID={runtime.MARKET_EVIDENCE_TENANT_ID}" in args
        assert f"PORTAL_MARKET_EVIDENCE_DATA_ROOT={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}" in args
