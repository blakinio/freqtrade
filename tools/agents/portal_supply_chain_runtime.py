from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, TypedDict

from portal_supply_chain_policy import (
    PolicyError,
    evaluate_licenses,
    evaluate_vulnerabilities,
    scan_evidence,
    validate_policy,
)


IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}")
SOURCE_SHA = re.compile(r"[0-9a-f]{40}")
FROM_DIGEST = re.compile(
    r"^FROM\s+\S+@(?P<digest>sha256:[0-9a-f]{64})"
    r"(?:\s+AS\s+\S+)?\s*$",
    re.IGNORECASE,
)
DEFAULT_POLICY = Path("docs/ai_platform/portal/portal-supply-chain-policy.json")
EVIDENCE = (
    "sbom",
    "vulnerabilities",
    "licenses",
    "vulnerability_policy",
    "provenance",
)
ROLLBACK_ARCHIVE_DIRNAME = "supply-chain-approvals"
ROLLBACK_POINTER_SCHEMA_VERSION = 1


class ImageBuildSpec(TypedDict):
    dockerfile: Path
    context: Path
    manifests: list[Path]


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PolicyError(f"expected JSON object: {path}")
    return value


def _save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        output = " | ".join(
            line.strip()
            for stream in (result.stdout, result.stderr)
            for line in stream.splitlines()
            if line.strip()
        )
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}: {output[:1500]}"
        )
    return result


def _base_digests(dockerfile: Path) -> list[str]:
    result: list[str] = []
    for raw in dockerfile.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or not line.upper().startswith("FROM "):
            continue
        match = FROM_DIGEST.fullmatch(line)
        if match is None:
            raise PolicyError(f"Docker base is not digest-pinned: {dockerfile}: {line}")
        result.append(match.group("digest"))
    if not result:
        raise PolicyError(f"Dockerfile has no FROM instruction: {dockerfile}")
    return result


def _image_id(reference: str) -> str:
    value = _run(
        [
            "docker",
            "image",
            "inspect",
            "--format",
            "{{.Id}}",
            reference,
        ]
    ).stdout.strip()
    if IMAGE_ID.fullmatch(value) is None:
        raise PolicyError(f"invalid Docker image ID: {reference}")
    return value


def _verify_revision(reference: str, source_sha: str) -> None:
    value = _run(
        [
            "docker",
            "image",
            "inspect",
            "--format",
            ('{{ index .Config.Labels "org.opencontainers.image.revision" }}'),
            reference,
        ]
    ).stdout.strip()
    if value != source_sha:
        raise PolicyError(f"image revision label mismatch: {reference}")


def _tool_version(command: list[str]) -> str:
    return _run(command).stdout.strip().splitlines()[0][:300]


def _build(
    repo: Path,
    name: str,
    dockerfile: Path,
    context: Path,
    source_sha: str,
) -> tuple[str, str]:
    tag = f"local/freqtrade-portal-{name}:{source_sha[:12]}"
    _run(
        [
            "docker",
            "build",
            "--pull=false",
            "--label",
            f"org.opencontainers.image.revision={source_sha}",
            "--file",
            str(dockerfile),
            "--tag",
            tag,
            str(context),
        ],
        cwd=repo,
    )
    image = _image_id(tag)
    _verify_revision(image, source_sha)
    return tag, image


