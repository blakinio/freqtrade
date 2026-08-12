from __future__ import annotations

import re
from pathlib import Path


_IMMUTABLE_IMAGE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/:@-]*@sha256:[0-9a-f]{64}$")
_LOCAL_TAG = re.compile(r"^[a-z0-9][a-z0-9._/-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*$")


def require_immutable_base_image(image: str) -> str:
    """Return an exact image reference or fail before invoking Docker."""

    if not _IMMUTABLE_IMAGE.fullmatch(image):
        raise ValueError("Portal runtime base image must be pinned by sha256 digest")
    return image


def require_local_target_tag(tag: str) -> str:
    if not _LOCAL_TAG.fullmatch(tag):
        raise ValueError("Portal runtime target must be a simple local Docker tag")
    return tag


def build_command(
    *,
    base_image: str,
    target_tag: str,
    repository_root: Path,
) -> tuple[str, ...]:
    dockerfile = repository_root / "ai_platform/portal/execution/runtime_image/Dockerfile"
    return (
        "docker",
        "build",
        "--pull=false",
        "--network=none",
        "--build-arg",
        f"FREQTRADE_BASE_IMAGE={require_immutable_base_image(base_image)}",
        "--file",
        str(dockerfile),
        "--tag",
        require_local_target_tag(target_tag),
        str(repository_root),
    )
