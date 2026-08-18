#!/usr/bin/env python3
"""Validate the static ADR-024 dedicated Linux runtime host contract."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath


REQUIRED_KEYS = {
    "RUNTIME_HOST_ROLE",
    "RUNTIME_CONTAINER_ENGINE",
    "RUNTIME_STATE_ROOT",
    "DURABLE_STORAGE_PROVIDER",
    "DURABLE_STORAGE_ROOT",
    "GITHUB_RUNNER_SCOPE",
    "ALLOW_APPLICATION_CONTAINER_ENGINE_SOCKET",
}


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"line {number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in values:
            raise ValueError(f"line {number}: invalid or duplicate key {key!r}")
        values[key] = value
    return values


def validate_scalar_contract(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    expected_values = {
        "RUNTIME_HOST_ROLE": {"dedicated-linux"},
        "RUNTIME_CONTAINER_ENGINE": {"docker", "podman"},
        "DURABLE_STORAGE_PROVIDER": {"synology", "local"},
        "GITHUB_RUNNER_SCOPE": {"disabled", "deploy-only"},
        "ALLOW_APPLICATION_CONTAINER_ENGINE_SOCKET": {"false"},
    }
    for key, allowed in expected_values.items():
        if values.get(key) not in allowed:
            errors.append(f"{key} must be one of: {', '.join(sorted(allowed))}")
    return errors


def validate_path(name: str, raw_path: str) -> tuple[PurePosixPath | None, list[str]]:
    errors: list[str] = []
    if not raw_path or not PurePosixPath(raw_path).is_absolute():
        return None, [f"{name} must be an absolute POSIX path"]

    path = PurePosixPath(raw_path)
    normalized = str(path)
    if normalized == "/" or normalized == "/volume1" or normalized.startswith("/volume1/"):
        errors.append(f"{name} must not use root or a Synology-specific /volume1 path")
    return path, errors


def validate_path_contract(values: dict[str, str]) -> list[str]:
    state, state_errors = validate_path("RUNTIME_STATE_ROOT", values.get("RUNTIME_STATE_ROOT", ""))
    storage, storage_errors = validate_path(
        "DURABLE_STORAGE_ROOT", values.get("DURABLE_STORAGE_ROOT", "")
    )
    errors = [*state_errors, *storage_errors]
    if state is None or storage is None:
        return errors
    if state == storage:
        errors.append("runtime state and durable storage roots must be distinct")
    elif state in storage.parents or storage in state.parents:
        errors.append("runtime state and durable storage roots must not be nested")
    return errors


def validate_contract(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_KEYS - values.keys())
    if missing:
        errors.append(f"missing required keys: {', '.join(missing)}")
    errors.extend(validate_scalar_contract(values))
    errors.extend(validate_path_contract(values))
    return errors


def validate_filesystem(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for name in ("RUNTIME_STATE_ROOT", "DURABLE_STORAGE_ROOT"):
        path = Path(values[name])
        if not path.is_dir():
            errors.append(f"{name} does not exist as a directory: {path}")
            continue
        if not os.access(path, os.R_OK | os.X_OK):
            errors.append(f"{name} is not readable/traversable: {path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--check-filesystem", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        values = parse_env_file(args.env_file)
        errors = validate_contract(values)
        if args.check_filesystem and not errors:
            errors.extend(validate_filesystem(values))
    except (OSError, ValueError) as exc:
        errors = [str(exc)]

    result = {
        "contract": "adr-024-dedicated-linux-runtime-host-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print("ADR-024 dedicated Linux runtime host contract: PASS")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
