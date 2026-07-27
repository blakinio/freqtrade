from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / ".github" / "workflows" / "freqtrade-synology-runner-dedicated-cutover-retry.yml"


def test_retry_uses_exact_proven_image_and_trusted_runner() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "sha-0e2a6428a7ca29e7c2fdc4ac34be85bb5f5ac0c0" in text
    assert "if: github.ref == 'refs/heads/develop'" in text
    assert "runs-on: [freqtrade-staging]" in text
    assert "cancel-in-progress: false" in text


def test_retry_stages_helper_through_root_host_bind() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "cutover-helper-host-bind.sh" in text
    assert "docker run --rm --interactive" in text
    assert "docker run --detach --rm" in text
    assert text.count("--user 0:0") >= 2
    assert text.count('--volume "$host_root:$host_root"') >= 2
    assert "cat > '$helper_path.tmp'" in text
    assert 'test "$(id -u)" = "0"' in text
    assert "Host-bind detached helper launched." in text
    assert "dedicated_runner_recreated_by_host_bind_helper" in text


def test_retry_does_not_assume_host_root_is_mounted_in_runner() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    launch_prefix = text.split("docker run --rm --interactive", maxsplit=1)[0]
    assert 'test -d "$host_root/state"' not in launch_prefix
    assert 'mkdir -p "$compose_dir"' not in launch_prefix
    assert 'cat > "$compose_path.tmp"' not in launch_prefix


def test_retry_preserves_registration_and_freqtrade_ownership() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "external: true" in text
    assert "RUNNER_CONFIG_VOLUME" in text
    assert "RUNNER_WORK_VOLUME" in text
    assert "/volume1/docker/freqtrade/state:/var/lib/freqtrade-staging-state" in text
    assert "name: freqtrade-deploy-runner" in text
    assert "container_name: freqtrade-synology-staging-runner" in text
    assert "oteryn" not in text.casefold()


def test_retry_is_observable_and_does_not_delete_volumes() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    lowered = text.casefold()

    assert "synology/freqtrade-runner-cutover" in text
    assert "verify-live-cutover" in text
    assert "cutover-watchdog" in text
    assert "docker volume rm" not in lowered
    assert "docker system prune" not in lowered
    assert "docker network prune" not in lowered
