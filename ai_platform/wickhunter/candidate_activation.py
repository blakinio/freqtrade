from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, fields
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.candidate_evaluation_identity import validate_evaluation_case_counts
from ai_platform.wickhunter.contracts import BotMode
from ai_platform.wickhunter.lightgbm_scorer import (
    CalibrationCurve,
    LightGBMModelArtifact,
    LightGBMScorerError,
    LightGBMTrainingPolicy,
)
from ai_platform.wickhunter.paper_validation import (
    PaperRunRequest,
    PaperValidationError,
    PaperValidationPolicy,
    build_paper_run_request,
    publish_paper_run_request,
    verify_paper_run_request,
)
from ai_platform.wickhunter.parameters import (
    DEFAULT_RESEARCH_BOUNDS,
    WickHunterParameters,
    validate_parameters,
)


CANDIDATE_MANIFEST_SCHEMA = "wickhunter-candidate-materialization-manifest-v1"
CANDIDATE_ACTIVATION_SCHEMA = "wickhunter-candidate-paper-activation-v1"
CANDIDATE_FILES = frozenset(
    {
        "comparison-report.json",
        "evaluation-identity.json",
        "finite-search-audit.json",
        "model-artifact.json",
        "optimizer-result.json",
        "rollback.json",
        "selected-parameters.json",
    }
)
CHECKSUM_NAME = "artifact-sha256.txt"
MANIFEST_NAME = "manifest.json"


class CandidateActivationError(RuntimeError):
    """Raised when candidate evidence cannot be activated safely."""


@dataclass(frozen=True, slots=True)
class VerifiedCandidateIdentity:
    package_id: str
    manifest_sha256: str
    source_commit_sha: str
    evaluation_sha256: str
    parameter_version: str
    parameter_hash: str
    model_version: str
    model_hash: str
    model_artifact_sha256: str
    optimizer_result_id: str
    comparison_report_id: str
    rollback_model_version: str
    rollback_model_hash: str
    rollback_parameter_version: str
    rollback_parameter_hash: str
    candidate_root: Path


@dataclass(frozen=True, slots=True)
class VerifiedCandidatePackage:
    identity: VerifiedCandidateIdentity
    parameters: WickHunterParameters
    model_artifact: LightGBMModelArtifact


