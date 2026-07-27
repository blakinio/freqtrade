from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = (
    ROOT / ".github" / "workflows" / "freqtrade-synology-runner-state-path-cutover.yml"
)


def test_cutover_translates_runner_state_to_host_state() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert 'runner_state_root="/var/lib/freqtrade-staging-state"' in text
    assert 'host_state_root="/volume1/docker/freqtrade/state"' in text
    assert 'runner_runtime_dir="$runner_state_root/$runtime_rel"' in text
    assert 'host_runtime_dir="$host_state_root/$runtime_rel"' in text
    assert '--volume "$host_state_root:$host_state_root"' in text
    assert '"$helper_host_path"' in text
    assert "/volume1/docker/freqtrade/runner" not in text


def test_cutover_preserves_exact_image_registration_and_state() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "sha-0e2a6428a7ca29e7c2fdc4ac34be85bb5f5ac0c0" in text
    assert "freqtrade-deploy-runner" in text
    assert "freqtrade-synology-staging-runner" in text
    assert "RUNNER_CONFIG_VOLUME" in text
    assert "RUNNER_WORK_VOLUME" in text
    assert "/volume1/docker/freqtrade/state:/var/lib/freqtrade-staging-state" in text
    assert "external: true" in text
    assert "oteryn" not in text.casefold()


def test_cutover_has_bounded_rollback_and_observability() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    lowered = text.casefold()

    assert "rollback-compose.yml" in text
    assert "PREVIOUS_IMAGE_ID" in text
    assert "target_failed_previous_runner_restored" in text
    assert "replacement_verification_timed_out_previous_runner_restored" in text
    assert "synology/freqtrade-runner-cutover" in text
    assert "cutover-watchdog" in text
    assert "docker volume rm" not in lowered
    assert "docker system prune" not in lowered
    assert "docker network prune" not in lowered


def test_cutover_mutates_only_from_trusted_develop() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "push:" in text
    assert "- develop" in text
    assert "pull_request:" not in text
    assert "if: github.ref == 'refs/heads/develop'" in text
    assert "runs-on: [freqtrade-staging]" in text
    assert "--user 0:0" in text
