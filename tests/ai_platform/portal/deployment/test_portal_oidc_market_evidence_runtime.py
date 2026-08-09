from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "market_evidence_runtime.py"
SPEC = importlib.util.spec_from_file_location("portal_oidc_market_evidence_runtime", MODULE_PATH)
assert SPEC and SPEC.loader
runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime
SPEC.loader.exec_module(runtime)


IMAGE = "local/freqtrade-portal-web:test"
RUN_ID = "wickhunter-production-market-evidence-20260808-v2-r1"
BASE_RUN_ID = "wickhunter-production-market-evidence-20260808-v1-r1"
ACTIVE_RUN_ID = "wickhunter-production-market-evidence-20260809-v1-r2"
RUN_ROOT = runtime.MARKET_EVIDENCE_HOST_ROOT / "runs" / RUN_ID
BASE_RUN_ROOT = runtime.MARKET_EVIDENCE_HOST_ROOT / "runs" / BASE_RUN_ID
ACTIVE_RUN_ROOT = runtime.MARKET_EVIDENCE_HOST_ROOT / "runs" / ACTIVE_RUN_ID


def _completed(command: list[str], stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")


def _v2_selection() -> Any:
    return runtime.MarketEvidenceSelection(
        run_id=RUN_ID,
        group_id="321",
        host_run_root=RUN_ROOT,
        version=2,
        base_v1_run_id=BASE_RUN_ID,
        base_v1_group_id="654",
        base_v1_host_root=BASE_RUN_ROOT,
    )


def test_preselection_returns_latest_pinned_run_and_bound_base_metadata() -> None:
    payload = {
        "run_id": RUN_ID,
        "group_id": "321",
        "layout": "runs",
        "has_package": True,
        "base_v1_run_id": BASE_RUN_ID,
        "base_v1_group_id": "654",
        "base_v1_layout": "runs",
    }

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        assert command[-2] == "-e"
        assert runtime.MARKET_EVIDENCE_SELECTION_MARKER in command[-1]
        return _completed(
            command,
            f"noise\n{runtime.MARKET_EVIDENCE_SELECTION_MARKER}{json.dumps(payload)}\n",
        )

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)
    assert runtime._preselect(deploy, IMAGE) == payload


def test_canonical_verifier_runs_as_web_user_with_exact_selected_and_base_mounts() -> None:
    preselection = {
        "run_id": RUN_ID,
        "group_id": "321",
        "layout": "runs",
        "has_package": True,
        "base_v1_run_id": BASE_RUN_ID,
        "base_v1_group_id": "654",
        "base_v1_layout": "runs",
    }

    args = runtime._canonical_verifier_args(IMAGE, preselection)

    assert runtime.WEB_RUNTIME_USER in args
    assert args.count("--group-add") == 2
    assert "321" in args and "654" in args
    assert (
        f"type=bind,src={RUN_ROOT},dst={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}/{RUN_ID},readonly"
    ) in args
    assert (
        f"type=bind,src={BASE_RUN_ROOT},"
        f"dst={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}/{BASE_RUN_ID},readonly"
    ) in args
    assert runtime.MARKET_EVIDENCE_VERIFIER in args
    assert args[-2:] == [runtime.MARKET_EVIDENCE_CONTAINER_ROOT, RUN_ID]
    rendered_selection = runtime._selection_script()
    assert "canonicalSha256" not in rendered_selection
    assert "verification_result" not in rendered_selection


def test_immutable_selection_requires_canonical_verifier_to_confirm_v2_base() -> None:
    preselection = {
        "run_id": RUN_ID,
        "group_id": "321",
        "layout": "runs",
        "has_package": True,
        "base_v1_run_id": BASE_RUN_ID,
        "base_v1_group_id": "654",
        "base_v1_layout": "runs",
    }
    marker = {
        "run_id": RUN_ID,
        "version": 2,
        "base_v1_run_id": BASE_RUN_ID,
    }

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return _completed(
            command,
            f"{runtime.MARKET_EVIDENCE_VERIFIED_MARKER}{json.dumps(marker)}\n",
        )

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)
    selection = runtime._verify_immutable_selection(deploy, IMAGE, preselection)

    assert selection == _v2_selection()

    marker["base_v1_run_id"] = "wickhunter-production-market-evidence-20260807-v1-r9"
    with pytest.raises(RuntimeError, match="base-v1 binding mismatch"):
        runtime._verify_immutable_selection(deploy, IMAGE, preselection)


def test_active_selection_is_verified_as_runtime_user_and_pins_active_pointer(
    tmp_path: Path,
) -> None:
    preselection = {
        "run_id": ACTIVE_RUN_ID,
        "group_id": "321",
        "layout": "runs",
        "has_package": False,
        "base_v1_run_id": None,
        "base_v1_group_id": None,
        "base_v1_layout": None,
    }
    calls: list[list[str]] = []

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return _completed(command, f"{runtime.MARKET_EVIDENCE_ACTIVE_MARKER}{ACTIVE_RUN_ID}\n")

    deploy = SimpleNamespace(
        _run=run,
        DeploymentError=RuntimeError,
        PORTAL_STATE_DIR=tmp_path,
    )
    selection = runtime._verify_active_selection(deploy, IMAGE, preselection)

    assert runtime.WEB_RUNTIME_USER in calls[0]
    assert "--group-add" in calls[0]
    assert (
        f"type=bind,src={ACTIVE_RUN_ROOT},"
        f"dst={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}/{ACTIVE_RUN_ID},readonly"
    ) in calls[0]
    assert selection.version is None
    assert selection.active_pointer_host is not None
    assert json.loads(selection.active_pointer_host.read_text(encoding="utf-8")) == {
        "run_id": ACTIVE_RUN_ID
    }
    assert selection.active_pointer_host.stat().st_mode & 0o777 == 0o644