@dataclass(frozen=True, slots=True)
class CandidateActivationResult:
    identity: VerifiedCandidateIdentity
    parameters: WickHunterParameters
    request: PaperRunRequest
    policy: PaperValidationPolicy
    activation_root: Path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_sha256(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise CandidateActivationError(f"{field} must be a string")
    normalized = value.strip().lower()
    invalid_character = any(character not in "0123456789abcdef" for character in normalized)
    if len(normalized) != 64 or invalid_character:
        raise CandidateActivationError(f"{field} must be a lowercase SHA-256 digest")
    return normalized


def _require_git_sha(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise CandidateActivationError(f"{field} must be a string")
    normalized = value.strip().lower()
    invalid_character = any(character not in "0123456789abcdef" for character in normalized)
    if len(normalized) != 40 or invalid_character:
        raise CandidateActivationError(f"{field} must be a lowercase Git SHA")
    return normalized


def _require_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CandidateActivationError(f"{field} must be non-empty text")
    return value.strip()


def _require_exact_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CandidateActivationError(f"{field} must be non-empty text")
    return value


def _require_false(payload: dict[str, Any], field: str) -> None:
    if payload.get(field) is not False:
        raise CandidateActivationError(f"unsafe authority field: {field}")


def _require_zero_authority(payload: dict[str, Any], *, field: str) -> None:
    for name in (
        "automatic_promotion_enabled",
        "protected_holdout_accessed",
        "trading_credentials_present",
        "order_adapter_present",
        "execution_enabled",
        "live_capital_authorized",
    ):
        if name in payload:
            _require_false(payload, name)
    if payload.get("orders_submitted") != 0:
        raise CandidateActivationError(f"{field} submitted orders")


def _load_object(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CandidateActivationError(f"{field} must be a regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateActivationError(f"unable to read {field}") from exc
    if not isinstance(payload, dict):
        raise CandidateActivationError(f"{field} must contain an object")
    return payload


def _safe_file(root: Path, name: object, *, field: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).name != name:
        raise CandidateActivationError(f"{field} contains an unsafe path")
    path = root / name
    if path.is_symlink() or not path.is_file():
        raise CandidateActivationError(f"{field} references a missing regular file")
    return path


def _verify_checksum_index(root: Path) -> None:
    path = _safe_file(root, CHECKSUM_NAME, field="checksum index")
    entries: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise CandidateActivationError("unable to read checksum index") from exc
    for line in lines:
        digest, separator, name = line.partition("  ")
        if not separator or name in entries:
            raise CandidateActivationError("checksum index is malformed")
        entries[name] = _require_sha256(digest, field="checksum digest")
    expected = set(CANDIDATE_FILES) | {MANIFEST_NAME}
    if set(entries) != expected:
        raise CandidateActivationError("checksum index file set mismatch")
    for name, expected_digest in entries.items():
        if _sha256_file(_safe_file(root, name, field="checksum entry")) != expected_digest:
            raise CandidateActivationError(f"checksum mismatch for {name}")


def _verify_manifest(root: Path) -> dict[str, Any]:  # noqa: C901
    manifest = _load_object(root / MANIFEST_NAME, field="candidate manifest")
    if manifest.get("schema_version") != CANDIDATE_MANIFEST_SCHEMA:
        raise CandidateActivationError("candidate manifest schema mismatch")
    claimed = _require_sha256(manifest.get("manifest_sha256"), field="manifest_sha256")
    seed = dict(manifest)
    seed.pop("manifest_sha256", None)
    if canonical_sha256(seed) != claimed:
        raise CandidateActivationError("candidate manifest self-hash mismatch")
    _require_zero_authority(manifest, field="candidate manifest")
    if manifest.get("candidate_only") is not True:
        raise CandidateActivationError("candidate manifest must remain candidate-only")
    if manifest.get("owner_decision_required") is not True:
        raise CandidateActivationError("candidate manifest must require an owner decision")
    if manifest.get("selection_source") != "validation_only":
        raise CandidateActivationError("candidate selection source is not validation-only")
    if manifest.get("test_used_for_selection") is not False:
        raise CandidateActivationError("test evidence was used for candidate selection")

    records = manifest.get("files")
    if not isinstance(records, list) or len(records) != len(CANDIDATE_FILES):
        raise CandidateActivationError("candidate manifest file records are incomplete")
    observed: dict[str, tuple[str, int]] = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {
            "logical_name",
            "sha256",
            "size_bytes",
        }:
            raise CandidateActivationError("candidate manifest file record is malformed")
        name = record.get("logical_name")
        if not isinstance(name, str) or name in observed:
            raise CandidateActivationError("candidate manifest contains duplicate file records")
        digest = _require_sha256(record.get("sha256"), field="candidate file sha256")
        size = record.get("size_bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 1:
            raise CandidateActivationError("candidate file size is invalid")
        observed[name] = (digest, size)
    if set(observed) != set(CANDIDATE_FILES):
        raise CandidateActivationError("candidate manifest file set mismatch")
    for name, (digest, size) in observed.items():
        path = _safe_file(root, name, field="candidate artifact")
        if path.stat().st_size != size or _sha256_file(path) != digest:
            raise CandidateActivationError(f"candidate artifact identity mismatch: {name}")
    return manifest


def _decimal(value: object, *, field: str) -> Decimal:
    if isinstance(value, bool):
        raise CandidateActivationError(f"{field} must be decimal-compatible")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CandidateActivationError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite():
        raise CandidateActivationError(f"{field} must be finite")
    return parsed


def _parameters(payload: dict[str, Any]) -> WickHunterParameters:
    expected = {item.name for item in fields(WickHunterParameters)} | {"parameter_sha256"}
    if set(payload) != expected:
        raise CandidateActivationError("selected parameter field set mismatch")
    claimed = _require_sha256(payload.pop("parameter_sha256"), field="parameter_sha256")
    decimal_fields = {
        "liquidation_percentile",
        "liquidation_zscore",
        "minimum_quote_volume_usd",
        "long_vwap_distance_ratio",
        "short_vwap_distance_ratio",
        "minimum_wick_ratio",
        "minimum_volatility",
        "maximum_volatility",
        "base_risk_ratio",
        "leverage",
        "dca_spacing_ratio",
        "dca_total_risk_ratio",
        "take_profit_ratio",
        "stop_loss_ratio",
        "minimum_confidence",
        "minimum_risk_multiplier",
        "maximum_risk_multiplier",
    }
    integer_fields = {
        "burst_window_ms",
        "cooldown_ms",
        "maximum_event_age_ms",
        "dca_levels",
        "maximum_holding_ms",
    }
    normalized: dict[str, Any] = {}
    for name, value in payload.items():
        if name in decimal_fields:
            normalized[name] = _decimal(value, field=name)
        elif name in integer_fields:
            if isinstance(value, bool) or not isinstance(value, int):
                raise CandidateActivationError(f"{name} must be an integer")
            normalized[name] = value
        elif name == "dca_enabled":
            if not isinstance(value, bool):
                raise CandidateActivationError("dca_enabled must be boolean")
            normalized[name] = value
        elif name == "parameter_version":
            normalized[name] = _require_text(value, field=name)
        else:
            raise CandidateActivationError(f"unsupported parameter field: {name}")
    try:
        parameters = WickHunterParameters(**normalized)
        validate_parameters(parameters, DEFAULT_RESEARCH_BOUNDS)
    except (TypeError, ValueError) as exc:
        raise CandidateActivationError("selected parameters are invalid") from exc
    if parameters.parameter_hash != claimed:
        raise CandidateActivationError("selected parameter identity mismatch")
    return parameters


def _list(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise CandidateActivationError(f"{field} must be a list")
    return value


def _text_tuple(value: object, *, field: str) -> tuple[str, ...]:
    return tuple(_require_text(item, field=field) for item in _list(value, field=field))


def _decimal_tuple(value: object, *, field: str) -> tuple[Decimal, ...]:
    return tuple(_decimal(item, field=field) for item in _list(value, field=field))


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CandidateActivationError(f"{field} must be an integer")
    return value


def _boolean(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise CandidateActivationError(f"{field} must be boolean")
    return value


def _training_policy(value: object) -> LightGBMTrainingPolicy:
    if not isinstance(value, dict):
        raise CandidateActivationError("model training policy must be an object")
    expected = {item.name for item in fields(LightGBMTrainingPolicy)}
    if set(value) != expected:
        raise CandidateActivationError("model training policy field set mismatch")
    return LightGBMTrainingPolicy(
        schema_version=_require_text(value["schema_version"], field="training schema"),
        policy_version=_require_text(value["policy_version"], field="training policy"),
        training_splits=_text_tuple(value["training_splits"], field="training splits"),
        calibration_splits=_text_tuple(value["calibration_splits"], field="calibration splits"),
        validation_splits=_text_tuple(value["validation_splits"], field="validation splits"),
        forbidden_splits=_text_tuple(value["forbidden_splits"], field="forbidden splits"),
        seed=_integer(value["seed"], field="training seed"),
        num_boost_round=_integer(value["num_boost_round"], field="num_boost_round"),
        num_leaves=_integer(value["num_leaves"], field="num_leaves"),
        min_data_in_leaf=_integer(value["min_data_in_leaf"], field="min_data_in_leaf"),
        learning_rate=_decimal(value["learning_rate"], field="learning_rate"),
        calibration_bins=_integer(value["calibration_bins"], field="calibration_bins"),
        no_trade_confidence=_decimal(value["no_trade_confidence"], field="no_trade_confidence"),
    )


def _calibration(value: object) -> CalibrationCurve:
    if not isinstance(value, dict):
        raise CandidateActivationError("model calibration must be an object")
    expected = {item.name for item in fields(CalibrationCurve)}
    if set(value) != expected:
        raise CandidateActivationError("model calibration field set mismatch")
    return CalibrationCurve(
        schema_version=_require_text(value["schema_version"], field="calibration schema"),
        upper_bounds=_decimal_tuple(value["upper_bounds"], field="calibration upper bounds"),
        probabilities=_decimal_tuple(value["probabilities"], field="calibration probabilities"),
    )


def _model_artifact(payload: dict[str, Any]) -> LightGBMModelArtifact:
    artifact_fields = {item.name for item in fields(LightGBMModelArtifact)}
    expected = artifact_fields | {
        "artifact_sha256",
        "promotion_state",
        "advisory_only",
    }
    if set(payload) != expected:
        raise CandidateActivationError("model artifact field set mismatch")
    if payload.get("promotion_state") != "candidate":
        raise CandidateActivationError("model artifact must remain a candidate")
    if payload.get("advisory_only") is not True:
        raise CandidateActivationError("model artifact must remain advisory-only")
    claimed = _require_sha256(payload.get("artifact_sha256"), field="artifact_sha256")
    try:
        artifact = LightGBMModelArtifact(
            schema_version=_require_text(payload["schema_version"], field="model schema"),
            model_kind=_require_text(payload["model_kind"], field="model_kind"),
            model_version=_require_text(payload["model_version"], field="model_version"),
            model_hash=_require_sha256(payload["model_hash"], field="model_hash"),
            model_text=_require_exact_text(payload["model_text"], field="model_text"),
            feature_schema_version=_require_text(
                payload["feature_schema_version"],
                field="feature_schema_version",
            ),
            feature_schema_sha256=_require_sha256(
                payload["feature_schema_sha256"],
                field="feature_schema_sha256",
            ),
            feature_names=_text_tuple(payload["feature_names"], field="feature_names"),
            training_policy=_training_policy(payload["training_policy"]),
            dataset_id=_require_text(payload["dataset_id"], field="dataset_id"),
            dataset_manifest_sha256=_require_sha256(
                payload["dataset_manifest_sha256"],
                field="dataset_manifest_sha256",
            ),
            market_manifest_sha256=_require_sha256(
                payload["market_manifest_sha256"],
                field="market_manifest_sha256",
            ),
            split_geometry_sha256=_require_sha256(
                payload["split_geometry_sha256"],
                field="split_geometry_sha256",
            ),
            price_path_manifest_sha256=_require_sha256(
                payload["price_path_manifest_sha256"],
                field="price_path_manifest_sha256",
            ),
            replay_policy_version=_require_text(
                payload["replay_policy_version"],
                field="replay_policy_version",
            ),
            replay_policy_sha256=_require_sha256(
                payload["replay_policy_sha256"],
                field="replay_policy_sha256",
            ),
            parameter_version=_require_text(
                payload["parameter_version"], field="parameter_version"
            ),
            parameter_sha256=_require_sha256(payload["parameter_sha256"], field="parameter_sha256"),
            training_case_sha256s=_text_tuple(
                payload["training_case_sha256s"],
                field="training_case_sha256s",
            ),
            calibration_case_sha256s=_text_tuple(
                payload["calibration_case_sha256s"],
                field="calibration_case_sha256s",
            ),
            training_example_count=_integer(
                payload["training_example_count"],
                field="training_example_count",
            ),
            calibration_example_count=_integer(
                payload["calibration_example_count"],
                field="calibration_example_count",
            ),
            positive_example_count=_integer(
                payload["positive_example_count"],
                field="positive_example_count",
            ),
            negative_example_count=_integer(
                payload["negative_example_count"],
                field="negative_example_count",
            ),
            positive_return_mean=_decimal(
                payload["positive_return_mean"],
                field="positive_return_mean",
            ),
            negative_return_mean=_decimal(
                payload["negative_return_mean"],
                field="negative_return_mean",
            ),
            calibration=_calibration(payload["calibration"]),
            protected_holdout_accessed=_boolean(
                payload["protected_holdout_accessed"],
                field="protected_holdout_accessed",
            ),
            automatic_promotion_enabled=_boolean(
                payload["automatic_promotion_enabled"],
                field="automatic_promotion_enabled",
            ),
            execution_enabled=_boolean(payload["execution_enabled"], field="execution_enabled"),
            live_capital_authorized=_boolean(
                payload["live_capital_authorized"],
                field="live_capital_authorized",
            ),
            orders_submitted=_integer(payload["orders_submitted"], field="orders_submitted"),
        )
    except (LightGBMScorerError, TypeError, ValueError) as exc:
        raise CandidateActivationError("model artifact semantic validation failed") from exc
    if artifact.artifact_sha256 != claimed:
        raise CandidateActivationError("model artifact identity mismatch")
    return artifact


def _verify_model(payload: dict[str, Any], *, manifest: dict[str, Any]) -> LightGBMModelArtifact:
    _require_zero_authority(payload, field="model artifact")
    artifact = _model_artifact(payload)
    bindings = (
        (artifact.model_version, manifest.get("model_version"), "model_version"),
        (artifact.model_hash, manifest.get("model_hash"), "model_hash"),
        (
            artifact.artifact_sha256,
            manifest.get("model_artifact_sha256"),
            "model_artifact_sha256",
        ),
        (
            artifact.parameter_version,
            manifest.get("parameter_version"),
            "model parameter_version",
        ),
        (
            artifact.parameter_sha256,
            manifest.get("parameter_sha256"),
            "model parameter_sha256",
        ),
    )
    for actual, expected_value, field in bindings:
        if actual != expected_value:
            raise CandidateActivationError(f"candidate manifest binding mismatch: {field}")
    return artifact


def load_verified_candidate_package(  # noqa: C901
    root: Path,
) -> VerifiedCandidatePackage:
    if root.is_symlink() or not root.is_dir():
        raise CandidateActivationError("candidate root must be a regular directory")
    root = root.resolve(strict=True)
    actual_files = {
        path.name for path in root.iterdir() if path.is_file() and not path.is_symlink()
    }
    expected_files = set(CANDIDATE_FILES) | {MANIFEST_NAME, CHECKSUM_NAME}
    if actual_files != expected_files or any(path.is_dir() for path in root.iterdir()):
        raise CandidateActivationError("candidate package file set mismatch")
    _verify_checksum_index(root)
    manifest = _verify_manifest(root)

    parameter_payload = _load_object(
        root / "selected-parameters.json",
        field="selected parameters",
    )
    parameters = _parameters(dict(parameter_payload))
    if parameters.parameter_version != manifest.get("parameter_version"):
        raise CandidateActivationError("parameter version does not match candidate manifest")
    if parameters.parameter_hash != manifest.get("parameter_sha256"):
        raise CandidateActivationError("parameter hash does not match candidate manifest")

    model_payload = _load_object(root / "model-artifact.json", field="model artifact")
    model_artifact = _verify_model(model_payload, manifest=manifest)

    evaluation = _load_object(root / "evaluation-identity.json", field="evaluation identity")
    _require_zero_authority(evaluation, field="evaluation identity")
    if evaluation.get("evaluation_sha256") != manifest.get("evaluation_sha256"):
        raise CandidateActivationError("evaluation identity does not match candidate manifest")
    try:
        validate_evaluation_case_counts(evaluation)
    except ValueError as exc:
        raise CandidateActivationError(str(exc)) from exc

    optimizer = _load_object(root / "optimizer-result.json", field="optimizer result")
    _require_zero_authority(optimizer, field="optimizer result")
    if optimizer.get("result_id") != manifest.get("optimizer_result_id"):
        raise CandidateActivationError("optimizer identity does not match candidate manifest")
    if optimizer.get("selection_source") != "validation_only":
        raise CandidateActivationError("optimizer did not remain validation-only")
    if optimizer.get("test_used_for_selection") is not False:
        raise CandidateActivationError("optimizer used test evidence for selection")

    comparison = _load_object(root / "comparison-report.json", field="comparison report")
    _require_zero_authority(comparison, field="comparison report")
    if comparison.get("report_id") != manifest.get("comparison_report_id"):
        raise CandidateActivationError("comparison identity does not match candidate manifest")
    if comparison.get("profitability_claimed") is not False:
        raise CandidateActivationError("comparison report claims profitability")

    search = _load_object(root / "finite-search-audit.json", field="finite search audit")
    _require_zero_authority(search, field="finite search audit")
    if search.get("selection_source") != "validation_only":
        raise CandidateActivationError("finite search was not validation-only")
    if search.get("test_used_for_selection") is not False:
        raise CandidateActivationError("finite search used test evidence for selection")

    rollback = _load_object(root / "rollback.json", field="rollback evidence")
    _require_zero_authority(rollback, field="rollback evidence")
    if rollback.get("owner_decision_required") is not True:
        raise CandidateActivationError("rollback evidence must require owner decision")
    rollback_bindings = (
        ("model_version", "rollback_model_version"),
        ("model_hash", "rollback_model_hash"),
        ("parameter_version", "rollback_parameter_version"),
        ("parameter_hash", "rollback_parameter_hash"),
    )
    for rollback_field, manifest_field in rollback_bindings:
        if rollback.get(rollback_field) != manifest.get(manifest_field):
            raise CandidateActivationError(f"rollback binding mismatch: {rollback_field}")

    identity = VerifiedCandidateIdentity(
        package_id=_require_text(manifest.get("package_id"), field="package_id"),
        manifest_sha256=_require_sha256(manifest.get("manifest_sha256"), field="manifest_sha256"),
        source_commit_sha=_require_git_sha(
            manifest.get("source_commit_sha"), field="source_commit_sha"
        ),
        evaluation_sha256=_require_sha256(
            manifest.get("evaluation_sha256"), field="evaluation_sha256"
        ),
        parameter_version=_require_text(
            manifest.get("parameter_version"), field="parameter_version"
        ),
        parameter_hash=_require_sha256(manifest.get("parameter_sha256"), field="parameter_sha256"),
        model_version=_require_text(manifest.get("model_version"), field="model_version"),
        model_hash=_require_sha256(manifest.get("model_hash"), field="model_hash"),
        model_artifact_sha256=_require_sha256(
            manifest.get("model_artifact_sha256"), field="model_artifact_sha256"
        ),
        optimizer_result_id=_require_sha256(
            manifest.get("optimizer_result_id"), field="optimizer_result_id"
        ),
        comparison_report_id=_require_sha256(
            manifest.get("comparison_report_id"), field="comparison_report_id"
        ),
        rollback_model_version=_require_text(
            manifest.get("rollback_model_version"), field="rollback_model_version"
        ),
        rollback_model_hash=_require_sha256(
            manifest.get("rollback_model_hash"), field="rollback_model_hash"
        ),
        rollback_parameter_version=_require_text(
            manifest.get("rollback_parameter_version"),
            field="rollback_parameter_version",
        ),
        rollback_parameter_hash=_require_sha256(
            manifest.get("rollback_parameter_hash"),
            field="rollback_parameter_hash",
        ),
        candidate_root=root,
    )
    return VerifiedCandidatePackage(
        identity=identity,
        parameters=parameters,
        model_artifact=model_artifact,
    )


def verify_candidate_package(
    root: Path,
) -> tuple[VerifiedCandidateIdentity, WickHunterParameters]:
    package = load_verified_candidate_package(root)
    return package.identity, package.parameters


def _activation_binding(
    identity: VerifiedCandidateIdentity,
    request: PaperRunRequest,
) -> dict[str, Any]:
    binding: dict[str, Any] = {
        "schema_version": CANDIDATE_ACTIVATION_SCHEMA,
        "candidate_package_id": identity.package_id,
        "candidate_manifest_sha256": identity.manifest_sha256,
        "run_id": request.run_id,
        "model_version": identity.model_version,
        "model_hash": identity.model_hash,
        "parameter_version": identity.parameter_version,
        "parameter_hash": identity.parameter_hash,
        "evaluation_sha256": identity.evaluation_sha256,
        "code_sha": identity.source_commit_sha,
        "protected_holdout_accessed": False,
        "automatic_promotion_enabled": False,
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "execution_enabled": False,
        "live_capital_authorized": False,
        "orders_submitted": 0,
    }
    binding["binding_sha256"] = canonical_sha256(binding)
    return binding


def _verify_activation_binding(path: Path, expected: dict[str, Any]) -> None:
    actual = _load_object(path, field="activation binding")
    if actual != expected:
        raise CandidateActivationError("activation binding identity mismatch")


def _write_or_verify_activation_binding(path: Path, binding: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        _verify_activation_binding(path, binding)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(binding, sort_keys=True, separators=(",", ":")) + "\n"
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        _verify_activation_binding(path, binding)


def _publish_or_verify_activation(
    activation_root: Path,
    *,
    request: PaperRunRequest,
    policy: PaperValidationPolicy,
) -> None:
    if activation_root.exists() or activation_root.is_symlink():
        try:
            verified = verify_paper_run_request(activation_root)
        except PaperValidationError as exc:
            raise CandidateActivationError("existing activation request is invalid") from exc
        if verified.get("run_id") != request.run_id:
            raise CandidateActivationError("activation request identity mismatch")
        return
    try:
        publish_paper_run_request(
            activation_root,
            request=request,
            policy=policy,
        )
    except PaperValidationError as exc:
        if not activation_root.is_dir() or activation_root.is_symlink():
            raise CandidateActivationError("unable to publish activation request") from exc
        try:
            verified = verify_paper_run_request(activation_root)
        except PaperValidationError as verify_exc:
            raise CandidateActivationError(
                "published activation request is invalid"
            ) from verify_exc
        if verified.get("run_id") != request.run_id:
            raise CandidateActivationError("activation request identity mismatch") from exc


def activate_verified_candidate(
    *,
    candidate_root: Path,
    activation_root: Path,
    created_at_ms: int,
    bot_instance: str = "wickhunter-paper-v1",
    mode: BotMode = BotMode.PAPER,
    wh08_consumer_version: str = "wickhunter-portal-consumer-v1",
    window_duration_ms: int = 86_700_000,
    policy: PaperValidationPolicy | None = None,
) -> CandidateActivationResult:
    if created_at_ms <= 0:
        raise CandidateActivationError("created_at_ms must be positive")
    policy = policy or PaperValidationPolicy()
    if window_duration_ms < policy.minimum_duration_ms:
        raise CandidateActivationError("activation window is shorter than paper policy")
    identity, parameters = verify_candidate_package(candidate_root)
    request = build_paper_run_request(
        created_at_ms=created_at_ms,
        window_start_ms=created_at_ms,
        window_end_ms=created_at_ms + window_duration_ms,
        bot_instance=bot_instance,
        mode=mode,
        model_version=identity.model_version,
        model_hash=identity.model_hash,
        parameter_version=identity.parameter_version,
        parameter_hash=identity.parameter_hash,
        dataset_hash=identity.evaluation_sha256,
        code_sha=identity.source_commit_sha,
        rollback_model_version=identity.rollback_model_version,
        rollback_model_hash=identity.rollback_model_hash,
        rollback_parameter_version=identity.rollback_parameter_version,
        rollback_parameter_hash=identity.rollback_parameter_hash,
        wh08_consumer_version=wh08_consumer_version,
        policy=policy,
    )
    binding_path = activation_root.parent / f"{activation_root.name}-candidate-binding.json"
    binding = _activation_binding(identity, request)
    if binding_path.exists() or binding_path.is_symlink():
        _verify_activation_binding(binding_path, binding)
    _publish_or_verify_activation(
        activation_root,
        request=request,
        policy=policy,
    )
    _write_or_verify_activation_binding(binding_path, binding)
    return CandidateActivationResult(
        identity=identity,
        parameters=parameters,
        request=request,
        policy=policy,
        activation_root=activation_root,
    )
