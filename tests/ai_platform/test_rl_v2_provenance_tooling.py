from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from ai_platform.provenance.rl_v2 import (
    RLV2ProvenanceError,
    TensorRecord,
    canonical_json_bytes,
    finalize_manifest,
    semantic_tensor_state_digest,
    validate_manifest,
)


SHA = "a" * 64
OTHER_SHA = "b" * 64


def tensor(
    *,
    name: str = "policy.layer.weight",
    role: str = "parameter",
    dtype: str = "float32",
    shape: tuple[int, ...] = (2,),
    device: str = "cpu",
    raw_bytes: bytes = b"\x00\x01\x02\x03\x04\x05\x06\x07",
) -> TensorRecord:
    return TensorRecord(
        logical_name=name,
        role=role,
        element_type="dense_tensor",
        dtype=dtype,
        shape=shape,
        device=device,
        byte_order="little",
        raw_bytes=raw_bytes,
    )


def manifest() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "manifest_id": "rl-v2-provenance-synthetic-v1",
        "classification": "internal_restricted",
        "authorization": {
            "model_training": False,
            "inference": False,
            "backtest": False,
            "replay": False,
            "seed_rerun": False,
            "market_data_access": False,
            "canonical_request_creation": False,
            "execution_workflow": False,
            "ranking": False,
            "selection": False,
            "promotion": False,
            "dry_run": False,
            "shadow": False,
            "live": False,
            "consumed_historical_oos_access": False,
            "protected_final_holdout_access": False,
            "phase6_changed": False,
            "phase6_selected_model": None,
        },
        "execution_environment": {
            "python_implementation": "CPython",
            "python_version": "3.12.0",
            "operating_system": "Linux",
            "operating_system_release": "synthetic",
            "runner_image": None,
            "runner_identity_class": "synthetic_test",
            "cpu_architecture": "x86_64",
            "cpu_model": None,
            "gpu_model": None,
            "gpu_driver_version": None,
            "cuda_version": None,
            "cudnn_version": None,
            "selected_device": "CPU:0",
            "container_image_digest": None,
            "environment_variables": [{"name": "PYTHONHASHSEED", "value": "0"}],
        },
        "runtime_dependencies": {
            "manifest_sha256": SHA,
            "dynamic_installation_performed": False,
            "distributions": [
                {"name": "python", "version": "3.12.0", "artifact_sha256": None},
            ],
        },
        "code_configuration_identity": {
            "repository_commit_sha": "c" * 40,
            "repository_tree_sha256": SHA,
            "base_config_sha256": SHA,
            "effective_config_sha256": SHA,
            "strategy_source_sha256": SHA,
            "model_source_sha256": SHA,
            "ppo_contract_sha256": SHA,
            "reward_action_contract_sha256": SHA,
            "feature_target_contract_sha256": SHA,
            "dataset_manifest_sha256": OTHER_SHA,
            "timerange": "synthetic-only",
            "pair_universe": ["SYNTHETIC/A", "SYNTHETIC/B"],
        },
        "determinism": {
            "class": "no_determinism_guarantee",
            "conditions": None,
            "torch_deterministic_algorithms": None,
            "torch_deterministic_warn_only": None,
            "cudnn_deterministic": None,
            "cudnn_benchmark": None,
            "cuda_workspace_config": None,
            "torch_intraop_threads": None,
            "torch_interop_threads": None,
            "blas_thread_settings": [],
            "multiprocessing_start_method": None,
            "process_count": None,
            "worker_count": None,
            "known_nondeterminism": ["not_evaluated_by_inert_tooling"],
        },
        "seed_rng": {
            "declared_seed": 7,
            "ppo_seed": None,
            "environment_seed": None,
            "action_space_seed": None,
            "python_initial_state_sha256": None,
            "numpy_initial_state_sha256": None,
            "torch_cpu_initial_state_sha256": None,
            "cuda_initial_state_sha256": [],
            "gymnasium_initial_state_sha256": None,
            "stable_baselines3_initial_state_sha256": None,
            "initialization_order": [],
            "consumed_before_snapshot": None,
            "final_state_manifest_sha256": None,
        },
        "policy_state": {
            "initial_digest_sha256": None,
            "final_digest_sha256": None,
            "trainable_parameters_digest_sha256": None,
            "buffers_digest_sha256": None,
        },
        "optimizer_state": {"state_digest_sha256": None},
        "serialized_model_artifacts": {"artifacts": []},
        "dataset_manifest": {
            "manifest_sha256": OTHER_SHA,
            "source_identity": "synthetic-unit-test-only",
            "cache_restore_used": False,
            "consumed_historical_oos_accessed": False,
            "protected_final_holdout_accessed": False,
        },
        "diagnostic_artifacts": {
            "artifacts": [
                {
                    "logical_identity": "diagnostics/synthetic",
                    "sha256": SHA,
                    "byte_size": 1,
                    "required": True,
                    "present": True,
                },
            ],
        },
        "final_evidence_manifest": {
            "logical_artifacts": [
                {
                    "logical_identity": "evidence/synthetic",
                    "sha256": OTHER_SHA,
                    "byte_size": 1,
                    "required": True,
                    "present": True,
                },
            ],
        },
        "missing_optional_fields": [],
        "self_hash_sha256": "0" * 64,
    }
    return finalize_manifest(payload)


def test_state_digest_ignores_input_order() -> None:
    first = tensor(name="policy.a")
    second = tensor(name="policy.b", raw_bytes=b"\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f")
    assert semantic_tensor_state_digest([first, second]) == semantic_tensor_state_digest(
        [second, first]
    )


