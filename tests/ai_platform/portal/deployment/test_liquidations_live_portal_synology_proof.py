from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / ".github" / "workflows" / "liquidations-live-portal-synology-proof.yml"
SCRIPT = ROOT / "deploy" / "synology" / "portal" / "prove-liquidations-live.sh"


def test_workflow_is_exact_develop_only_and_uploads_evidence() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "push:" in text
    assert "- develop" in text
    assert "runs-on: freqtrade-staging" in text
    assert "environment: synology-staging" in text
    assert "persist-credentials: false" in text
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" in text
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in text
    assert "liquidations-live-portal-synology-proof" in text


def test_script_preserves_production_and_mount_boundaries() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    lowered = text.casefold()

    assert 'portal_container="${PORTAL_CONTAINER_NAME:-freqtrade-portal-staging}"' in text
    assert 'test "$mount_rw" = "false"' in text
    assert 'test -z "$docker_socket_mount"' in text
    assert 'test "$portal_uid" != "0"' in text
    expected_mount = (
        '--mount "type=bind,src=${liquidations_host_root},'
        'dst=${liquidations_container_root},readonly"'
    )
    assert expected_mount in text
    assert "--read-only" in text
    assert "--cap-drop ALL" in text
    assert "--security-opt no-new-privileges:true" in text
    assert "--restart no" in text
    assert 'docker rm -f "$portal_container"' not in text
    assert 'docker stop "$portal_container"' not in text
    assert 'docker restart "$portal_container"' not in text
    assert "docker system prune" not in lowered
    assert "docker volume rm" not in lowered


def test_script_uses_explicit_fixture_identity_only_in_isolated_candidate() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert "--env PORTAL_ENVIRONMENT=test" in text
    assert "--env PORTAL_IDENTITY_FIXTURE_MODE=enabled" in text
    assert "--env PORTAL_WEB_DATA_MODE=fixture" in text
    assert 'candidate="${PORTAL_LIVE_PROOF_CANDIDATE:-freqtrade-portal-live-proof-' in text
    assert 'fixture_identity": True' in text
    assert "SESSION_MISSING" in text
    assert "production_boundary" in text


def test_script_requires_truthful_live_health_and_timestamps() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert 'health.contract !== "portal-liquidations-health-v2"' in text
    assert 'health.mode !== "live" || health.run_state !== "active"' in text
    assert "collector_heartbeat_at_ms" in text
    assert "portal_checked_at_ms" in text
    assert "Ostatnie zdarzenie" in text
    assert "Ostatni heartbeat collectora" in text
    assert "Ostatnie sprawdzenie przez portal" in text
    assert "collector heartbeat did not advance" in text
    assert "portal read timestamp did not advance" in text
    assert "real_exchange_event_observed" in text
    assert "without fabricating an event" in text
    assert '"trading_authorized": False' in text


def test_script_checks_sources_no_store_and_same_process() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert '["bybit-linear", "binance-usdm"]' in text
    assert "subscription_symbol_count" in text
    assert "last_heartbeat_at_ms" in text
    assert 'cacheControl.includes("no-store")' in text
    assert '"same_portal_process": True' in text
    assert '"no_store_api": True' in text


def test_script_probes_synology_pid_limit_and_records_runtime_setting() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert "configure_pids_limit" in text
    assert "PIDs limit discarded" in text
    assert "pids cgroup is not mounted" in text
    assert "pids_limit_args=(--pids-limit 256)" in text
    assert 'run_args+=("${pids_limit_args[@]}")' in text
    assert 'candidate_pids_limit_json="$(docker inspect' in text
    assert "{{json .HostConfig.PidsLimit}}" in text
    assert 'test "$candidate_pids_limit_json" = "256"' in text
    assert "null | 0)" in text
    assert 'CANDIDATE_PIDS_LIMIT_JSON="$candidate_pids_limit_json"' in text
    assert '"pids_limit_supported":' in text
    assert '"pids_limit": json.loads(' in text
