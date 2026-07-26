"""Inert standard-library provenance primitives for future RL-v2 experiments."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


SCHEMA_VERSION = 1
CANONICAL_JSON_MEDIA_TYPE = "application/json; charset=utf-8"
PROVENANCE_CLASSIFICATIONS = frozenset({"internal_restricted", "sanitized_public"})
DETERMINISM_CLASSES = frozenset(
    {
        "full_determinism_claimed",
        "conditional_determinism_claimed",
        "no_determinism_guarantee",
    }
)
TENSOR_ROLES = frozenset({"parameter", "buffer", "optimizer_state"})
DTYPE_BYTE_WIDTHS = {
    "bool": 1,
    "uint8": 1,
    "int8": 1,
    "int16": 2,
    "float16": 2,
    "bfloat16": 2,
    "int32": 4,
    "float32": 4,
    "int64": 8,
    "float64": 8,
    "complex64": 8,
    "complex128": 16,
}
AUTHORIZATION_BOOLEAN_FIELDS = frozenset(
    {
        "model_training",
        "inference",
        "backtest",
        "replay",
        "seed_rerun",
        "market_data_access",
        "canonical_request_creation",
        "execution_workflow",
        "ranking",
        "selection",
        "promotion",
        "dry_run",
        "shadow",
        "live",
        "consumed_historical_oos_access",
        "protected_final_holdout_access",
        "phase6_changed",
    }
)
OPTIONAL_FIELD_PATHS = (
    "execution_environment.runner_image",
    "execution_environment.cpu_model",
    "execution_environment.gpu_model",
    "execution_environment.gpu_driver_version",
    "execution_environment.cuda_version",
    "execution_environment.cudnn_version",
    "execution_environment.container_image_digest",
    "determinism.conditions",
    "determinism.torch_deterministic_algorithms",
    "determinism.torch_deterministic_warn_only",
    "determinism.cudnn_deterministic",
    "determinism.cudnn_benchmark",
    "determinism.cuda_workspace_config",
    "determinism.torch_intraop_threads",
    "determinism.torch_interop_threads",
    "determinism.multiprocessing_start_method",
    "determinism.process_count",
    "determinism.worker_count",
    "seed_rng.ppo_seed",
    "seed_rng.environment_seed",
    "seed_rng.action_space_seed",
    "seed_rng.python_initial_state_sha256",
    "seed_rng.numpy_initial_state_sha256",
    "seed_rng.torch_cpu_initial_state_sha256",
    "seed_rng.gymnasium_initial_state_sha256",
    "seed_rng.stable_baselines3_initial_state_sha256",
    "seed_rng.consumed_before_snapshot",
    "seed_rng.final_state_manifest_sha256",
    "policy_state.initial_digest_sha256",
    "policy_state.final_digest_sha256",
    "policy_state.trainable_parameters_digest_sha256",
    "policy_state.buffers_digest_sha256",
    "optimizer_state.state_digest_sha256",
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_GIT_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
_ID_RE = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,255}\Z")
_DEVICE_RE = re.compile(r"(?:cuda|xpu):[0-9]+\Z")
_SENSITIVE_KEY_RE = re.compile(
    r"(?:^|_)(?:api_?key|secret|token|password|passwd|cookie|authorization_?header|"
    r"private_?endpoint|credential(?:s|_material)?)(?:$|_)",
    re.IGNORECASE,
)
_SENSITIVE_VALUE_RE = re.compile(
    r"(?:^|\b)(?:bearer\s+|basic\s+|sk-[a-z0-9_-]{8,}|api[_-]?key\s*[:=]|"
    r"password\s*[:=]|access[_-]?token\s*[:=])",
    re.IGNORECASE,
)
_PRIVATE_ENDPOINT_RE = re.compile(
    r"https?://(?:localhost|127(?:\.[0-9]{1,3}){3}|10(?:\.[0-9]{1,3}){3}|"
    r"192\.168(?:\.[0-9]{1,3}){2}|172\.(?:1[6-9]|2[0-9]|3[01])"
    r"(?:\.[0-9]{1,3}){2}|[^/]+\.(?:internal|local))(?:[:/]|\Z)",
    re.IGNORECASE,
)


class RLV2ProvenanceError(ValueError):
    """Raised when inert RL-v2 provenance fails closed."""


@dataclass(frozen=True)
class TensorRecord:
    """Dependency-light semantic representation of one tensor-like entry."""

    logical_name: str
    role: str
    element_type: str
    dtype: str
    shape: tuple[int, ...]
    device: str
    byte_order: str
    raw_bytes: bytes


def _canonical_value(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, bool | str | int):
        return
    if isinstance(value, float):
        prefix = "non-finite " if not math.isfinite(value) else ""
        raise RLV2ProvenanceError(f"{path}: {prefix}JSON floats are forbidden")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _canonical_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise RLV2ProvenanceError(f"{path}: JSON object keys must be strings")
            _canonical_value(item, f"{path}.{key}")
        return
    raise RLV2ProvenanceError(f"{path}: unsupported JSON type {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return canonical UTF-8 JSON followed by exactly one LF byte."""

    _canonical_value(value)
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return f"{text}\n".encode()