def _provenance(
    *,
    name: str,
    image: str,
    source_sha: str,
    dockerfile: Path,
    repo: Path,
    policy: Path,
    manifests: list[Path],
    bases: list[str],
    tools: dict[str, str],
) -> dict[str, Any]:
    materials = [
        {
            "uri": dockerfile.relative_to(repo).as_posix(),
            "digest": {"sha256": _digest(dockerfile)},
        },
        {
            "uri": policy.relative_to(repo).as_posix(),
            "digest": {"sha256": _digest(policy)},
        },
        *[
            {
                "uri": path.relative_to(repo).as_posix(),
                "digest": {"sha256": _digest(path)},
            }
            for path in manifests
        ],
        *[
            {
                "uri": f"docker-base:{value}",
                "digest": {"sha256": value.removeprefix("sha256:")},
            }
            for value in bases
        ],
    ]
    predicate = {
        "buildDefinition": {
            "buildType": ("https://github.com/blakinio/freqtrade/portal-exact-image@v1"),
            "externalParameters": {
                "image_name": f"freqtrade-portal-{name}",
                "final_image_digest": image,
                "source_sha": source_sha,
            },
            "resolvedDependencies": materials,
        },
        "runDetails": {
            "builder": {"id": ("https://github.com/blakinio/freqtrade/actions")},
            "metadata": {"invocationId": "github-actions"},
            "byproducts": [
                {
                    "name": key,
                    "annotations": {"version": value},
                }
                for key, value in sorted(tools.items())
            ],
        },
    }
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {
                "name": f"freqtrade-portal-{name}",
                "digest": {"sha256": image.removeprefix("sha256:")},
            }
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": predicate,
    }


def build_verify(args: argparse.Namespace) -> int:
    repo = Path(args.repository).resolve()
    source_sha = args.source_sha
    if SOURCE_SHA.fullmatch(source_sha) is None:
        raise PolicyError("source SHA must be 40 lowercase hex characters")
    policy_path = (repo / args.policy).resolve()
    policy = _load(policy_path)
    validate_policy(policy)
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    generated_at = dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")
    tools = {
        "syft": _tool_version(["syft", "version"]),
        "grype": _tool_version(["grype", "version"]),
    }
    specs: dict[str, ImageBuildSpec] = {
        "control-plane": {
            "dockerfile": (repo / "deploy/synology/portal-oidc/Dockerfile.control-plane"),
            "context": repo,
            "manifests": [repo / "deploy/synology/portal-oidc/requirements.txt"],
        },
        "web": {
            "dockerfile": (repo / "deploy/synology/portal/Dockerfile"),
            "context": repo / "ai_platform/portal/web",
            "manifests": [
                repo / "ai_platform/portal/web/package.json",
                repo / "ai_platform/portal/web/package-lock.json",
            ],
        },
    }
    images: dict[str, Any] = {}
    documents: list[tuple[str, Any]] = []
    for name, spec in specs.items():
        tag, image = _build(
            repo,
            name,
            spec["dockerfile"],
            spec["context"],
            source_sha,
        )
        prefix = output / name
        sbom = prefix.with_suffix(".sbom.cdx.json")
        grype = prefix.with_suffix(".grype.json")
        licenses = prefix.with_suffix(".licenses.json")
        vulnerabilities = prefix.with_suffix(".vulnerability-policy.json")
        provenance = prefix.with_suffix(".provenance.json")
        _run(
            [
                "syft",
                image,
                "-o",
                f"cyclonedx-json={sbom}",
            ]
        )
        grype_payload = json.loads(
            _run(
                [
                    "grype",
                    f"sbom:{sbom}",
                    "-o",
                    "json",
                ]
            ).stdout
        )
        _save(grype, grype_payload)
        sbom_payload = _load(sbom)
        license_payload = evaluate_licenses(
            sbom_payload,
            policy,
        )
        vulnerability_payload = evaluate_vulnerabilities(
            grype_payload,
            policy,
        )
        _save(licenses, license_payload)
        _save(vulnerabilities, vulnerability_payload)
        if license_payload["status"] != "pass" or vulnerability_payload["status"] != "pass":
            raise PolicyError(f"{name} violates vulnerability or license policy")
        bases = _base_digests(spec["dockerfile"])
        _save(
            provenance,
            _provenance(
                name=name,
                image=image,
                source_sha=source_sha,
                dockerfile=spec["dockerfile"],
                repo=repo,
                policy=policy_path,
                manifests=spec["manifests"],
                bases=bases,
                tools=tools,
            ),
        )
        files = {
            "sbom": sbom,
            "vulnerabilities": grype,
            "licenses": licenses,
            "vulnerability_policy": vulnerabilities,
            "provenance": provenance,
        }
        documents.extend((f"{name}.{key}", _load(path)) for key, path in files.items())
        images[name] = {
            "tag": tag,
            "digest": image,
            "base_digests": bases,
            "evidence": {
                key: {
                    "path": path.name,
                    "sha256": _digest(path),
                }
                for key, path in files.items()
            },
        }
    violations = scan_evidence(documents, policy)
    if violations:
        raise PolicyError("evidence policy rejected reports: " + "; ".join(violations[:10]))
    approval = {
        "schema_version": 1,
        "status": "approved",
        "source_sha": source_sha,
        "generated_at": generated_at,
        "policy": {
            "path": policy_path.relative_to(repo).as_posix(),
            "sha256": _digest(policy_path),
        },
        "images": images,
        "secret_values_recorded": False,
        "private_infrastructure_recorded": False,
        "live_capital_authorized": False,
    }
    approval_path = Path(args.approval).resolve()
    _save(approval_path, approval)
    print(
        json.dumps(
            {
                "approval": str(approval_path),
                "images": {key: value["digest"] for key, value in images.items()},
            },
            sort_keys=True,
        )
    )
    return 0


