"""Inert, standard-library provenance primitives for future RL-v2 experiments."""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


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

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_GIT_SHA = re.compile(r"[0-9a-f]{40}\Z")
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,255}\Z")
_DEVICE = re.compile(r"(cuda|xpu):([0-9]+)\Z")
_SECRET_KEY = re.compile(
    r"(?:^|_)(?:api_?key|secret|token|password|passwd|cookie|authorization_?header|"
    r"private_?endpoint|credential(?:s|_material)?)(?:$|_)",
    re.IGNORECASE,
)
_SECRET_VALUE = re.compile(
    r"(?:^|\b)(?:bearer\s+|basic\s+|sk-[a-z0-9_-]{8,}|api[_-]?key\s*[:=]|"
    r"password\s*[:=]|access[_-]?token\s*[:=])",
    re.IGNORECASE,
)
_PRIVATE_ENDPOINT = re.compile(
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


def _json_value(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, bool | str):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        qualifier = "non-finite " if not math.isfinite(value) else ""
        raise RLV2ProvenanceError(f"{path}: {qualifier}JSON floats are forbidden")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise RLV2ProvenanceError(f"{path}: JSON object keys must be strings")
            _json_value(item, f"{path}.{key}")
        return
    raise RLV2ProvenanceError(f"{path}: unsupported canonical JSON type {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize canonical UTF-8 JSON with sorted keys and exactly one trailing LF."""

    _json_value(value)
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()


def canonical_sha256(value: Any) -> str:
    """Return SHA-256 over canonical JSON bytes."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def normalize_device(value: str) -> str:
    """Normalize dependency-neutral device labels."""

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
    if normalized == "mps" or _DEVICE.fullmatch(normalized):
        return normalized
    raise RLV2ProvenanceError(f"Unsupported device label: {value}")


def _frame(data: bytes) -> bytes:
    return len(data).to_bytes(8, "big") + data


def semantic_tensor_state_digest(records: Iterable[TensorRecord]) -> str:
    """Hash semantic tensor state without file or archive metadata."""

    validated: list[tuple[str, dict[str, Any], bytes]] = []
    seen: set[str] = set()
    for record in records:
        name = record.logical_name
        if not isinstance(name, str) or not _IDENTIFIER.fullmatch(name):
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
        if record.dtype not in {"bool", "uint8", "int8"} and record.byte_order == "not_applicable":
            raise RLV2ProvenanceError("Multi-byte tensor dtype requires explicit byte order")
        if any(
            isinstance(size, bool) or not isinstance(size, int) or size < 0
            for size in record.shape
        ):
            raise RLV2ProvenanceError(f"Invalid tensor shape: {record.shape}")
        elements = math.prod(record.shape)
        if len(record.raw_bytes) != elements * width:
            raise RLV2ProvenanceError(
                f"Tensor byte length mismatch for {name}: expected {elements * width}, "
                f"got {len(record.raw_bytes)}"
            )
        metadata = {
            "logical_name": name,
            "role": record.role,
            "element_type": record.element_type,
            "dtype": record.dtype,
            "shape": list(record.shape),
            "device": normalize_device(record.device),
            "byte_order": record.byte_order,
        }
        validated.append((name, metadata, bytes(record.raw_bytes)))
    digest = hashlib.sha256(b"rl-v2-semantic-tensor-state-v1\x00")
    for _, metadata, raw in sorted(validated, key=lambda item: item[0]):
        digest.update(_frame(canonical_json_bytes(metadata)))
        digest.update(_frame(raw))
    return digest.hexdigest()


def _map(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise RLV2ProvenanceError(f"{label} must be an object")
    return value


def _seq(value: Any, label: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise RLV2ProvenanceError(f"{label} must be a list")
    return value


def _keys(value: Mapping[str, Any], expected: Iterable[str], label: str) -> None:
    expected_set = set(expected)
    missing = expected_set - set(value)
    extra = set(value) - expected_set
    if missing:
        raise RLV2ProvenanceError(f"{label} missing required fields: {sorted(missing)}")
    if extra:
        raise RLV2ProvenanceError(f"{label} contains forbidden fields: {sorted(extra)}")


def _str(value: Any, label: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise RLV2ProvenanceError(f"{label} must be a non-empty string")
    return value


def _bool(value: Any, label: str, nullable: bool = False) -> bool | None:
    if value is None and nullable:
        return None
    if not isinstance(value, bool):
        raise RLV2ProvenanceError(f"{label} must be boolean")
    return value


def _int(value: Any, label: str, nullable: bool = False, minimum: int = 0) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise RLV2ProvenanceError(f"{label} must be an integer >= {minimum}")
    return value


def _sha(value: Any, label: str, nullable: bool = False) -> str | None:
    text = _str(value, label, nullable)
    if text is not None and not _SHA.fullmatch(text):
        raise RLV2ProvenanceError(f"{label} must be lowercase SHA-256")
    return text


def _strings(value: Any, label: str, unique: bool = False) -> list[str]:
    result = [
        _str(item, f"{label}[{index}]") or "" for index, item in enumerate(_seq(value, label))
    ]
    if unique and len(result) != len(set(result)):
        raise RLV2ProvenanceError(f"{label} must not contain duplicates")
    return result


def _name_values(value: Any, label: str) -> None:
    seen: set[str] = set()
    for index, raw in enumerate(_seq(value, label)):
        item_label = f"{label}[{index}]"
        item = _map(raw, item_label)
        _keys(item, {"name", "value"}, item_label)
        name = _str(item["name"], f"{item_label}.name") or ""
        if name in seen:
            raise RLV2ProvenanceError(f"Duplicate name in {label}: {name}")
        seen.add(name)
        _str(item["value"], f"{item_label}.value")


def _secret_scan(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _SECRET_KEY.search(key):
                raise RLV2ProvenanceError(f"{path}.{key}: secret-like field is forbidden")
            _secret_scan(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _secret_scan(item, f"{path}[{index}]")
    elif isinstance(value, str) and (
        _SECRET_VALUE.search(value) or _PRIVATE_ENDPOINT.search(value)
    ):
        raise RLV2ProvenanceError(f"{path}: secret-like or private endpoint value is forbidden")


def _artifact_list(value: Any, label: str, model: bool = False) -> None:
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
    for index, raw in enumerate(_seq(value, label)):
        item_label = f"{label}[{index}]"
        item = _map(raw, item_label)
        _keys(item, model_fields if model else evidence_fields, item_label)
        identity = _str(item["logical_identity"], f"{item_label}.logical_identity") or ""
        if identity in seen:
            raise RLV2ProvenanceError(f"Duplicate logical artifact identity: {identity}")
        seen.add(identity)
        if model:
            _str(item["format"], f"{item_label}.format")
            _strings(item["writer_versions"], f"{item_label}.writer_versions")
            _sha(
                item["semantic_digest_sha256"],
                f"{item_label}.semantic_digest_sha256",
                True,
            )
            _sha(item["file_digest_sha256"], f"{item_label}.file_digest_sha256", True)
            _int(item["byte_size"], f"{item_label}.byte_size", True)
            _bool(item["reread_verified"], f"{item_label}.reread_verified", True)
        else:
            _sha(item["sha256"], f"{item_label}.sha256")
            _int(item["byte_size"], f"{item_label}.byte_size", True)
            required = _bool(item["required"], f"{item_label}.required")
            present = _bool(item["present"], f"{item_label}.present")
            if required and not present:
                raise RLV2ProvenanceError(f"Required artifact is absent: {identity}")


def _environment(value: Any) -> None:
    label = "execution_environment"
    item = _map(value, label)
    required = {
        "python_implementation",
        "python_version",
        "operating_system",
        "operating_system_release",
        "runner_image",
        "runner_identity_class",
        "cpu_architecture",
        "cpu_model",
        "gpu_model",
        "gpu_driver_version",
        "cuda_version",
        "cudnn_version",
        "selected_device",
        "container_image_digest",
        "environment_variables",
    }
    _keys(item, required, label)
    for field in {
        "python_implementation",
        "python_version",
        "operating_system",
        "operating_system_release",
        "runner_identity_class",
        "cpu_architecture",
    }:
        _str(item[field], f"{label}.{field}")
    nullable = required - {
        "python_implementation",
        "python_version",
        "operating_system",
        "operating_system_release",
        "runner_identity_class",
        "cpu_architecture",
        "selected_device",
        "environment_variables",
    }
    for field in nullable:
        _str(item[field], f"{label}.{field}", True)
    normalize_device(_str(item["selected_device"], f"{label}.selected_device") or "")
    _name_values(item["environment_variables"], f"{label}.environment_variables")


def _dependencies(value: Any) -> None:
    label = "runtime_dependencies"
    item = _map(value, label)
    _keys(item, {"manifest_sha256", "dynamic_installation_performed", "distributions"}, label)
    _sha(item["manifest_sha256"], f"{label}.manifest_sha256")
    if _bool(item["dynamic_installation_performed"], f"{label}.dynamic_installation_performed"):
        raise RLV2ProvenanceError("Dynamic dependency installation must be false")
    seen: set[str] = set()
    for index, raw in enumerate(_seq(item["distributions"], f"{label}.distributions")):
        row_label = f"{label}.distributions[{index}]"
        row = _map(raw, row_label)
        _keys(row, {"name", "version", "artifact_sha256"}, row_label)
        name = _str(row["name"], f"{row_label}.name") or ""
        if name in seen:
            raise RLV2ProvenanceError(f"Duplicate runtime distribution: {name}")
        seen.add(name)
        _str(row["version"], f"{row_label}.version")
        _sha(row["artifact_sha256"], f"{row_label}.artifact_sha256", True)


def _code_identity(value: Any) -> str:
    label = "code_configuration_identity"
    item = _map(value, label)
    fields = {
        "repository_commit_sha",
        "repository_tree_sha256",
        "base_config_sha256",
        "effective_config_sha256",
        "strategy_source_sha256",
        "model_source_sha256",
        "ppo_contract_sha256",
        "reward_action_contract_sha256",
        "feature_target_contract_sha256",
        "dataset_manifest_sha256",
        "timerange",
        "pair_universe",
    }
    _keys(item, fields, label)
    commit = _str(item["repository_commit_sha"], f"{label}.repository_commit_sha") or ""
    if not _GIT_SHA.fullmatch(commit):
        raise RLV2ProvenanceError(f"{label}.repository_commit_sha must be lowercase Git SHA-1")
    for field in fields - {"repository_commit_sha", "timerange", "pair_universe"}:
        _sha(item[field], f"{label}.{field}")
    _str(item["timerange"], f"{label}.timerange")
    _strings(item["pair_universe"], f"{label}.pair_universe", True)
    return str(item["dataset_manifest_sha256"])


def _determinism(value: Any) -> None:
    label = "determinism"
    item = _map(value, label)
    fields = {
        "class",
        "conditions",
        "torch_deterministic_algorithms",
        "torch_deterministic_warn_only",
        "cudnn_deterministic",
        "cudnn_benchmark",
        "cuda_workspace_config",
        "torch_intraop_threads",
        "torch_interop_threads",
        "blas_thread_settings",
        "multiprocessing_start_method",
        "process_count",
        "worker_count",
        "known_nondeterminism",
    }
    _keys(item, fields, label)
    category = _str(item["class"], f"{label}.class")
    if category not in DETERMINISM_CLASSES:
        raise RLV2ProvenanceError(f"Unknown determinism class: {category}")
    conditions = item["conditions"]
    if conditions is not None:
        _strings(conditions, f"{label}.conditions")
    if category == "conditional_determinism_claimed" and not conditions:
        raise RLV2ProvenanceError("Conditional determinism requires explicit conditions")
    for field in {
        "torch_deterministic_algorithms",
        "torch_deterministic_warn_only",
        "cudnn_deterministic",
        "cudnn_benchmark",
    }:
        _bool(item[field], f"{label}.{field}", True)
    for field in {
        "torch_intraop_threads",
        "torch_interop_threads",
        "process_count",
        "worker_count",
    }:
        _int(item[field], f"{label}.{field}", True, 1)
    _str(item["cuda_workspace_config"], f"{label}.cuda_workspace_config", True)
    _str(
        item["multiprocessing_start_method"],
        f"{label}.multiprocessing_start_method",
        True,
    )
    _name_values(item["blas_thread_settings"], f"{label}.blas_thread_settings")
    _strings(item["known_nondeterminism"], f"{label}.known_nondeterminism")


def _seed_rng(value: Any) -> None:
    label = "seed_rng"
    item = _map(value, label)
    fields = {
        "declared_seed",
        "ppo_seed",
        "environment_seed",
        "action_space_seed",
        "python_initial_state_sha256",
        "numpy_initial_state_sha256",
        "torch_cpu_initial_state_sha256",
        "cuda_initial_state_sha256",
        "gymnasium_initial_state_sha256",
        "stable_baselines3_initial_state_sha256",
        "initialization_order",
        "consumed_before_snapshot",
        "final_state_manifest_sha256",
    }
    _keys(item, fields, label)
    _int(item["declared_seed"], f"{label}.declared_seed")
    for field in {"ppo_seed", "environment_seed", "action_space_seed"}:
        _int(item[field], f"{label}.{field}", True)
    hash_fields = fields - {
        "declared_seed",
        "ppo_seed",
        "environment_seed",
        "action_space_seed",
        "cuda_initial_state_sha256",
        "initialization_order",
        "consumed_before_snapshot",
    }
    for field in hash_fields:
        _sha(item[field], f"{label}.{field}", True)
    seen: set[str] = set()
    cuda_states = _seq(
        item["cuda_initial_state_sha256"],
        f"{label}.cuda_initial_state_sha256",
    )
    for index, raw in enumerate(cuda_states):
        row_label = f"{label}.cuda_initial_state_sha256[{index}]"
        row = _map(raw, row_label)
        _keys(row, {"device", "sha256"}, row_label)
        device = normalize_device(_str(row["device"], f"{row_label}.device") or "")
        if not device.startswith("cuda:") or device in seen:
            raise RLV2ProvenanceError(f"Invalid or duplicate CUDA RNG device: {device}")
        seen.add(device)
        _sha(row["sha256"], f"{row_label}.sha256")
    _strings(item["initialization_order"], f"{label}.initialization_order")
    _bool(item["consumed_before_snapshot"], f"{label}.consumed_before_snapshot", True)


def _nullable_hash_object(value: Any, label: str, fields: set[str]) -> None:
    item = _map(value, label)
    _keys(item, fields, label)
    for field in fields:
        _sha(item[field], f"{label}.{field}", True)


def _dataset(value: Any, expected_digest: str) -> None:
    label = "dataset_manifest"
    item = _map(value, label)
    fields = {
        "manifest_sha256",
        "source_identity",
        "cache_restore_used",
        "consumed_historical_oos_accessed",
        "protected_final_holdout_accessed",
    }
    _keys(item, fields, label)
    if _sha(item["manifest_sha256"], f"{label}.manifest_sha256") != expected_digest:
        raise RLV2ProvenanceError("Dataset manifest identity does not match code/config binding")
    _str(item["source_identity"], f"{label}.source_identity")
    if _bool(item["cache_restore_used"], f"{label}.cache_restore_used"):
        raise RLV2ProvenanceError("Cache restore must be false")
    if _bool(
        item["consumed_historical_oos_accessed"],
        f"{label}.consumed_historical_oos_accessed",
    ):
        raise RLV2ProvenanceError("Consumed historical OOS access is forbidden")
    if _bool(
        item["protected_final_holdout_accessed"],
        f"{label}.protected_final_holdout_accessed",
    ):
        raise RLV2ProvenanceError("Protected final holdout access is forbidden")


def _authorization(value: Any) -> None:
    label = "authorization"
    item = _map(value, label)
    fields = AUTHORIZATION_BOOLEAN_FIELDS | {"phase6_selected_model"}
    _keys(item, fields, label)
    for field in AUTHORIZATION_BOOLEAN_FIELDS:
        if _bool(item[field], f"{label}.{field}"):
            raise RLV2ProvenanceError(f"Execution authorization must remain false: {field}")
    if item["phase6_selected_model"] is not None:
        raise RLV2ProvenanceError("Phase 6 selected_model must remain null")


def _at_path(value: Mapping[str, Any], path: str) -> Any:
    current: Any = value
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            raise RLV2ProvenanceError(f"Optional field path is structurally missing: {path}")
        current = current[segment]
    return current


def collect_missing_optional_fields(manifest: Mapping[str, Any]) -> list[str]:
    """Return sorted nullable schema paths whose explicit value is null."""

    return sorted(path for path in OPTIONAL_FIELD_PATHS if _at_path(manifest, path) is None)


def _structure(manifest: Mapping[str, Any]) -> None:
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
    _keys(manifest, fields, "manifest")
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise RLV2ProvenanceError(f"Unsupported schema_version: {manifest['schema_version']}")
    _str(manifest["manifest_id"], "manifest.manifest_id")
    if manifest["classification"] not in PROVENANCE_CLASSIFICATIONS:
        raise RLV2ProvenanceError(f"Unknown classification: {manifest['classification']}")
    _authorization(manifest["authorization"])
    _environment(manifest["execution_environment"])
    _dependencies(manifest["runtime_dependencies"])
    dataset_digest = _code_identity(manifest["code_configuration_identity"])
    _determinism(manifest["determinism"])
    _seed_rng(manifest["seed_rng"])
    _nullable_hash_object(
        manifest["policy_state"],
        "policy_state",
        {
            "initial_digest_sha256",
            "final_digest_sha256",
            "trainable_parameters_digest_sha256",
            "buffers_digest_sha256",
        },
    )
    _nullable_hash_object(
        manifest["optimizer_state"],
        "optimizer_state",
        {"state_digest_sha256"},
    )
    model_artifacts = _map(
        manifest["serialized_model_artifacts"],
        "serialized_model_artifacts",
    )
    _keys(model_artifacts, {"artifacts"}, "serialized_model_artifacts")
    _artifact_list(
        model_artifacts["artifacts"],
        "serialized_model_artifacts.artifacts",
        True,
    )
    _dataset(manifest["dataset_manifest"], dataset_digest)
    for section, field in (
        ("diagnostic_artifacts", "artifacts"),
        ("final_evidence_manifest", "logical_artifacts"),
    ):
        item = _map(manifest[section], section)
        _keys(item, {field}, section)
        _artifact_list(item[field], f"{section}.{field}")
    missing = _strings(
        manifest["missing_optional_fields"],
        "missing_optional_fields",
        True,
    )
    expected_missing = collect_missing_optional_fields(manifest)
    if missing != expected_missing:
        raise RLV2ProvenanceError(
            f"missing_optional_fields must equal explicit null paths: {expected_missing}"
        )
    _sha(manifest["self_hash_sha256"], "manifest.self_hash_sha256")
    _secret_scan(manifest)
    _json_value(manifest)


def compute_manifest_self_hash(manifest: Mapping[str, Any]) -> str:
    """Hash every manifest field except the self-hash field itself."""

    payload = deepcopy(dict(manifest))
    if "self_hash_sha256" not in payload:
        raise RLV2ProvenanceError("Manifest self_hash_sha256 field is required")
    payload.pop("self_hash_sha256")
    return canonical_sha256(payload)


def finalize_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Populate explicit missing fields and deterministic self-hash."""

    result = deepcopy(dict(manifest))
    if "missing_optional_fields" not in result or "self_hash_sha256" not in result:
        raise RLV2ProvenanceError(
            "Manifest requires missing_optional_fields and self_hash_sha256"
        )
    result["missing_optional_fields"] = collect_missing_optional_fields(result)
    result["self_hash_sha256"] = "0" * 64
    _structure(result)
    result["self_hash_sha256"] = compute_manifest_self_hash(result)
    return result


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate schema, authorization, secrets, explicit nulls and self-hash."""

    item = _map(manifest, "manifest")
    _secret_scan(item)
    _structure(item)
    expected = compute_manifest_self_hash(item)
    if item["self_hash_sha256"] != expected:
        raise RLV2ProvenanceError(
            f"Manifest self-hash mismatch: expected {expected}, "
            f"got {item['self_hash_sha256']}"
        )
