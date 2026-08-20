from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType


def _runtime_module() -> ModuleType:
    tools_agents = str(Path("tools/agents").resolve())
    sys.path.insert(0, tools_agents)
    try:
        return importlib.import_module("portal_supply_chain_runtime")
    finally:
        sys.path.remove(tools_agents)


def test_dynamic_module_loader_registers_dataclass_module_before_exec(tmp_path: Path) -> None:
    runtime = _runtime_module()
    module_path = tmp_path / "dynamic_dataclass.py"
    module_path.write_text(
        "from __future__ import annotations\n"
        "from dataclasses import dataclass\n\n"
        "@dataclass(frozen=True)\n"
        "class Payload:\n"
        "    value: int\n",
        encoding="utf-8",
    )
    module_name = "portal_supply_chain_runtime_test_dataclass"
    sys.modules.pop(module_name, None)
    try:
        loaded = runtime._module(module_name, module_path)
        assert sys.modules[module_name] is loaded
        assert loaded.Payload(7).value == 7
    finally:
        sys.modules.pop(module_name, None)


def test_approved_deploy_installs_runtime_hooks_after_approved_images() -> None:
    source = Path("tools/agents/portal_supply_chain_runtime.py").read_text(encoding="utf-8")
    function = source.split("def deploy_approved(args: argparse.Namespace) -> int:", 1)[1]
    function = function.split("\ndef evaluate_files(", 1)[0]

    approved_images = function.index('"_build_images",')
    docker_host = function.index("docker_host_state.install(deploy)")
    liquidations = function.index("entrypoint._install_docker_host_liquidations_preflight(deploy)")
    market_root = function.index('market_evidence.__dict__["MARKET_EVIDENCE_HOST_ROOT"]')
    market_evidence = function.index("market_evidence.install(deploy)")
    copy_on_write = function.index("copy_on_write.install(deploy)")
    deploy_call = function.index("deploy.deploy(")

    assert approved_images < docker_host
    assert docker_host < liquidations < market_root < market_evidence < copy_on_write < deploy_call
    assert "entrypoint._resolve_market_evidence_host_root(deploy)" in function
    assert 'directory / "docker_host_state.py"' in function
    assert 'directory / "market_evidence_runtime.py"' in function
    assert 'directory / "postgresql_copy_on_write.py"' in function
