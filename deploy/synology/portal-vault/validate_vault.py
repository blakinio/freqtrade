#!/usr/bin/env python3
"""Fail-closed static validation for the PI-07 Vault Synology package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


VAULT_IMAGE_RE = re.compile(
    r"^docker\.io/hashicorp/vault:2\.0\.3@sha256:[0-9a-f]{64}$"
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


def validate_environment(values: dict[str, str], *, example: bool) -> list[str]:
    errors: list[str] = []
    required = {
        "VAULT_IMAGE",
        "VAULT_TLS_DIRECTORY",
        "VAULT_OPERATOR_DIRECTORY",
        "VAULT_APPROLE_OUTPUT_DIRECTORY",
    }
    for key in sorted(required - values.keys()):
        errors.append(f"missing required variable {key}")

    image = values.get("VAULT_IMAGE", "")
    if not VAULT_IMAGE_RE.fullmatch(image):
        errors.append(
            "VAULT_IMAGE must pin docker.io/hashicorp/vault:2.0.3 by a full sha256 digest"
        )

    for key in sorted(required - {"VAULT_IMAGE"}):
        value = values.get(key, "")
        if not value.startswith("/"):
            errors.append(f"{key} must be an absolute owner-managed host path")
        if any(marker in value.upper() for marker in PLACEHOLDER_MARKERS):
            errors.append(f"{key} must not contain a placeholder")
        if not example and value.startswith(str(Path.cwd())):
            errors.append(f"{key} must not live inside the repository checkout")
    return errors


def validate_compose(text: str) -> list[str]:
    errors: list[str] = []
    forbidden = {
        "host-published port": re.compile(r"(?m)^\s+ports:\s*$"),
        "Docker socket mount": re.compile(r"docker\.sock"),
        "host network": re.compile(r"network_mode:\s*host"),
        "privileged container": re.compile(r"privileged:\s*true"),
        "unbounded latest image": re.compile(r"image:\s*[^\n]+:latest(?:\s|$)"),
        "public ingress": re.compile(r"(?:cloudflare|tunnel|traefik|nginx)", re.IGNORECASE),
    }
    for name, pattern in forbidden.items():
        if pattern.search(text):
            errors.append(f"compose contains forbidden {name}")

    required = [
        "internal: true",
        "read_only: true",
        "cap_drop:\n      - ALL",
        "no-new-privileges:true",
        "./vault.hcl:/vault/config/vault.hcl:ro",
        "vault_data:/vault/data",
        "vault_audit_primary:/vault/audit-primary",
        "vault_audit_secondary:/vault/audit-secondary",
        "profiles:\n      - bootstrap",
        "profiles:\n      - rotate-approle",
        "VAULT_ADDR: https://vault:8200",
    ]
    for snippet in required:
        if snippet not in text:
            errors.append(f"compose is missing required control: {snippet.strip()}")
    if text.count("${VAULT_IMAGE:?") != 3:
        errors.append("all Vault services must use the same immutable VAULT_IMAGE")
    return errors


def validate_vault_config(text: str) -> list[str]:
    errors: list[str] = []
    required = [
        "disable_mlock = true",
        'default_lease_ttl = "10m"',
        'max_lease_ttl = "15m"',
        'storage "raft"',
        'path = "/vault/data"',
        'api_addr = "https://vault:8200"',
        'cluster_addr = "https://vault:8201"',
        'tls_cert_file = "/vault/tls/vault.crt"',
        'tls_key_file = "/vault/tls/vault.key"',
        'tls_client_ca_file = "/vault/tls/ca.crt"',
        'tls_min_version = "tls13"',
        'tls_max_version = "tls13"',
        'redact_addresses = "true"',
        'redact_cluster_name = "true"',
        'redact_version = "true"',
        "unauthenticated_metrics_access = false",
    ]
    for snippet in required:
        if snippet not in text:
            errors.append(f"vault.hcl is missing required control: {snippet}")
    if re.search(r"tls_disable\s*=\s*(?:1|true)", text):
        errors.append("Vault TLS must never be disabled")
    return errors


def validate_policy(text: str) -> list[str]:
    errors: list[str] = []
    if text.count('capabilities = ["read"]') != 3:
        errors.append("broker policy must contain exactly three read-only grants")
    for forbidden in ("create", "update", "delete", "sudo", "list", "patch"):
        if re.search(rf'capabilities\s*=\s*\[[^\]]*"{forbidden}"', text):
            errors.append(f"broker policy must not grant {forbidden}")
    required = (
        "portal-secrets/data/tenants/+/exchange-connections/+",
        "portal-secrets/metadata/tenants/+/exchange-connections/+",
        "auth/token/lookup-self",
    )
    for path in required:
        if path not in text:
            errors.append(f"broker policy is missing path {path}")
    return errors


def validate_scripts(root: Path) -> list[str]:
    errors: list[str] = []
    bootstrap = (root / "bootstrap.sh").read_text(encoding="utf-8")
    rotate = (root / "rotate-approle-secret-id.sh").read_text(encoding="utf-8")
    required_bootstrap = [
        "set -eu",
        "umask 077",
        "vault secrets enable -path=portal-secrets -version=2 kv",
        "cas_required=true",
        "vault auth enable approle",
        "token_ttl=10m",
        "token_max_ttl=15m",
        "secret_id_ttl=24h",
        "audit-primary",
        "audit-secondary",
        "chmod 600",
    ]
    for snippet in required_bootstrap:
        if snippet not in bootstrap:
            errors.append(f"bootstrap.sh is missing required control: {snippet}")
    if "echo $VAULT_TOKEN" in bootstrap or "set -x" in bootstrap:
        errors.append("bootstrap.sh must not print token material")
    for snippet in ("set -eu", "umask 077", "chmod 600", "secret-id.tmp"):
        if snippet not in rotate:
            errors.append(f"rotation script is missing required control: {snippet}")
    return errors


def validate(root: Path, env_file: Path, *, example: bool) -> list[str]:
    errors: list[str] = []
    try:
        values = read_env(env_file)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    errors.extend(validate_environment(values, example=example))
    errors.extend(validate_compose((root / "compose.yml").read_text(encoding="utf-8")))
    errors.extend(validate_vault_config((root / "vault.hcl").read_text(encoding="utf-8")))
    errors.extend(validate_policy((root / "broker-policy.hcl").read_text(encoding="utf-8")))
    errors.extend(validate_scripts(root))
    contract = json.loads((root / "deployment-contract-v1.json").read_text(encoding="utf-8"))
    if contract.get("status") != "repository_validated_target_not_accepted":
        errors.append("deployment contract must not claim target acceptance")
    if contract.get("execution_mode") != "dry_run":
        errors.append("deployment contract must remain dry_run")
    if contract.get("withdrawals_enabled") is not False:
        errors.append("deployment contract must keep withdrawals disabled")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--example", action="store_true")
    args = parser.parse_args()
    errors = validate(args.root.resolve(), args.env_file.resolve(), example=args.example)
    print(
        json.dumps(
            {
                "valid": not errors,
                "mode": "example" if args.example else "runtime",
                "errors": errors,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