def canonical_sha256(value: Any) -> str:
    """Return SHA-256 over canonical JSON bytes."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def normalize_device(value: str) -> str:
    """Normalize a dependency-neutral device label."""

    normalized = value.strip().casefold().replace(" ", "")
    aliases = {
        "cpu": "cpu",
        "cpu:0": "cpu",
        "gpu": "cuda:0",
        "gpu:0": "cuda:0",
        "cuda": "cuda:0",
    }
    if normalized in aliases:
        return aliases[normalized]
    if normalized == "mps" or _DEVICE_RE.fullmatch(normalized):
        return normalized
    raise RLV2ProvenanceError(f"Unsupported device label: {value}")


def _frame(value: bytes) -> bytes:
    return len(value).to_bytes(8, "big") + value


def semantic_tensor_state_digest(records: Iterable[TensorRecord]) -> str:
    """Hash semantic tensor state independently of archive and filesystem metadata."""

    entries: list[tuple[str, dict[str, Any], bytes]] = []
    seen: set[str] = set()
    for record in records:
        name = record.logical_name
        if not isinstance(name, str) or not _ID_RE.fullmatch(name):
            raise RLV2ProvenanceError(f"Invalid logical tensor identity: {name}")
        if name in seen:
            raise RLV2ProvenanceError(f"Duplicate logical tensor identity: {name}")
        seen.add(name)
        if record.role not in TENSOR_ROLES:
            raise RLV2ProvenanceError(f"Unknown tensor role: {record.role}")
        if record.element_type != "dense_tensor":
            raise RLV2ProvenanceError(f"Unknown tensor element type: {record.element_type}")
        width = DTYPE_BYTE_WIDTHS.get(record.dtype)
        if width is None:
            raise RLV2ProvenanceError(f"Unknown tensor dtype: {record.dtype}")
        if record.byte_order not in {"little", "big", "not_applicable"}:
            raise RLV2ProvenanceError(f"Invalid tensor byte order: {record.byte_order}")
        byte_order_optional = record.dtype in {"bool", "uint8", "int8"}
        if not byte_order_optional and record.byte_order == "not_applicable":
            raise RLV2ProvenanceError("Multi-byte tensor dtype requires explicit byte order")
        if any(
            isinstance(size, bool) or not isinstance(size, int) or size < 0
            for size in record.shape
        ):
            raise RLV2ProvenanceError(f"Invalid tensor shape: {record.shape}")
        expected = math.prod(record.shape) * width
        if len(record.raw_bytes) != expected:
            raise RLV2ProvenanceError(
                f"Tensor byte length mismatch for {name}: expected {expected}, "
                f"got {len(record.raw_bytes)}"
            )
        metadata = {
            "byte_order": record.byte_order,
            "device": normalize_device(record.device),
            "dtype": record.dtype,
            "element_type": record.element_type,
            "logical_name": name,
            "role": record.role,
            "shape": list(record.shape),
        }
        entries.append((name, metadata, bytes(record.raw_bytes)))
    digest = hashlib.sha256(b"rl-v2-semantic-tensor-state-v1\x00")
    for _, metadata, raw_bytes in sorted(entries, key=lambda item: item[0]):
        digest.update(_frame(canonical_json_bytes(metadata)))
        digest.update(_frame(raw_bytes))
    return digest.hexdigest()


def _object(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise RLV2ProvenanceError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise RLV2ProvenanceError(f"{label} must be a list")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    missing = expected - set(value)
    extra = set(value) - expected
    if missing:
        raise RLV2ProvenanceError(f"{label} missing required fields: {sorted(missing)}")
    if extra:
        raise RLV2ProvenanceError(f"{label} contains forbidden fields: {sorted(extra)}")


def _string(value: Any, label: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise RLV2ProvenanceError(f"{label} must be a non-empty string")
    return value


def _boolean(value: Any, label: str, nullable: bool = False) -> bool | None:
    if value is None and nullable:
        return None
    if not isinstance(value, bool):
        raise RLV2ProvenanceError(f"{label} must be boolean")
    return value


def _integer(
    value: Any,
    label: str,
    nullable: bool = False,
    minimum: int = 0,
) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise RLV2ProvenanceError(f"{label} must be an integer >= {minimum}")
    return value


def _sha256(value: Any, label: str, nullable: bool = False) -> str | None:
    text = _string(value, label, nullable)
    if text is not None and not _SHA256_RE.fullmatch(text):
        raise RLV2ProvenanceError(f"{label} must be lowercase SHA-256")
    return text


def _string_list(value: Any, label: str, unique: bool = False) -> list[str]:
    result = [
        _string(item, f"{label}[{index}]") or ""
        for index, item in enumerate(_list(value, label))
    ]
    if unique and len(result) != len(set(result)):
        raise RLV2ProvenanceError(f"{label} must not contain duplicates")
    return result


def _name_value_list(value: Any, label: str) -> None:
    seen: set[str] = set()
    for index, raw in enumerate(_list(value, label)):
        item_label = f"{label}[{index}]"
        item = _object(raw, item_label)
        _exact_keys(item, {"name", "value"}, item_label)
        name = _string(item["name"], f"{item_label}.name") or ""
        if name in seen:
            raise RLV2ProvenanceError(f"Duplicate name in {label}: {name}")
        seen.add(name)
        _string(item["value"], f"{item_label}.value")


def _scan_sensitive(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _SENSITIVE_KEY_RE.search(key):
                raise RLV2ProvenanceError(f"{path}.{key}: secret-like field is forbidden")
            _scan_sensitive(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_sensitive(item, f"{path}[{index}]")
    elif isinstance(value, str):
        if _SENSITIVE_VALUE_RE.search(value) or _PRIVATE_ENDPOINT_RE.search(value):
            raise RLV2ProvenanceError(f"{path}: secret-like or private endpoint value is forbidden")


def _validate_authorization(value: Any) -> None:
    label = "authorization"
    item = _object(value, label)
    _exact_keys(item, AUTHORIZATION_BOOLEAN_FIELDS | {"phase6_selected_model"}, label)
    for field in AUTHORIZATION_BOOLEAN_FIELDS:
        if _boolean(item[field], f"{label}.{field}"):
            raise RLV2ProvenanceError(f"Execution authorization must remain false: {field}")
    if item["phase6_selected_model"] is not None:
        raise RLV2ProvenanceError("Phase 6 selected_model must remain null")


def _validate_environment(value: Any) -> None:
    label = "execution_environment"
    item = _object(value, label)
    required_strings = {
        "python_implementation",
        "python_version",
        "operating_system",
        "operating_system_release",
        "runner_identity_class",
        "cpu_architecture",
    }
    nullable_strings = {
        "runner_image",
        "cpu_model",
        "gpu_model",
        "gpu_driver_version",
        "cuda_version",
        "cudnn_version",
        "container_image_digest",
    }
    fields = required_strings | nullable_strings | {"selected_device", "environment_variables"}
    _exact_keys(item, fields, label)
    for field in required_strings:
        _string(item[field], f"{label}.{field}")
    for field in nullable_strings:
        _string(item[field], f"{label}.{field}", True)
    normalize_device(_string(item["selected_device"], f"{label}.selected_device") or "")
    _name_value_list(item["environment_variables"], f"{label}.environment_variables")


def _validate_dependencies(value: Any) -> None:
    label = "runtime_dependencies"
    item = _object(value, label)
    _exact_keys(
        item,
        {"manifest_sha256", "dynamic_installation_performed", "distributions"},
        label,
    )
    _sha256(item["manifest_sha256"], f"{label}.manifest_sha256")
    if _boolean(
        item["dynamic_installation_performed"],
        f"{label}.dynamic_installation_performed",
    ):
        raise RLV2ProvenanceError("Dynamic dependency installation must be false")
    seen: set[str] = set()
    for index, raw in enumerate(_list(item["distributions"], f"{label}.distributions")):
        row_label = f"{label}.distributions[{index}]"
        row = _object(raw, row_label)
        _exact_keys(row, {"name", "version", "artifact_sha256"}, row_label)
        name = _string(row["name"], f"{row_label}.name") or ""
        if name in seen:
            raise RLV2ProvenanceError(f"Duplicate runtime distribution: {name}")
        seen.add(name)
        _string(row["version"], f"{row_label}.version")
        _sha256(row["artifact_sha256"], f"{row_label}.artifact_sha256", True)


def _validate_code_identity(value: Any) -> str:
    label = "code_configuration_identity"
    item = _object(value, label)
    hash_fields = {
        "repository_tree_sha256",
        "base_config_sha256",
        "effective_config_sha256",
        "strategy_source_sha256",
        "model_source_sha256",
        "ppo_contract_sha256",
        "reward_action_contract_sha256",
        "feature_target_contract_sha256",
        "dataset_manifest_sha256",
    }
    fields = hash_fields | {"repository_commit_sha", "timerange", "pair_universe"}
    _exact_keys(item, fields, label)
    commit = _string(item["repository_commit_sha"], f"{label}.repository_commit_sha") or ""
    if not _GIT_SHA_RE.fullmatch(commit):
        raise RLV2ProvenanceError(
            f"{label}.repository_commit_sha must be lowercase Git SHA-1"
        )
    for field in hash_fields:
        _sha256(item[field], f"{label}.{field}")
    _string(item["timerange"], f"{label}.timerange")
    _string_list(item["pair_universe"], f"{label}.pair_universe", True)
    return str(item["dataset_manifest_sha256"])


def _validate_determinism(value: Any) -> None:
    label = "determinism"
    item = _object(value, label)
    bool_fields = {
        "torch_deterministic_algorithms",
        "torch_deterministic_warn_only",
        "cudnn_deterministic",
        "cudnn_benchmark",
    }
    integer_fields = {
        "torch_intraop_threads",
        "torch_interop_threads",
        "process_count",
        "worker_count",
    }
    fields = bool_fields | integer_fields | {
        "class",
        "conditions",
        "cuda_workspace_config",
        "blas_thread_settings",
        "multiprocessing_start_method",
        "known_nondeterminism",
    }
    _exact_keys(item, fields, label)
    category = _string(item["class"], f"{label}.class")
    if category not in DETERMINISM_CLASSES:
        raise RLV2ProvenanceError(f"Unknown determinism class: {category}")
    conditions = item["conditions"]
    if conditions is not None:
        _string_list(conditions, f"{label}.conditions")
    if category == "conditional_determinism_claimed" and not conditions:
        raise RLV2ProvenanceError("Conditional determinism requires explicit conditions")
    for field in bool_fields:
        _boolean(item[field], f"{label}.{field}", True)
    for field in integer_fields:
        _integer(item[field], f"{label}.{field}", True, 1)
    _string(item["cuda_workspace_config"], f"{label}.cuda_workspace_config", True)
    _string(
        item["multiprocessing_start_method"],
        f"{label}.multiprocessing_start_method",
        True,
    )
    _name_value_list(item["blas_thread_settings"], f"{label}.blas_thread_settings")
    _string_list(item["known_nondeterminism"], f"{label}.known_nondeterminism")


def _validate_seed_rng(value: Any) -> None:
    label = "seed_rng"
    item = _object(value, label)
    seed_fields = {"ppo_seed", "environment_seed", "action_space_seed"}
    hash_fields = {
        "python_initial_state_sha256",
        "numpy_initial_state_sha256",
        "torch_cpu_initial_state_sha256",
        "gymnasium_initial_state_sha256",
        "stable_baselines3_initial_state_sha256",
        "final_state_manifest_sha256",
    }
    fields = seed_fields | hash_fields | {
        "declared_seed",
        "cuda_initial_state_sha256",
        "initialization_order",
        "consumed_before_snapshot",
    }
    _exact_keys(item, fields, label)
    _integer(item["declared_seed"], f"{label}.declared_seed")
    for field in seed_fields:
        _integer(item[field], f"{label}.{field}", True)
    for field in hash_fields:
        _sha256(item[field], f"{label}.{field}", True)
    seen: set[str] = set()
    cuda_states = _list(
        item["cuda_initial_state_sha256"],
        f"{label}.cuda_initial_state_sha256",
    )
    for index, raw in enumerate(cuda_states):
        row_label = f"{label}.cuda_initial_state_sha256[{index}]"
        row = _object(raw, row_label)
        _exact_keys(row, {"device", "sha256"}, row_label)
        device = normalize_device(_string(row["device"], f"{row_label}.device") or "")
        if not device.startswith("cuda:") or device in seen:
            raise RLV2ProvenanceError(f"Invalid or duplicate CUDA RNG device: {device}")
        seen.add(device)
        _sha256(row["sha256"], f"{row_label}.sha256")
    _string_list(item["initialization_order"], f"{label}.initialization_order")
    _boolean(
        item["consumed_before_snapshot"],
        f"{label}.consumed_before_snapshot",
        True,
    )


def _validate_nullable_hashes(value: Any, label: str, fields: set[str]) -> None:
    item = _object(value, label)
    _exact_keys(item, fields, label)
    for field in fields:
        _sha256(item[field], f"{label}.{field}", True)


def _validate_artifacts(value: Any, label: str, model_artifact: bool) -> None:
    model_fields = {
        "logical_identity",
        "format",
        "writer_versions",
        "semantic_digest_sha256",
        "file_digest_sha256",
        "byte_size",
        "reread_verified",
    }
    evidence_fields = {"logical_identity", "sha256", "byte_size", "required", "present"}
    seen: set[str] = set()
    for index, raw in enumerate(_list(value, label)):
        row_label = f"{label}[{index}]"
        row = _object(raw, row_label)
        _exact_keys(row, model_fields if model_artifact else evidence_fields, row_label)
        identity = _string(row["logical_identity"], f"{row_label}.logical_identity") or ""
        if identity in seen:
            raise RLV2ProvenanceError(f"Duplicate logical artifact identity: {identity}")
        seen.add(identity)
        if model_artifact:
            _string(row["format"], f"{row_label}.format")
            _string_list(row["writer_versions"], f"{row_label}.writer_versions")
            _sha256(
                row["semantic_digest_sha256"],
                f"{row_label}.semantic_digest_sha256",
                True,
            )
            _sha256(
                row["file_digest_sha256"],
                f"{row_label}.file_digest_sha256",
                True,
            )
            _integer(row["byte_size"], f"{row_label}.byte_size", True)
            _boolean(row["reread_verified"], f"{row_label}.reread_verified", True)
        else:
            _sha256(row["sha256"], f"{row_label}.sha256")
            _integer(row["byte_size"], f"{row_label}.byte_size", True)
            required = _boolean(row["required"], f"{row_label}.required")
            present = _boolean(row["present"], f"{row_label}.present")
            if required and not present:
                raise RLV2ProvenanceError(f"Required artifact is absent: {identity}")


def _validate_dataset(value: Any, expected_digest: str) -> None:
    label = "dataset_manifest"
    item = _object(value, label)
    fields = {
        "manifest_sha256",
        "source_identity",
        "cache_restore_used",
        "consumed_historical_oos_accessed",
        "protected_final_holdout_accessed",
    }
    _exact_keys(item, fields, label)
    if _sha256(item["manifest_sha256"], f"{label}.manifest_sha256") != expected_digest:
        raise RLV2ProvenanceError(
            "Dataset manifest identity does not match code/config binding"
        )
    _string(item["source_identity"], f"{label}.source_identity")
    if _boolean(item["cache_restore_used"], f"{label}.cache_restore_used"):
        raise RLV2ProvenanceError("Cache restore must be false")
    if _boolean(
        item["consumed_historical_oos_accessed"],
        f"{label}.consumed_historical_oos_accessed",
    ):
        raise RLV2ProvenanceError("Consumed historical OOS access is forbidden")
    if _boolean(
        item["protected_final_holdout_accessed"],
        f"{label}.protected_final_holdout_accessed",
    ):
        raise RLV2ProvenanceError("Protected final holdout access is forbidden")


def _path_value(value: Mapping[str, Any], path: str) -> Any:
    current: Any = value
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            raise RLV2ProvenanceError(
                f"Optional field path is structurally missing: {path}"
            )
        current = current[segment]
    return current


def collect_missing_optional_fields(manifest: Mapping[str, Any]) -> list[str]:
    """Return sorted nullable schema paths whose explicit value is null."""

    return sorted(
        path for path in OPTIONAL_FIELD_PATHS if _path_value(manifest, path) is None
    )


def _validate_structure(manifest: Mapping[str, Any]) -> None:
    fields = {
        "schema_version",
        "manifest_id",
        "classification",
        "authorization",
        "execution_environment",
        "runtime_dependencies",
        "code_configuration_identity",
        "determinism",
        "seed_rng",
        "policy_state",
        "optimizer_state",
        "serialized_model_artifacts",
        "dataset_manifest",
        "diagnostic_artifacts",
        "final_evidence_manifest",
        "missing_optional_fields",
        "self_hash_sha256",
    }
    _exact_keys(manifest, fields, "manifest")
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise RLV2ProvenanceError(
            f"Unsupported schema_version: {manifest['schema_version']}"
        )
    manifest_id = _string(manifest["manifest_id"], "manifest.manifest_id") or ""
    if not _ID_RE.fullmatch(manifest_id):
        raise RLV2ProvenanceError("manifest.manifest_id has invalid syntax")
    if manifest["classification"] not in PROVENANCE_CLASSIFICATIONS:
        raise RLV2ProvenanceError(
            f"Unknown classification: {manifest['classification']}"
        )
    _validate_authorization(manifest["authorization"])
    _validate_environment(manifest["execution_environment"])
    _validate_dependencies(manifest["runtime_dependencies"])
    dataset_digest = _validate_code_identity(manifest["code_configuration_identity"])
    _validate_determinism(manifest["determinism"])
    _validate_seed_rng(manifest["seed_rng"])
    _validate_nullable_hashes(
        manifest["policy_state"],
        "policy_state",
        {
            "initial_digest_sha256",
            "final_digest_sha256",
            "trainable_parameters_digest_sha256",
            "buffers_digest_sha256",
        },
    )
    _validate_nullable_hashes(
        manifest["optimizer_state"],
        "optimizer_state",
        {"state_digest_sha256"},
    )
    model_artifacts = _object(
        manifest["serialized_model_artifacts"],
        "serialized_model_artifacts",
    )
    _exact_keys(model_artifacts, {"artifacts"}, "serialized_model_artifacts")
    _validate_artifacts(
        model_artifacts["artifacts"],
        "serialized_model_artifacts.artifacts",
        True,
    )
    _validate_dataset(manifest["dataset_manifest"], dataset_digest)
    for section, field in (
        ("diagnostic_artifacts", "artifacts"),
        ("final_evidence_manifest", "logical_artifacts"),
    ):
        item = _object(manifest[section], section)
        _exact_keys(item, {field}, section)
        _validate_artifacts(item[field], f"{section}.{field}", False)
    missing = _string_list(
        manifest["missing_optional_fields"],
        "missing_optional_fields",
        True,
    )
    expected_missing = collect_missing_optional_fields(manifest)
    if missing != expected_missing:
        raise RLV2ProvenanceError(
            f"missing_optional_fields must equal explicit null paths: {expected_missing}"
        )
    _sha256(manifest["self_hash_sha256"], "manifest.self_hash_sha256")
    _scan_sensitive(manifest)
    _canonical_value(manifest)


def compute_manifest_self_hash(manifest: Mapping[str, Any]) -> str:
    """Hash every manifest field except the self-hash field itself."""

    payload = deepcopy(dict(manifest))
    if "self_hash_sha256" not in payload:
        raise RLV2ProvenanceError("Manifest self_hash_sha256 field is required")
    payload.pop("self_hash_sha256")
    return canonical_sha256(payload)


def finalize_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Populate explicit missing paths and a deterministic self-hash."""

    result = deepcopy(dict(manifest))
    required_helpers = {"missing_optional_fields", "self_hash_sha256"}
    if not required_helpers <= set(result):
        raise RLV2ProvenanceError(
            "Manifest requires missing_optional_fields and self_hash_sha256"
        )
    result["missing_optional_fields"] = collect_missing_optional_fields(result)
    result["self_hash_sha256"] = "0" * 64
    _validate_structure(result)
    result["self_hash_sha256"] = compute_manifest_self_hash(result)
    return result


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate schema, boundaries, secrets, explicit nulls and self-hash."""

    item = _object(manifest, "manifest")
    _scan_sensitive(item)
    _validate_structure(item)
    expected = compute_manifest_self_hash(item)
    if item["self_hash_sha256"] != expected:
        raise RLV2ProvenanceError(
            f"Manifest self-hash mismatch: expected {expected}, "
            f"got {item['self_hash_sha256']}"
        )