def test_market_web_args_mounts_selected_v2_and_bound_v1_only() -> None:
    def original(image: str, name: str, *, publish: bool) -> list[str]:
        del name, publish
        return ["docker", "run", "--group-add", "123", image]

    selection = _v2_selection()
    args = runtime._market_web_args(original, selection, IMAGE, "candidate", publish=False)

    assert args[-1] == IMAGE
    assert args.count("--group-add") == 3
    assert (
        f"type=bind,src={RUN_ROOT},dst={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}/{RUN_ID},readonly"
    ) in args
    assert (
        f"type=bind,src={BASE_RUN_ROOT},"
        f"dst={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}/{BASE_RUN_ID},readonly"
    ) in args
    assert f"PORTAL_MARKET_EVIDENCE_RUN_ID={RUN_ID}" in args
    assert f"PORTAL_MARKET_EVIDENCE_BASE_V1_RUN_ID={BASE_RUN_ID}" in args
    assert f"PORTAL_MARKET_EVIDENCE_DATA_ROOT={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}" in args


def test_market_web_args_mounts_pinned_pointer_for_active_v1(tmp_path: Path) -> None:
    pointer = tmp_path / "pointer.json"
    pointer.write_text(json.dumps({"run_id": ACTIVE_RUN_ID}), encoding="utf-8")
    selection = runtime.MarketEvidenceSelection(
        run_id=ACTIVE_RUN_ID,
        group_id="321",
        host_run_root=ACTIVE_RUN_ROOT,
        version=None,
        active_pointer_host=pointer,
    )

    def original(image: str, name: str, *, publish: bool) -> list[str]:
        del name, publish
        return ["docker", "run", image]

    args = runtime._market_web_args(original, selection, IMAGE, "candidate", publish=False)
    assert (
        f"type=bind,src={pointer},"
        f"dst={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}/{runtime.MARKET_EVIDENCE_ACTIVE_POINTER},readonly"
    ) in args
    assert not any("BASE_V1_RUN_ID" in value for value in args)


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


def test_running_container_verification_requires_exact_v2_mount_inventory() -> None:
    selection = _v2_selection()
    inspect_payload: list[dict[str, Any]] = [
        {
            "Mounts": [
                {
                    "Type": "bind",
                    "Source": str(RUN_ROOT),
                    "Destination": f"{runtime.MARKET_EVIDENCE_CONTAINER_ROOT}/{RUN_ID}",
                    "RW": False,
                },
                {
                    "Type": "bind",
                    "Source": str(BASE_RUN_ROOT),
                    "Destination": f"{runtime.MARKET_EVIDENCE_CONTAINER_ROOT}/{BASE_RUN_ID}",
                    "RW": False,
                },
            ],
            "Config": {
                "Env": [
                    f"PORTAL_MARKET_EVIDENCE_DATA_ROOT={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}",
                    f"PORTAL_MARKET_EVIDENCE_TENANT_ID={runtime.MARKET_EVIDENCE_TENANT_ID}",
                    f"PORTAL_MARKET_EVIDENCE_RUN_ID={RUN_ID}",
                    f"PORTAL_MARKET_EVIDENCE_BASE_V1_RUN_ID={BASE_RUN_ID}",
                ]
            },
            "HostConfig": {"GroupAdd": ["321", "654"]},
        }
    ]

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return _completed(command, json.dumps(inspect_payload))

    deploy = SimpleNamespace(
        _run=run,
        DeploymentError=RuntimeError,
        PORTAL_CONTAINER="freqtrade-portal-web",
    )

    runtime._verify_running_container(deploy, selection)

    mounts = inspect_payload[0]["Mounts"]
    assert isinstance(mounts, list)
    mounts.append(
        {
            "Type": "bind",
            "Source": "/mutable-parent",
            "Destination": runtime.MARKET_EVIDENCE_CONTAINER_ROOT,
            "RW": False,
        }
    )
    with pytest.raises(RuntimeError, match="inventory is not pinned"):
        runtime._verify_running_container(deploy, selection)


def test_install_injects_same_pinned_contract_for_candidate_and_final_web_then_restores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_args: list[list[str]] = []
    selection = _v2_selection()

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

    monkeypatch.setattr(runtime, "_select_market_evidence", lambda _deploy, _image: selection)
    monkeypatch.setattr(runtime, "_assert_tenant_authorized", lambda _deploy: None)
    monkeypatch.setattr(runtime, "_verify_running_container", lambda _deploy, _selection: None)

    runtime.install(deploy)
    original_after_install = deploy._web_run_args
    deploy._deploy_web(IMAGE, "abc")

    assert deploy._web_run_args is original_after_install
    assert len(seen_args) == 2
    for args in seen_args:
        assert f"PORTAL_MARKET_EVIDENCE_TENANT_ID={runtime.MARKET_EVIDENCE_TENANT_ID}" in args
        assert f"PORTAL_MARKET_EVIDENCE_RUN_ID={RUN_ID}" in args
        assert f"PORTAL_MARKET_EVIDENCE_BASE_V1_RUN_ID={BASE_RUN_ID}" in args
        assert (
            f"type=bind,src={RUN_ROOT},"
            f"dst={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}/{RUN_ID},readonly"
        ) in args
        assert (
            f"type=bind,src={BASE_RUN_ROOT},"
            f"dst={runtime.MARKET_EVIDENCE_CONTAINER_ROOT}/{BASE_RUN_ID},readonly"
        ) in args