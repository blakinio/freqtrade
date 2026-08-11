from pathlib import Path

import pytest

from ai_platform.portal.execution.runtime_image.build import (
    build_command,
    require_immutable_base_image,
)


RUNTIME_IMAGE_ROOT = Path("ai_platform/portal/execution/runtime_image")


def test_runtime_image_build_requires_digest_pinned_base() -> None:
    with pytest.raises(ValueError, match="sha256"):
        require_immutable_base_image("freqtradeorg/freqtrade:stable")

    pinned = f"freqtradeorg/freqtrade@sha256:{'a' * 64}"
    assert require_immutable_base_image(pinned) == pinned


def test_runtime_image_build_is_offline_and_does_not_pull(tmp_path: Path) -> None:
    pinned = f"freqtradeorg/freqtrade@sha256:{'a' * 64}"

    command = build_command(
        base_image=pinned,
        target_tag="portal/freqtrade-runtime:test",
        repository_root=tmp_path,
    )

    assert "--pull=false" in command
    assert "--network=none" in command
    assert f"FREQTRADE_BASE_IMAGE={pinned}" in command


def test_runtime_image_dockerfile_binds_fixed_quarantine_and_returns_to_ftuser() -> None:
    dockerfile = (RUNTIME_IMAGE_ROOT / "Dockerfile").read_text(encoding="utf-8").splitlines()
    joined = "\n".join(dockerfile)

    assert "ARG FREQTRADE_BASE_IMAGE" in joined
    assert "FROM ${FREQTRADE_BASE_IMAGE}" in joined
    assert "gpasswd -d ftuser sudo" in joined
    assert "/usr/bin/sudo" in joined
    assert "NOPASSWD" in joined
    assert (
        "COPY ai_platform/portal/execution/runtime_image/portal-runtime-quarantine "
        "/usr/local/bin/portal-runtime-quarantine"
    ) in joined
    assert "chmod 0555 /usr/local/bin/portal-runtime-quarantine" in joined
    assert "chown root:root /usr/local/bin/portal-runtime-quarantine" in joined
    assert dockerfile[-3:] == [
        "USER ftuser",
        'ENTRYPOINT ["/usr/local/bin/portal-runtime-quarantine"]',
        'CMD ["freqtrade", "trade"]',
    ]


def test_runtime_quarantine_is_fixed_fail_closed_bootstrap() -> None:
    script = (RUNTIME_IMAGE_ROOT / "portal-runtime-quarantine").read_text(encoding="utf-8")

    assert "PORTAL_LOG_PROBE_BYTES is required" in script
    assert "PORTAL_LOG_BOUND_PROBE_BEGIN" in script
    assert "PORTAL_LOG_BOUND_PROBE_END" in script
    assert ': > "$log_probe_ready"' in script
    assert 'while [ ! -f "$release_file" ]' in script
    assert 'application_ready="$release_dir/application-ready"' in script
    assert '"$@" &' in script
    assert ': > "$application_ready"' in script
    assert 'wait "$child_pid"' in script
    assert "curl " not in script
    assert "wget " not in script
