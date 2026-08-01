from __future__ import annotations

import stat
from pathlib import Path, PurePosixPath, PureWindowsPath


class MarketEvidencePathError(ValueError):
    """Raised when an immutable package member is not a safe regular file."""


def safe_regular_member(root: Path, logical_name: str) -> Path:
    """Validate a POSIX logical member without following any member symlink."""

    posix = PurePosixPath(logical_name)
    windows = PureWindowsPath(logical_name)
    parts = logical_name.split("/")
    if (
        not logical_name
        or "\x00" in logical_name
        or "\\" in logical_name
        or posix.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise MarketEvidencePathError("artifact path must be a non-empty relative POSIX path")

    try:
        root_metadata = root.lstat()
    except OSError as exc:
        raise MarketEvidencePathError("artifact root must be a regular directory") from exc
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
        raise MarketEvidencePathError("artifact root must be a regular directory")
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        raise MarketEvidencePathError("artifact root must be a regular directory") from exc

    candidate = root
    candidate_metadata = None
    for part in parts:
        candidate = candidate / part
        try:
            candidate_metadata = candidate.lstat()
        except OSError as exc:
            raise MarketEvidencePathError("artifact member is missing") from exc
        if stat.S_ISLNK(candidate_metadata.st_mode):
            raise MarketEvidencePathError("artifact path traverses a symlink")

    try:
        candidate.resolve(strict=True).relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise MarketEvidencePathError("artifact path escapes its immutable root") from exc
    if candidate_metadata is None or not stat.S_ISREG(candidate_metadata.st_mode):
        raise MarketEvidencePathError("artifact member is not a regular file")
    return candidate
