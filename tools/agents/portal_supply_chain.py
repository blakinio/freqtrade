#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import portal_supply_chain_runtime as _runtime  # noqa: E402
from portal_supply_chain_policy import (  # noqa: E402,F401
    PolicyError,
    evaluate_licenses,
    evaluate_vulnerabilities,
    scan_evidence,
    validate_policy,
)


_original_provenance = _runtime._provenance
_original_build_verify = _runtime.build_verify
_original_verify_approval = _runtime.verify_approval
_original_deploy_approved = _runtime.deploy_approved
_HEX_DIGEST = re.compile(r"[0-9a-f]{64}")
_GRYPE_FROZEN_ENVIRONMENT = {
    "GRYPE_DB_AUTO_UPDATE": "false",
    "GRYPE_DB_REQUIRE_UPDATE_CHECK": "false",
    "GRYPE_DB_VALIDATE_BY_HASH_ON_START": "true",
    "GRYPE_DB_VALIDATE_AGE": "true",
    "GRYPE_DB_MAX_ALLOWED_BUILT_AGE": "120h",
}


def _statement_provenance(**kwargs):
    payload = _original_provenance(**kwargs)
    if payload.get("_type") == "https://in-toto.io/Statement/v1":
        return payload
    image = kwargs["image"]
    name = kwargs["name"]
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {
                "name": f"freqtrade-portal-{name}",
                "digest": {"sha256": image.removeprefix("sha256:")},
            }
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": payload,
    }


_runtime._provenance = _statement_provenance

DEFAULT_POLICY = _runtime.DEFAULT_POLICY
_annotate_deployment_report = _runtime._annotate_deployment_report
_approved_image_tuple = _runtime._approved_image_tuple
_base_digests = _runtime._base_digests
evaluate_files = _runtime.evaluate_files


