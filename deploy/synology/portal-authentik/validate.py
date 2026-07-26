#!/usr/bin/env python3
"""Fail-closed static validation for the PI-06 Authentik Synology package."""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

DIGEST_RE = re.compile(r"@sha256:[0-9a-f]{64}$")
AUTHENTIK_IMAGE_RE = re.compile(
    r"^docker\.io/authentik/server:2026\.5\.5@sha256:[0-9a-f]{64}$"
)
POSTGRES_IMAGE_RE = re.compile(
    r"^docker\.io/library/postgres:16\.13-alpine3\.23@sha256:[0-9a-f]{64}$"
)
PLACEHOLDER_MARKERS = ("REPLACE", "CHANGEME", "EXAMPLE", "<", ">")


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"{path}:{number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise ValueError(f"{path}:{number}: invalid environment key {key!r}")
        if key in values:
            raise ValueError(f"{path}:{number}: duplicate environment key {key}")
        values[key] = value.strip()
    return values


def has_placeholder(value: str) -> bool:
    upper = value.upper()
    return any(marker in upper for marker in PLACEHOLDER_MARKERS)


def decoded_key_is_long_enough(value: str) -> bool:
    try:
        return len(base64.b64decode(value, validate=True)) >= 32
    except (ValueError, TypeError):
        return False


def validate_environment(values: dict[str, str], *, example: bool) -> list[str]:
    errors: list[str] = []
    required = {
        "AUTHENTIK_IMAGE",
        "POSTGRES_IMAGE",
        "AUTHENTIK_POSTGRESQL__NAME",
        "AUTHENTIK_POSTGRESQL__USER",
        "AUTHENTIK_POSTGRESQL__PASSWORD",
        "AUTHENTIK_SECRET_KEY",
        "AUTHENTIK_BIND_ADDRESS",
        "AUTHENTIK_HTTP_PORT",
        "AUTHENTIK_BOOTSTRAP_PASSWORD_HASH",
    }
    for key in sorted(required - values.keys()):
        errors.append(f"missing required variable {key}")

    authentik_image = values.get("AUTHENTIK_IMAGE", "")
    postgres_image = values.get("POSTGRES_IMAGE", "")
    if not AUTHENTIK_IMAGE_RE.fullmatch(authentik_image):
        errors.append("AUTHENTIK_IMAGE must pin docker.io/authentik/server:2026.5.5 by full sha256 digest")
    if not POSTGRES_IMAGE_RE.fullmatch(postgres_image):
        errors.append(
            "POSTGRES_IMAGE must pin docker.io/library/postgres:16.13-alpine3.23 by full sha256 digest"
        )
    for key, value in (("AUTHENTIK_IMAGE", authentik_image), ("POSTGRES_IMAGE", postgres_image)):
        if value and not DIGEST_RE.search(value):
            errors.append(f"{key} is not digest pinned")

    if values.get("AUTHENTIK_BIND_ADDRESS") != "127.0.0.1":
        errors.append("AUTHENTIK_BIND_ADDRESS must remain 127.0.0.1")
    port = values.get("AUTHENTIK_HTTP_PORT", "")
    if not port.isdigit() or not (1024 <= int(port) <= 65535):
        errors.append("AUTHENTIK_HTTP_PORT must be a non-privileged TCP port")
    if values.get("AUTHENTIK_BOOTSTRAP_PASSWORD_HASH", ""):
        errors.append("AUTHENTIK_BOOTSTRAP_PASSWORD_HASH must be empty in the steady-state env file")

    if not example:
        password = values.get("AUTHENTIK_POSTGRESQL__PASSWORD", "")
        secret_key = values.get("AUTHENTIK_SECRET_KEY", "")
        if has_placeholder(password) or not (32 <= len(password) <= 99):
            errors.append("AUTHENTIK_POSTGRESQL__PASSWORD must be a non-placeholder 32-99 character value")
        if has_placeholder(secret_key) or len(secret_key) < 50:
            errors.append("AUTHENTIK_SECRET_KEY must be a non-placeholder value of at least 50 characters")
    return errors


