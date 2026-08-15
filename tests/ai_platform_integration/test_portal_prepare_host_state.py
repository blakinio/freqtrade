from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "deploy"
    / "synology"
    / "portal-oidc"
    / "prepare_host_state.py"
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("portal_prepare_host_state_tested", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_helper_run_args_include_deterministic_ownership() -> None:
    module = _load_module()
    args = module._helper_run_args(
        "example/image@sha256:" + "1" * 64,
        helper_name="portal-prepare-host-123",
        helper_labels=(
            "io.freqtrade.owner=github-actions:123",
            "io.freqtrade.purpose=portal-host-preparation",
        ),
    )

    name_index = args.index("--name")
    assert args[name_index + 1] == "portal-prepare-host-123"
    label_values = [args[index + 1] for index, value in enumerate(args) if value == "--label"]
    assert label_values == [
        "io.freqtrade.owner=github-actions:123",
        "io.freqtrade.purpose=portal-host-preparation",
    ]


def test_main_derives_github_run_ownership(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module()
    captured: dict[str, object] = {}

    def fake_prepare(
        repo: Path, *, helper_name: str | None, helper_labels: tuple[str, ...]
    ) -> None:
        captured.update(
            repo=repo,
            helper_name=helper_name,
            helper_labels=helper_labels,
        )

    monkeypatch.setattr(module, "prepare", fake_prepare)
    monkeypatch.setenv("GITHUB_RUN_ID", "456")
    monkeypatch.setattr(sys, "argv", ["prepare_host_state.py", "--repository", str(tmp_path)])

    assert module.main() == 0
    assert captured["repo"] == tmp_path.resolve()
    assert captured["helper_name"] == "portal-prepare-host-456"
    assert captured["helper_labels"] == (
        "io.freqtrade.owner=github-actions:456",
        "io.freqtrade.purpose=portal-host-preparation",
    )


def test_prepare_removes_named_helper_when_run_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_module()
    cleanup_commands: list[list[str]] = []

    def completed(stdout: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], 0, stdout=stdout, stderr="")

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        if command == module._preflight_command():
            return completed()
        if command[-3:] == ["ps", "-q", "server"]:
            return completed("server-id\n")
        if command[:4] == ["docker", "inspect", "--format", "{{.Config.Image}}"]:
            return completed("example/image:trusted\n")
        if command[:2] == ["docker", "run"]:
            raise module.PreparationError("synthetic helper failure")
        raise AssertionError(f"unexpected command: {command}")

    def fake_subprocess_run(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        cleanup_commands.append(command)
        return completed()

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_compose_command", lambda _repo: ["docker", "compose"])
    monkeypatch.setattr(module.subprocess, "run", fake_subprocess_run)

    with pytest.raises(module.PreparationError, match="synthetic helper failure"):
        module.prepare(
            tmp_path,
            helper_name="portal-prepare-host-789",
            helper_labels=("io.freqtrade.owner=github-actions:789",),
        )

    assert cleanup_commands == [
        ["docker", "rm", "-f", "portal-prepare-host-789"],
        ["docker", "rm", "-f", "portal-prepare-host-789"],
    ]
