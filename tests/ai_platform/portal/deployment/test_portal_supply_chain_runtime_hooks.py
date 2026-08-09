from __future__ import annotations

from pathlib import Path


def test_approved_deploy_installs_runtime_hooks_after_approved_images() -> None:
    source = Path("tools/agents/portal_supply_chain_runtime.py").read_text(encoding="utf-8")
    function = source.split("def deploy_approved(args: argparse.Namespace) -> int:", 1)[1]
    function = function.split("\ndef evaluate_files(", 1)[0]

    approved_images = function.index('"_build_images",')
    docker_host = function.index("docker_host_state.install(deploy)")
    liquidations = function.index("entrypoint._install_docker_host_liquidations_preflight(deploy)")
    market_evidence = function.index("market_evidence.install(deploy)")
    copy_on_write = function.index("copy_on_write.install(deploy)")
    deploy_call = function.index("deploy.deploy(")

    assert approved_images < docker_host
    assert docker_host < liquidations < market_evidence < copy_on_write < deploy_call
    assert 'directory / "docker_host_state.py"' in function
    assert 'directory / "market_evidence_runtime.py"' in function
    assert 'directory / "postgresql_copy_on_write.py"' in function
