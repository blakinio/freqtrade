from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DEPLOYMENT = ROOT / "deploy" / "synology" / "portal-oidc"
WORKFLOW = ROOT / ".github" / "workflows" / "portal-oidc-public-deploy.yml"
SPEC = importlib.util.spec_from_file_location(
    "portal_oidc_prepare_host_state",
    DEPLOYMENT / "prepare_host_state.py",
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_helper_uses_host_visible_bind_with_minimal_runtime() -> None:
    args = module._helper_run_args("authentik-image")

    mount_index = args.index("--mount")
    assert args[mount_index + 1] == "type=bind,src=/volume1/docker,dst=/host-volume"
    assert args[args.index("--network") + 1] == "none"
    assert args[args.index("--entrypoint") + 1] == "python"
    assert args[args.index("--user") + 1] == "0:0"
    assert "--privileged" not in args
    assert "/var/run/docker.sock" not in " ".join(args)
    assert args.count("--cap-add") == 3
    assert {"CHOWN", "DAC_OVERRIDE", "FOWNER"}.issubset(args)

    script = args[-1]
    assert "/host-volume/freqtrade-portal-oidc/data" in script
    assert "os.chown(path, 10001, 10001)" in script
    assert "path.chmod(0o700)" in script
    assert "portal data mode mismatch" in script


def test_prepare_reuses_running_authentik_server_image(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runtime_env = tmp_path / "runtime.env"
    runtime_env.write_text("AUTHENTIK_SECRET_KEY=redacted\n", encoding="utf-8")
    runtime_env.chmod(0o600)
    monkeypatch.setattr(module, "AUTHENTIK_STATE_DIR", tmp_path)

    commands: list[list[str]] = []

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[-3:] == ["ps", "-q", "server"]:
            return subprocess.CompletedProcess(command, 0, "server-container\n", "")
        if command[:4] == ["docker", "inspect", "--format", "{{.Config.Image}}"]:
            return subprocess.CompletedProcess(command, 0, "authentik-image\n", "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(module, "_run", fake_run)
    module.prepare(tmp_path)

    assert commands[-1] == module._helper_run_args("authentik-image")


def test_public_workflow_prepares_host_state_before_deployer() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    helper = "Prepare Synology host Portal state directory"
    deploy = "Apply provider and deploy public Portal OIDC"
    assert "python3 deploy/synology/portal-oidc/prepare_host_state.py" in workflow
    assert workflow.index(helper) < workflow.index(deploy)