def validate_compose(text: str) -> list[str]:
    errors: list[str] = []
    forbidden = {
        "unbounded latest tag": re.compile(r"image:\s*[^\n]+:latest(?:\s|$)"),
        "Docker socket mount": re.compile(r"docker\.sock"),
        "host network": re.compile(r"network_mode:\s*host"),
        "privileged container": re.compile(r"privileged:\s*true"),
        "timezone mount": re.compile(r"/(?:etc/)?(?:localtime|timezone)"),
        "Redis dependency": re.compile(r"(?m)^\s{2}redis:\s*$"),
        "public wildcard bind": re.compile(r"0\.0\.0\.0:\$\{AUTHENTIK_HTTP_PORT"),
    }
    for name, pattern in forbidden.items():
        if pattern.search(text):
            errors.append(f"compose contains forbidden {name}")

    required_snippets = [
        "  postgresql:\n",
        "  server:\n",
        "  worker:\n",
        "internal: true",
        "${AUTHENTIK_BIND_ADDRESS:-127.0.0.1}",
        "condition: service_healthy",
        "pg_isready",
        "- ak\n        - healthcheck",
        "no-new-privileges:true",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            errors.append(f"compose is missing required control: {snippet.strip()}")

    postgres_block = text.split("  postgresql:\n", 1)[-1].split("\n  server:\n", 1)[0]
    if "ports:" in postgres_block:
        errors.append("PostgreSQL must not publish a host port")
    if text.count("healthcheck:") < 3:
        errors.append("all three services require healthchecks")
    if text.count("restart: unless-stopped") < 3:
        errors.append("all three services require restart: unless-stopped")
    return errors


def validate_portal_identity_example(path: Path) -> list[str]:
    values = read_env(path)
    required = {
        "PORTAL_IDENTITY_ISSUER",
        "PORTAL_IDENTITY_CLIENT_ID",
        "PORTAL_IDENTITY_CLIENT_SECRET",
        "PORTAL_IDENTITY_REDIRECT_URI",
        "PORTAL_IDENTITY_SESSION_HMAC_KEY_B64",
        "PORTAL_IDENTITY_FLOW_ENCRYPTION_KEY_B64",
    }
    errors = [f"portal identity example is missing {key}" for key in sorted(required - values.keys())]
    if not values.get("PORTAL_IDENTITY_ISSUER", "").startswith("https://"):
        errors.append("PORTAL_IDENTITY_ISSUER must use HTTPS")
    if not values.get("PORTAL_IDENTITY_REDIRECT_URI", "").startswith("https://"):
        errors.append("PORTAL_IDENTITY_REDIRECT_URI must use HTTPS")
    return errors


def validate_scripts(root: Path) -> list[str]:
    errors: list[str] = []
    backup = (root / "backup.sh").read_text(encoding="utf-8")
    restore = (root / "restore.sh").read_text(encoding="utf-8")
    bootstrap = (root / "bootstrap.sh").read_text(encoding="utf-8")
    if "age -r" not in backup or ".dump.age" not in backup or ".tar.age" not in backup:
        errors.append("backup.sh must encrypt database and volume streams with age")
    if re.search(r">\s*[^\n]*\.sql(?:\s|$)", backup):
        errors.append("backup.sh must not write a plaintext SQL file")
    if "RESTORE_AUTHENTIK_DATABASE_AND_VOLUMES" not in restore:
        errors.append("restore.sh must require the destructive restore confirmation phrase")
    if "sha256sum -c" not in restore:
        errors.append("restore.sh must verify checksums before restore")
    if "AUTHENTIK_BOOTSTRAP_PASSWORD_HASH" not in bootstrap:
        errors.append("bootstrap.sh must use a one-shot password hash")
    if "--force-recreate server worker" not in bootstrap:
        errors.append("bootstrap.sh must recreate services without bootstrap material")
    return errors


def validate(root: Path, env_file: Path, *, example: bool) -> list[str]:
    errors: list[str] = []
    try:
        values = read_env(env_file)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    errors.extend(validate_environment(values, example=example))
    errors.extend(validate_compose((root / "compose.yml").read_text(encoding="utf-8")))
    errors.extend(validate_portal_identity_example(root / "portal-identity.env.example"))
    errors.extend(validate_scripts(root))
    contract = json.loads((root / "deployment-contract-v1.json").read_text(encoding="utf-8"))
    if contract.get("status") != "repository_validated_target_not_accepted":
        errors.append("deployment contract must not claim target acceptance")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--example", action="store_true")
    args = parser.parse_args()
    errors = validate(args.root.resolve(), args.env_file.resolve(), example=args.example)
    result = {
        "valid": not errors,
        "mode": "example" if args.example else "runtime",
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