def _approval_evidence_path(
    approval_path: Path,
    relative_value: Any,
    context: str,
) -> Path:
    if not isinstance(relative_value, str) or not relative_value:
        raise PolicyError(f"invalid evidence path: {context}")
    relative = Path(relative_value)
    if relative.is_absolute() or relative.name != relative_value:
        raise PolicyError(f"evidence path must be a file name: {context}")
    root = approval_path.parent.resolve()
    path = (root / relative).resolve()
    if path.parent != root or not path.is_file() or path.is_symlink():
        raise PolicyError(f"evidence path escapes approval directory: {context}")
    return path


def _private_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _optional_private_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.is_symlink():
        raise PolicyError(f"rollback pointer cannot be a symlink: {path.name}")
    return _load(path)


def _approval_archive_files(
    approval_path: Path,
    approval: dict[str, Any],
) -> dict[str, Path]:
    files: dict[str, Path] = {"approval.json": approval_path}
    images = approval.get("images")
    if not isinstance(images, dict):
        raise PolicyError("approval image map is missing")
    for image_name, detail in images.items():
        if not isinstance(detail, dict):
            raise PolicyError(f"invalid approval image detail: {image_name}")
        evidence = detail.get("evidence")
        if not isinstance(evidence, dict):
            raise PolicyError(f"missing approval evidence: {image_name}")
        for evidence_name, entry in evidence.items():
            if not isinstance(entry, dict):
                raise PolicyError(f"invalid approval evidence: {image_name}.{evidence_name}")
            source = _approval_evidence_path(
                approval_path,
                entry.get("path"),
                f"{image_name}.{evidence_name}",
            )
            destination = source.name
            existing = files.get(destination)
            if existing is not None and existing != source:
                raise PolicyError(f"duplicate approval evidence name: {destination}")
            files[destination] = source
    scanner_database = approval.get("scanner_database")
    if scanner_database is not None:
        if not isinstance(scanner_database, dict):
            raise PolicyError("approval scanner_database evidence is invalid")
        entry = scanner_database.get("evidence")
        if not isinstance(entry, dict):
            raise PolicyError("approval scanner_database evidence map is invalid")
        source = _approval_evidence_path(
            approval_path,
            entry.get("path"),
            "scanner_database",
        )
        files[source.name] = source
    return files