def _database_content_digest(path: Path) -> str:
    root = path.resolve()
    if not root.exists():
        raise PolicyError("Grype database path does not exist")
    digest = hashlib.sha256()
    if root.is_file():
        files = [root]
        relative_root = root.parent
    elif root.is_dir():
        files = sorted(candidate for candidate in root.rglob("*") if candidate.is_file())
        relative_root = root
    else:
        raise PolicyError("Grype database path is not a file or directory")
    if not files:
        raise PolicyError("Grype database path contains no files")
    for file_path in files:
        if file_path.is_symlink():
            raise PolicyError("Grype database evidence cannot contain symlinks")
        relative = file_path.relative_to(relative_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        file_digest = hashlib.sha256(file_path.read_bytes()).digest()
        digest.update(file_digest)
    return digest.hexdigest()


def _normalize_database_status(raw: dict[str, Any]) -> dict[str, Any]:
    schema_version = raw.get("schemaVersion")
    built = raw.get("built")
    source = raw.get("from")
    valid = raw.get("valid")
    database_path = raw.get("path")
    if not isinstance(schema_version, str) or not schema_version.strip():
        raise PolicyError("Grype database schema version is missing")
    if not isinstance(built, str) or not built.strip():
        raise PolicyError("Grype database build timestamp is missing")
    if source is not None and not isinstance(source, str):
        raise PolicyError("Grype database source is invalid")
    if valid is not True:
        raise PolicyError("Grype database status is not valid")
    if not isinstance(database_path, str) or not database_path.strip():
        raise PolicyError("Grype database path is missing")
    return {
        "schema_version": schema_version,
        "built": built,
        "source": source or "unknown",
        "valid": True,
        "content_sha256": _database_content_digest(Path(database_path)),
    }


def _capture_scanner_database(
    output_dir: Path,
) -> tuple[Path, dict[str, Any], Path]:
    _runtime._run(["grype", "db", "update"])
    raw = json.loads(_runtime._run(["grype", "db", "status", "-o", "json"]).stdout)
    if not isinstance(raw, dict):
        raise PolicyError("Grype database status must be a JSON object")
    database_value = raw.get("path")
    if not isinstance(database_value, str) or not database_value.strip():
        raise PolicyError("Grype database path is missing")
    database_path = Path(database_value).resolve()
    normalized = _normalize_database_status(raw)
    evidence_path = output_dir / "grype-database.json"
    _runtime._save(evidence_path, normalized)
    return evidence_path, normalized, database_path


def _augment_provenance(path: Path, scanner_database: dict[str, Any]) -> None:
    statement = _runtime._load(path)
    predicate = statement.get("predicate")
    if not isinstance(predicate, dict):
        raise PolicyError("provenance statement has no predicate")
    build_definition = predicate.get("buildDefinition")
    run_details = predicate.get("runDetails")
    if not isinstance(build_definition, dict) or not isinstance(run_details, dict):
        raise PolicyError("provenance predicate is incomplete")
    dependencies = build_definition.get("resolvedDependencies")
    if not isinstance(dependencies, list):
        raise PolicyError("provenance resolvedDependencies must be a list")
    dependencies.append(
        {
            "uri": (f"grype-db:{scanner_database['schema_version']}:{scanner_database['built']}"),
            "digest": {"sha256": scanner_database["content_sha256"]},
        }
    )
    byproducts = run_details.get("byproducts")
    if not isinstance(byproducts, list):
        raise PolicyError("provenance byproducts must be a list")
    byproducts.append(
        {
            "name": "grype-database",
            "annotations": {
                "schema_version": scanner_database["schema_version"],
                "built": scanner_database["built"],
                "source": scanner_database["source"],
                "content_sha256": scanner_database["content_sha256"],
                "auto_update_during_scan": False,
                "validated_by_hash": True,
                "maximum_built_age": "120h",
            },
        }
    )
    _runtime._save(path, statement)


def _apply_frozen_grype_environment() -> dict[str, str | None]:
    previous = {key: os.environ.get(key) for key in _GRYPE_FROZEN_ENVIRONMENT}
    os.environ.update(_GRYPE_FROZEN_ENVIRONMENT)
    return previous


def _restore_environment(previous: dict[str, str | None]) -> None:
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _blocked_policy_summary(output_dir: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    report_suffixes = {
        "vulnerabilities": ".vulnerability-policy.json",
        "licenses": ".licenses.json",
    }
    for image_name in ("control-plane", "web"):
        image_summary: dict[str, Any] = {}
        for report_name, suffix in report_suffixes.items():
            path = output_dir / f"{image_name}{suffix}"
            if not path.is_file() or path.is_symlink():
                continue
            payload = _runtime._load(path)
            blocked = payload.get("blocked")
            if isinstance(blocked, list) and blocked:
                image_summary[report_name] = blocked[:20]
        if image_summary:
            summary[image_name] = image_summary
    return summary


def build_verify(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    database_evidence, scanner_database, database_path = _capture_scanner_database(output_dir)
    previous_environment = _apply_frozen_grype_environment()
    try:
        try:
            result = int(_original_build_verify(args))
        except PolicyError as exc:
            blocked = _blocked_policy_summary(output_dir)
            if blocked:
                raise PolicyError(
                    f"{exc}; blocked_findings={json.dumps(blocked, sort_keys=True)}"
                ) from exc
            raise
    finally:
        _restore_environment(previous_environment)
    if result != 0:
        return result
    if _database_content_digest(database_path) != scanner_database["content_sha256"]:
        raise PolicyError("Grype database changed after it was bound to the scan")
    approval_path = Path(args.approval).resolve()
    approval = _runtime._load(approval_path)
    images = approval.get("images")
    if not isinstance(images, dict):
        raise PolicyError("approval image map is missing")
    for name, details in images.items():
        if not isinstance(details, dict):
            raise PolicyError(f"invalid approval image detail: {name}")
        evidence = details.get("evidence")
        if not isinstance(evidence, dict):
            raise PolicyError(f"missing approval evidence: {name}")
        provenance_entry = evidence.get("provenance")
        if not isinstance(provenance_entry, dict):
            raise PolicyError(f"missing provenance approval entry: {name}")
        provenance_path = approval_path.parent / str(provenance_entry.get("path", ""))
        _augment_provenance(provenance_path, scanner_database)
        provenance_entry["sha256"] = _runtime._digest(provenance_path)
    approval["scanner_database"] = {
        **scanner_database,
        "evidence": {
            "path": database_evidence.name,
            "sha256": _runtime._digest(database_evidence),
        },
    }
    _runtime._save(approval_path, approval)
    return 0


def _verify_scanner_database(approval_path: Path) -> None:
    approval = _runtime._load(approval_path)
    scanner_database = approval.get("scanner_database")
    if not isinstance(scanner_database, dict):
        raise PolicyError("approval scanner_database evidence is missing")
    for field in ("schema_version", "built", "source"):
        if not isinstance(scanner_database.get(field), str) or not scanner_database[field].strip():
            raise PolicyError(f"approval scanner_database.{field} is invalid")
    content_digest = scanner_database.get("content_sha256")
    if not isinstance(content_digest, str) or _HEX_DIGEST.fullmatch(content_digest) is None:
        raise PolicyError("approval scanner database content digest is invalid")
    if scanner_database.get("valid") is not True:
        raise PolicyError("approval scanner database is not valid")
    evidence = scanner_database.get("evidence")
    if not isinstance(evidence, dict):
        raise PolicyError("approval scanner database evidence map is invalid")
    relative_path = evidence.get("path")
    if not isinstance(relative_path, str) or Path(relative_path).name != relative_path:
        raise PolicyError("approval scanner database evidence path is invalid")
    evidence_path = (approval_path.parent / relative_path).resolve()
    if evidence_path.parent != approval_path.parent.resolve():
        raise PolicyError("approval scanner database evidence escapes its directory")
    expected_checksum = evidence.get("sha256")
    if (
        not evidence_path.is_file()
        or not isinstance(expected_checksum, str)
        or _runtime._digest(evidence_path) != expected_checksum
    ):
        raise PolicyError("approval scanner database evidence checksum mismatch")
    normalized = _runtime._load(evidence_path)
    expected = {
        "schema_version": scanner_database["schema_version"],
        "built": scanner_database["built"],
        "source": scanner_database["source"],
        "valid": True,
        "content_sha256": content_digest,
    }
    if normalized != expected:
        raise PolicyError("approval scanner database evidence content mismatch")


def verify_approval(args: argparse.Namespace) -> int:
    result = int(_original_verify_approval(args))
    if result != 0:
        return result
    _verify_scanner_database(Path(args.approval).resolve())
    return 0


def deploy_approved(args: argparse.Namespace) -> int:
    verify_approval(
        argparse.Namespace(
            approval=args.approved_images,
            expected_source_sha=args.expected_repository_sha,
        )
    )
    return int(_original_deploy_approved(args))


def main() -> int:
    parser = argparse.ArgumentParser(description="Portal exact-image supply-chain policy")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build-verify")
    build.add_argument("--repository", default=".")
    build.add_argument("--source-sha", required=True)
    build.add_argument("--output-dir", required=True)
    build.add_argument("--approval", required=True)
    build.add_argument("--policy", default=str(DEFAULT_POLICY))
    build.set_defaults(handler=build_verify)

    verify = commands.add_parser("verify-approval")
    verify.add_argument("--approval", required=True)
    verify.add_argument("--expected-source-sha", required=True)
    verify.set_defaults(handler=verify_approval)

    deploy = commands.add_parser("deploy-approved")
    deploy.add_argument("--approved-images", required=True)
    deploy.add_argument("--repository", required=True)
    deploy.add_argument("--request", required=True)
    deploy.add_argument("--expected-repository-sha", required=True)
    deploy.add_argument("--report", required=True)
    deploy.set_defaults(handler=deploy_approved)

    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--policy", required=True)
    evaluate.add_argument("--grype", required=True)
    evaluate.add_argument("--sbom", required=True)
    evaluate.add_argument("--output", required=True)
    evaluate.set_defaults(handler=evaluate_files)

    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except (PolicyError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"portal supply-chain gate failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