def test_state_digest_changes_with_logical_name() -> None:
    assert semantic_tensor_state_digest([tensor()]) != semantic_tensor_state_digest(
        [tensor(name="policy.layer.bias")]
    )


def test_state_digest_changes_with_dtype() -> None:
    assert semantic_tensor_state_digest([tensor(dtype="float32")]) != semantic_tensor_state_digest(
        [tensor(dtype="int32")]
    )


def test_state_digest_changes_with_shape() -> None:
    assert semantic_tensor_state_digest([tensor(shape=(1, 2))]) != semantic_tensor_state_digest(
        [tensor(shape=(2, 1))]
    )


def test_state_digest_changes_with_one_byte() -> None:
    assert semantic_tensor_state_digest([tensor()]) != semantic_tensor_state_digest(
        [tensor(raw_bytes=b"\x00\x01\x02\x03\x04\x05\x06\x08")]
    )


def test_device_normalization_is_deterministic() -> None:
    assert semantic_tensor_state_digest([tensor(device="GPU")]) == semantic_tensor_state_digest(
        [tensor(device="cuda:0")]
    )


def test_state_role_changes_digest() -> None:
    parameter = semantic_tensor_state_digest([tensor(role="parameter")])
    buffer = semantic_tensor_state_digest([tensor(role="buffer")])
    optimizer = semantic_tensor_state_digest([tensor(role="optimizer_state")])
    assert len({parameter, buffer, optimizer}) == 3


def test_duplicate_tensor_identity_is_rejected() -> None:
    with pytest.raises(RLV2ProvenanceError, match="Duplicate logical tensor identity"):
        semantic_tensor_state_digest([tensor(), tensor()])


def test_tensor_byte_length_mismatch_is_rejected() -> None:
    with pytest.raises(RLV2ProvenanceError, match="byte length mismatch"):
        semantic_tensor_state_digest([tensor(raw_bytes=b"\x00")])


def test_finite_float_is_rejected_as_noncanonical() -> None:
    with pytest.raises(RLV2ProvenanceError, match="JSON floats are forbidden"):
        canonical_json_bytes({"value": 1.5})


def test_execution_authorization_is_rejected() -> None:
    payload = manifest()
    authorization = payload["authorization"]
    assert isinstance(authorization, dict)
    authorization["model_training"] = True
    with pytest.raises(RLV2ProvenanceError, match="must remain false"):
        finalize_manifest(payload)


def test_consumed_oos_and_holdout_access_are_rejected() -> None:
    for field in (
        "consumed_historical_oos_accessed",
        "protected_final_holdout_accessed",
    ):
        payload = manifest()
        dataset = payload["dataset_manifest"]
        assert isinstance(dataset, dict)
        dataset[field] = True
        with pytest.raises(RLV2ProvenanceError, match="access is forbidden"):
            finalize_manifest(payload)


def test_explicit_missing_optional_fields_are_enforced() -> None:
    payload = manifest()
    missing = payload["missing_optional_fields"]
    assert isinstance(missing, list)
    missing.pop()
    with pytest.raises(RLV2ProvenanceError, match="missing_optional_fields"):
        validate_manifest(payload)


def test_duplicate_logical_artifact_identity_is_rejected() -> None:
    payload = manifest()
    evidence = payload["final_evidence_manifest"]
    assert isinstance(evidence, dict)
    artifacts = evidence["logical_artifacts"]
    assert isinstance(artifacts, list)
    artifacts.append(deepcopy(artifacts[0]))
    with pytest.raises(RLV2ProvenanceError, match="Duplicate logical artifact identity"):
        finalize_manifest(payload)


def test_manifest_tampering_is_detected() -> None:
    payload = manifest()
    validate_manifest(payload)
    tampered = deepcopy(payload)
    tampered["manifest_id"] = "rl-v2-provenance-tampered-v1"
    with pytest.raises(RLV2ProvenanceError, match="self-hash mismatch"):
        validate_manifest(tampered)


def test_secret_like_field_is_rejected() -> None:
    payload = manifest()
    environment = payload["execution_environment"]
    assert isinstance(environment, dict)
    environment["api_key"] = "not-a-real-credential"
    with pytest.raises(RLV2ProvenanceError, match="secret-like"):
        validate_manifest(payload)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_numbers_are_rejected(value: float) -> None:
    with pytest.raises(RLV2ProvenanceError, match="non-finite"):
        canonical_json_bytes({"value": value})


def test_missing_required_field_is_rejected() -> None:
    payload = manifest()
    payload.pop("dataset_manifest")
    with pytest.raises(RLV2ProvenanceError, match="missing required fields"):
        validate_manifest(payload)


def test_forbidden_extra_field_is_rejected() -> None:
    payload = manifest()
    payload["unexpected"] = None
    with pytest.raises(RLV2ProvenanceError, match="forbidden fields"):
        validate_manifest(payload)


def test_unknown_determinism_class_is_rejected() -> None:
    payload = manifest()
    determinism = payload["determinism"]
    assert isinstance(determinism, dict)
    determinism["class"] = "magic_determinism"
    with pytest.raises(RLV2ProvenanceError, match="Unknown determinism class"):
        finalize_manifest(payload)


def test_module_has_no_rl_runtime_imports_or_data_io() -> None:
    source_path = Path(__file__).parents[2] / "ai_platform/provenance/rl_v2.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported_roots.isdisjoint(
        {"torch", "stable_baselines3", "gymnasium", "freqtrade", "numpy", "pandas"}
    )
    assert "read_bytes(" not in source
    assert "read_text(" not in source
    assert "urlopen(" not in source
    assert "requests" not in source