def _archive_id(approval_path: Path, approval: dict[str, Any]) -> str:
    source_sha = approval.get("source_sha")
    if not isinstance(source_sha, str) or SOURCE_SHA.fullmatch(source_sha) is None:
        raise PolicyError("approval source SHA is invalid for archival")
    return f"{source_sha}-{_digest(approval_path)[:16]}"


def _prepare_approval_archive(
    archive_root: Path,
    approval_path: Path,
    repo: Path,
    request_path: Path,
) -> tuple[Path, dict[str, Any]]:
    approval = _load(approval_path)
    archive_id = _archive_id(approval_path, approval)
    archive_root.mkdir(parents=True, exist_ok=True)
    archive_root.chmod(0o700)
    target = archive_root / archive_id
    images = approval.get("images")
    if not isinstance(images, dict) or set(images) != {"control-plane", "web"}:
        raise PolicyError("approval image map is invalid for archival")
    pointer = {
        "schema_version": ROLLBACK_POINTER_SCHEMA_VERSION,
        "status": "approved",
        "archive_id": archive_id,
        "source_sha": approval["source_sha"],
        "approval_manifest_sha256": _digest(approval_path),
        "images": {name: detail["digest"] for name, detail in images.items()},
    }
    if target.exists():
        _validate_approval_archive(target, pointer, require_deployed=False)
        return target, pointer

    temporary = Path(tempfile.mkdtemp(prefix=f".{archive_id}.", dir=archive_root))
    temporary.chmod(0o700)
    try:
        manifest: dict[str, str] = {}
        for destination, source in _approval_archive_files(
            approval_path,
            approval,
        ).items():
            copied = temporary / destination
            shutil.copyfile(source, copied)
            copied.chmod(0o600)
            manifest[destination] = _digest(copied)
        policy = approval.get("policy")
        if not isinstance(policy, dict):
            raise PolicyError("approval policy binding is missing")
        policy_value = policy.get("path")
        if not isinstance(policy_value, str) or not policy_value:
            raise PolicyError("approval policy path is invalid")
        policy_source = (repo / policy_value).resolve()
        if repo.resolve() not in policy_source.parents or not policy_source.is_file():
            raise PolicyError("approval policy path escapes repository")
        if _digest(policy_source) != policy.get("sha256"):
            raise PolicyError("approval policy checksum mismatch")
        policy_copy = temporary / "policy.json"
        if policy_copy.name in manifest:
            raise PolicyError("approval evidence collides with archived policy")
        shutil.copyfile(policy_source, policy_copy)
        policy_copy.chmod(0o600)
        manifest[policy_copy.name] = _digest(policy_copy)
        if not request_path.is_file() or request_path.is_symlink():
            raise PolicyError("deployment request is not a regular file")
        request_copy = temporary / "deployment-request.json"
        if request_copy.name in manifest:
            raise PolicyError("approval evidence collides with deployment request")
        shutil.copyfile(request_path, request_copy)
        request_copy.chmod(0o600)
        manifest[request_copy.name] = _digest(request_copy)
        metadata = {
            **pointer,
            "status": "approved_not_deployed",
            "evidence": dict(sorted(manifest.items())),
            "secret_values_recorded": False,
            "private_infrastructure_recorded": False,
            "live_capital_authorized": False,
        }
        _private_json(temporary / "archive-metadata.json", metadata)
        temporary.replace(target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return target, pointer


def _approval_archive_metadata(
    archive: Path,
    pointer: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not archive.is_dir() or archive.is_symlink():
        raise PolicyError("approval archive is unavailable")
    approval_path = archive / "approval.json"
    metadata_path = archive / "archive-metadata.json"
    if (
        not approval_path.is_file()
        or approval_path.is_symlink()
        or not metadata_path.is_file()
        or metadata_path.is_symlink()
    ):
        raise PolicyError("approval archive metadata is incomplete")
    if _digest(approval_path) != pointer.get("approval_manifest_sha256"):
        raise PolicyError("approval archive manifest checksum mismatch")
    approval = _load(approval_path)
    metadata = _load(metadata_path)
    if metadata.get("archive_id") != pointer.get("archive_id"):
        raise PolicyError("approval archive ID mismatch")
    if metadata.get("source_sha") != pointer.get("source_sha"):
        raise PolicyError("approval archive source SHA mismatch")
    images = approval.get("images")
    expected_images = (
        {name: detail.get("digest") for name, detail in images.items()}
        if isinstance(images, dict)
        else None
    )
    if expected_images != pointer.get("images"):
        raise PolicyError("approval archive image map mismatch")
    evidence = metadata.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        raise PolicyError("approval archive evidence manifest is missing")
    return metadata, evidence


def _validate_archive_evidence(
    archive: Path,
    evidence: dict[str, Any],
) -> None:
    for name, expected_digest in evidence.items():
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or not isinstance(expected_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_digest) is None
        ):
            raise PolicyError("approval archive evidence entry is invalid")
        evidence_path = archive / name
        if (
            not evidence_path.is_file()
            or evidence_path.is_symlink()
            or _digest(evidence_path) != expected_digest
        ):
            raise PolicyError(f"approval archive evidence mismatch: {name}")


def _validate_deployed_archive(
    archive: Path,
    metadata: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    if metadata.get("status") != "deployed":
        raise PolicyError("rollback approval archive is not deployed")
    report_digest = metadata.get("deployment_report_sha256")
    report_path = archive / "deployment-report.json"
    if (
        not isinstance(report_digest, str)
        or not report_path.is_file()
        or report_path.is_symlink()
        or _digest(report_path) != report_digest
        or evidence.get(report_path.name) != report_digest
    ):
        raise PolicyError("rollback deployment report evidence mismatch")


def _validate_approval_archive(
    archive: Path,
    pointer: dict[str, Any],
    *,
    require_deployed: bool,
) -> None:
    metadata, evidence = _approval_archive_metadata(archive, pointer)
    _validate_archive_evidence(archive, evidence)
    if require_deployed:
        _validate_deployed_archive(archive, metadata, evidence)


def _validate_rollback_pointer(
    archive_root: Path,
    pointer: dict[str, Any],
) -> None:
    if pointer.get("schema_version") != ROLLBACK_POINTER_SCHEMA_VERSION:
        raise PolicyError("rollback pointer schema is invalid")
    archive_id = pointer.get("archive_id")
    if not isinstance(archive_id, str) or Path(archive_id).name != archive_id:
        raise PolicyError("rollback pointer archive ID is invalid")
    images = pointer.get("images")
    if not isinstance(images, dict) or set(images) != {"control-plane", "web"}:
        raise PolicyError("rollback pointer image map is invalid")
    for image in images.values():
        if not isinstance(image, str) or IMAGE_ID.fullmatch(image) is None:
            raise PolicyError("rollback pointer image digest is invalid")
        if _image_id(image) != image:
            raise PolicyError("rollback image is not retained locally")
    archive = archive_root / archive_id
    _validate_approval_archive(archive, pointer, require_deployed=True)
    report_digest = pointer.get("deployment_report_sha256")
    if (
        not isinstance(report_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", report_digest) is None
        or _digest(archive / "deployment-report.json") != report_digest
    ):
        raise PolicyError("rollback pointer deployment report checksum mismatch")


def _tag_approved_images(images: dict[str, str], role: str) -> None:
    if role not in {"current", "previous"}:
        raise ValueError("unsupported approved image role")
    for name, image in images.items():
        _run(
            [
                "docker",
                "image",
                "tag",
                image,
                f"local/freqtrade-portal-{name}:approved-{role}",
            ]
        )


def _promote_approval_archive(
    archive_root: Path,
    archive: Path,
    pointer: dict[str, Any],
    report_path: Path,
    previous: dict[str, Any] | None,
) -> None:
    report_copy = archive / "deployment-report.json"
    shutil.copyfile(report_path, report_copy)
    report_copy.chmod(0o600)
    report_digest = _digest(report_copy)
    metadata_path = archive / "archive-metadata.json"
    metadata = _load(metadata_path)
    evidence = metadata.get("evidence")
    if not isinstance(evidence, dict):
        raise PolicyError("approval archive evidence manifest is missing")
    evidence[report_copy.name] = report_digest
    metadata.update(
        {
            "status": "deployed",
            "deployment_report_sha256": report_digest,
            "evidence": dict(sorted(evidence.items())),
        }
    )
    _private_json(metadata_path, metadata)
    previous_path = archive_root / "previous.json"
    if previous is not None:
        _private_json(previous_path, previous)
    else:
        previous_path.unlink(missing_ok=True)
    current = {
        **pointer,
        "status": "deployed",
        "deployment_report_sha256": report_digest,
    }
    _private_json(archive_root / "current.json", current)


def _verify_image_approval(
    approval_path: Path,
    source_sha: str,
    name: str,
    detail: Any,
) -> str:
    if not isinstance(detail, dict):
        raise PolicyError(f"invalid image approval: {name}")
    image = detail.get("digest")
    if not isinstance(image, str) or IMAGE_ID.fullmatch(image) is None or _image_id(image) != image:
        raise PolicyError(f"approved image is unavailable: {name}")
    _verify_revision(image, source_sha)
    evidence = detail.get("evidence")
    if not isinstance(evidence, dict):
        raise PolicyError(f"missing evidence map: {name}")
    for evidence_name in EVIDENCE:
        entry = evidence.get(evidence_name)
        if not isinstance(entry, dict):
            raise PolicyError(f"missing {evidence_name} evidence for {name}")
        evidence_path = _approval_evidence_path(
            approval_path,
            entry.get("path"),
            f"{name}.{evidence_name}",
        )
        if _digest(evidence_path) != entry.get("sha256"):
            raise PolicyError(f"evidence checksum mismatch: {name}.{evidence_name}")
    return image


def verify_approval(args: argparse.Namespace) -> int:
    approval_path = Path(args.approval).resolve()
    approval = _load(approval_path)
    source_sha = args.expected_source_sha
    if approval.get("schema_version") != 1 or approval.get("status") != "approved":
        raise PolicyError("approval is not an approved schema v1 manifest")
    if approval.get("source_sha") != source_sha or SOURCE_SHA.fullmatch(source_sha) is None:
        raise PolicyError("approval source SHA mismatch")
    for field in (
        "secret_values_recorded",
        "private_infrastructure_recorded",
        "live_capital_authorized",
    ):
        if approval.get(field) is not False:
            raise PolicyError(f"approval must set {field}=false")
    images = approval.get("images")
    if not isinstance(images, dict) or set(images) != {"control-plane", "web"}:
        raise PolicyError("approval must contain control-plane and web images")
    result = {
        name: _verify_image_approval(approval_path, source_sha, name, detail)
        for name, detail in images.items()
    }
    print(json.dumps(result, sort_keys=True))
    return 0


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _approved_image_tuple(
    images: dict[str, str],
) -> tuple[str, str, str, str]:
    return (
        images["control-plane"],
        images["control-plane"],
        images["web"],
        images["web"],
    )


def _annotate_deployment_report(
    report_path: Path,
    approval_path: Path,
    images: dict[str, str],
    *,
    archive_id: str | None = None,
    previous: dict[str, Any] | None = None,
) -> None:
    report = _load(report_path)
    portal = report.get("portal")
    if not isinstance(portal, dict):
        raise PolicyError("successful deployment report has no Portal section")
    if portal.get("control_plane_image_id") != images["control-plane"]:
        raise PolicyError("deployed control-plane image differs from approval")
    if portal.get("web_image_id") != images["web"]:
        raise PolicyError("deployed web image differs from approval")
    report["supply_chain"] = {
        "status": "approved_exact_images",
        "approval_manifest_sha256": _digest(approval_path),
        "control_plane_image_id": images["control-plane"],
        "web_image_id": images["web"],
        "rebuilt_during_deploy": False,
        "secret_values_recorded": False,
        "private_infrastructure_recorded": False,
        "approval_archive_id": archive_id,
        "rollback_previous_available": previous is not None,
        "rollback_previous_images": (previous.get("images") if previous is not None else None),
    }
    _save(report_path, report)


def deploy_approved(args: argparse.Namespace) -> int:
    approval_path = Path(args.approved_images).resolve()
    verify_approval(
        argparse.Namespace(
            approval=str(approval_path),
            expected_source_sha=args.expected_repository_sha,
        )
    )
    approval = _load(approval_path)
    images = {name: detail["digest"] for name, detail in approval["images"].items()}
    repo = Path(args.repository).resolve()
    directory = repo / "deploy/synology/portal-oidc"
    deploy = _module(
        "portal_oidc_deploy",
        directory / "deploy.py",
    )
    discovery = _module(
        "portal_oidc_discovery",
        directory / "diagnose_discovery.py",
    )
    entrypoint = _module(
        "portal_oidc_deploy_entrypoint",
        directory / "deploy_entrypoint.py",
    )
    setattr(  # noqa: B010
        deploy,
        "_discovery_from_identity_container",
        lambda: discovery.deployment_probe(deploy.DeploymentError),
    )
    entrypoint._install_verified_build_timeout(deploy)
    entrypoint._install_docker_host_liquidations_preflight(deploy)
    setattr(  # noqa: B010
        deploy,
        "_build_images",
        lambda _repo, _sha: _approved_image_tuple(images),
    )
    archive_root = Path(deploy.PORTAL_STATE_DIR) / ROLLBACK_ARCHIVE_DIRNAME
    request_path = Path(args.request).resolve()
    archive, pointer = _prepare_approval_archive(
        archive_root,
        approval_path,
        repo,
        request_path,
    )
    current = _optional_private_json(archive_root / "current.json")
    retained_previous = _optional_private_json(archive_root / "previous.json")
    if current is not None:
        _validate_rollback_pointer(archive_root, current)
    if retained_previous is not None:
        _validate_rollback_pointer(archive_root, retained_previous)
    previous: dict[str, Any] | None
    if current is not None and current.get("archive_id") != pointer["archive_id"]:
        previous = current
    elif current is not None:
        previous = retained_previous
    else:
        previous = None
    if previous is not None:
        _tag_approved_images(previous["images"], "previous")
    report_path = Path(args.report).resolve()
    result = int(
        deploy.deploy(
            argparse.Namespace(
                repository=str(repo),
                request=args.request,
                expected_repository_sha=(args.expected_repository_sha),
                report=str(report_path),
            )
        )
    )
    if result == 0:
        _tag_approved_images(images, "current")
        _annotate_deployment_report(
            report_path,
            approval_path,
            images,
            archive_id=pointer["archive_id"],
            previous=previous,
        )
        _promote_approval_archive(
            archive_root,
            archive,
            pointer,
            report_path,
            previous,
        )
        print(
            json.dumps(
                {
                    "report": str(report_path),
                    "sha256": _digest(report_path),
                    "status": "success",
                },
                sort_keys=True,
            )
        )
    return result


def evaluate_files(args: argparse.Namespace) -> int:
    policy = _load(Path(args.policy))
    validate_policy(policy)
    vulnerability = evaluate_vulnerabilities(
        _load(Path(args.grype)),
        policy,
    )
    licenses = evaluate_licenses(
        _load(Path(args.sbom)),
        policy,
    )
    _save(
        Path(args.output),
        {
            "vulnerability": vulnerability,
            "license": licenses,
        },
    )
    return 0 if (vulnerability["status"] == licenses["status"] == "pass") else 2
