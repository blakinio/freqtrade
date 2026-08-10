from pathlib import Path

import pytest

from ai_platform.portal.execution.runtime_image.build import (
    build_command,
    require_immutable_base_image,
)


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


def test_runtime_image_dockerfile_removes_sudo_path_and_returns_to_ftuser() -> None:
    dockerfile = (
        Path("ai_platform/portal/execution/runtime_image/Dockerfile")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    joined = "\n".join(dockerfile)

    assert "ARG FREQTRADE_BASE_IMAGE" in joined
    assert "FROM ${FREQTRADE_BASE_IMAGE}" in joined
    assert "gpasswd -d ftuser sudo" in joined
    assert "/usr/bin/sudo" in joined
    assert "NOPASSWD" in joined
    assert dockerfile[-3:] == ["USER ftuser", 'ENTRYPOINT ["freqtrade"]', 'CMD ["trade"]']
