from __future__ import annotations

import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT_ROOT = REPOSITORY_ROOT / "deploy" / "synology" / "liquid20"
WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "liquidations-live-synology.yml"


def test_live_entrypoint_and_deploy_script_have_valid_shell_syntax() -> None:
    for path in (DEPLOYMENT_ROOT / "live-entrypoint.sh", DEPLOYMENT_ROOT / "deploy-live.sh"):
        subprocess.run(
            ["bash" if path.name == "deploy-live.sh" else "sh", "-n", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )


def test_compose_separates_restartable_live_service_from_evidence_profile() -> None:
    compose = (DEPLOYMENT_ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert "liquid20-live:" in compose
    assert "restart: always" in compose
    assert 'entrypoint: ["/usr/local/bin/liquid20-live-entrypoint"]' in compose
    assert "liquid20-evidence:" in compose
    assert 'profiles: ["evidence"]' in compose
    assert 'restart: "no"' in compose
    assert 'entrypoint: ["/usr/local/bin/liquid20-entrypoint"]' in compose
    assert "./data:/data:rw" in compose
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "pids_limit:" not in compose
    assert "mem_limit: 512m" in compose
    assert "cpus:" not in compose
    assert "ports:" not in compose
    assert "/var/run/docker.sock" not in compose


def test_live_entrypoint_refuses_credentials_and_stays_data_only() -> None:
    entrypoint = (DEPLOYMENT_ROOT / "live-entrypoint.sh").read_text(encoding="utf-8")
    assert "ai_platform.scripts.liquidation_live_stream" in entrypoint
    assert "LIQUID20_DATA_ROOT" in entrypoint
    assert "--maximum-symbols" in entrypoint
    for variable in (
        "BYBIT_API_KEY",
        "BYBIT_API_SECRET",
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "OKX_API_KEY",
        "OKX_API_SECRET",
        "FREQTRADE__EXCHANGE__KEY",
        "FREQTRADE__EXCHANGE__SECRET",
    ):
        assert variable in entrypoint
    assert "freqtrade trade" not in entrypoint
    assert "order" not in entrypoint.lower()


def test_controlled_deployment_is_exact_sha_candidate_first_and_rollback_capable() -> None:
    script = (DEPLOYMENT_ROOT / "deploy-live.sh").read_text(encoding="utf-8")
    assert 'commit_sha="${GITHUB_SHA:?' in script
    assert 'image="${image_name}:sha-${commit_sha}"' in script
    assert "candidate_first" in script
    assert "production_first" in script
    assert "Restoring previous live collector image" in script
    assert "previous_commit" in script
    assert "COLLECTOR_COMMIT=${selected_commit}" in script
    assert "history_before" in script
    assert 'test "$history_before" = "$history_after"' in script
    assert '--restart "$restart_policy"' in script
    assert '--user "${puid}:${pgid}"' in script
    assert '--mount "type=bind,src=/var/run/docker.sock' not in script
    assert "chmod -R" not in script
    assert "chown -R" not in script
    assert "refs/heads/develop" in script


def test_deployment_resolves_non_root_uid_and_existing_data_group() -> None:
    script = (DEPLOYMENT_ROOT / "deploy-live.sh").read_text(encoding="utf-8")
    defaults = (DEPLOYMENT_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "PUID=1026" in defaults
    assert 'puid="${LIQUID20_PUID:-$(read_default PUID)}"' in script
    assert '[[ "$1" -gt 0 ]]' in script
    assert 'pgid="$data_gid"' in script
    assert "LIQUID20_PGID must match the existing data-root group" in script
    assert 'test "$running_uid" != "0"' in script
    assert 'test "$running_gid" = "$pgid"' in script


def test_deployment_maps_runner_state_to_docker_host_candidate_root() -> None:
    script = (DEPLOYMENT_ROOT / "deploy-live.sh").read_text(encoding="utf-8")

    assert "/var/lib/freqtrade-staging-state/liquidations-live-candidates/" in script
    assert "/volume1/docker/freqtrade/state/liquidations-live-candidates/" in script
    assert 'install -d -m 0750 -o "$puid" -g "$pgid" "$candidate_runner_root"' in script
    assert 'start_container "$candidate" "$image" "$candidate_host_root"' in script
    assert 'wait_for_state "$candidate"' in script
    assert 'state_observation "$selected_container"' in script
    assert 'wait_for_heartbeat_advance "$candidate" "$candidate_first"' in script
    assert "for _ in $(seq 1 15)" in script
    assert "Collector heartbeat did not advance within 30 seconds" in script
    assert "sleep 6" not in script
    assert 'docker exec --interactive "$selected_container" python' in script


def test_live_bootstrap_is_bounded_to_sibling_live_root() -> None:
    script = (DEPLOYMENT_ROOT / "deploy-live.sh").read_text(encoding="utf-8")

    assert "bootstrap_live_root" in script
    assert 'accepted = root / "runs"' in script
    assert 'live = root / "live"' in script
    assert 'live_runs = live / "runs"' in script
    assert "os.chown(path, uid, gid)" in script
    assert "os.chmod(path, 0o750)" in script
    assert '--mount "type=bind,src=${data_root},dst=/data,readonly"' in script
    assert '--mount "type=bind,src=${data_root},dst=/data"' in script


def test_cpu_quota_probe_is_strict_and_preserves_other_limits() -> None:
    script = (DEPLOYMENT_ROOT / "deploy-live.sh").read_text(encoding="utf-8")

    assert "configure_cpu_limit" in script
    assert 'docker run --rm --cpus 0.1 --entrypoint /bin/true "$image"' in script
    assert "NanoCPUs can not be set" in script
    assert "kernel does not support CPU CFS scheduler" in script
    assert "cgroup is not mounted" in script
    assert "capability probe failed for an unexpected reason" in script
    assert "cpu_limit_args=(--cpus 1.0)" in script
    assert 'run_args+=("${cpu_limit_args[@]}")' in script
    assert "configure_pids_limit" in script
    assert "PIDs limit discarded" in script
    assert "pids_limit_args=(--pids-limit 128)" in script
    assert 'run_args+=("${pids_limit_args[@]}")' in script
    assert "--memory 512m" in script
    assert 'test "$running_nano_cpus" = "1000000000"' in script
    assert 'test "$running_nano_cpus" = "0"' in script
    assert '"cpu_quota_supported": cpu_quota_supported' in script
    assert '"memory_limit_bytes": memory_limit' in script
    assert 'test "$running_memory_limit" = "536870912"' in script
    assert '"pids_limit_supported": pids_limit_supported' in script
    assert '"pids_limit": pids_limit' in script


def test_synology_workflow_mutates_production_only_from_develop() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "push:" in workflow
    assert "- develop" in workflow
    assert "pull_request:" not in workflow
    assert "persist-credentials: false" in workflow
    assert "deploy/synology/liquid20/deploy-live.sh" in workflow
    assert "liquidations-live-synology-report.json" in workflow
    assert "liquidations-live-synology.log" in workflow
    assert 'context":"liquidations-live-synology"' in workflow
    assert "workflow_dispatch:" in workflow


def test_synology_workflow_deploys_only_for_runtime_paths() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    runtime_paths = (
        "deploy/synology/liquid20/.env.example",
        "deploy/synology/liquid20/Dockerfile",
        "deploy/synology/liquid20/compose.yaml",
        "deploy/synology/liquid20/deploy-live.sh",
        "deploy/synology/liquid20/live-entrypoint.sh",
    )

    assert "deploy/synology/liquid20/**" not in workflow
    for path in runtime_paths:
        assert f"- {path}" in workflow
    assert "- deploy/synology/liquid20/LIVE_STREAM.md" not in workflow


def test_deployment_uses_validated_full_public_universe_bound() -> None:
    script = (DEPLOYMENT_ROOT / "deploy-live.sh").read_text(encoding="utf-8")
    entrypoint = (DEPLOYMENT_ROOT / "live-entrypoint.sh").read_text(encoding="utf-8")
    compose = (DEPLOYMENT_ROOT / "compose.yaml").read_text(encoding="utf-8")
    defaults = (DEPLOYMENT_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "MAXIMUM_SYMBOLS=1000" in defaults
    assert "LIQUID20_MAXIMUM_SYMBOLS:-1000" in entrypoint
    assert "MAXIMUM_SYMBOLS:-1000" in compose
    assert (
        'maximum_symbols="${LIQUID20_MAXIMUM_SYMBOLS:-$(read_default MAXIMUM_SYMBOLS)}"' in script
    )
    assert "LIQUID20_MAXIMUM_SYMBOLS=${maximum_symbols}" in script
    assert 'item.get("connected") is not True' in script
