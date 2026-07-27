from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ai_platform.provenance import (
    RLV2ProvenanceError,
    assemble_model_state_provenance_manifest,
    canonical_json_bytes,
    validate_manifest,
)


PARAMETER_SHA = "a" * 64
BUFFER_SHA = "b" * 64
OPTIMIZER_SHA = "c" * 64
ALTERNATE_SHA = "d" * 64
DATASET_SHA = "e" * 64


def manifest_draft() -> dict[str, object]:
    return {
        "schema_version": 1,
        "manifest_id": "rl-v2-model-state-assembler-synthetic-v1",
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
            "selected_device": "cpu",
            "container_image_digest": None,
            "environment_variables": [{"name": "PYTHONHASHSEED", "value": "0"}],
        },
        "runtime_dependencies": {
            "manifest_sha256": ALTERNATE_SHA,
            "dynamic_installation_performed": False,
            "distributions": [],
        },
        "code_configuration_identity": {
            "repository_commit_sha": "f" * 40,
            "repository_tree_sha256": ALTERNATE_SHA,
            "base_config_sha256": ALTERNATE_SHA,
            "effective_config_sha256": ALTERNATE_SHA,
            "strategy_source_sha256": ALTERNATE_SHA,
            "model_source_sha256": ALTERNATE_SHA,
            "ppo_contract_sha256": ALTERNATE_SHA,
            "reward_action_contract_sha256": ALTERNATE_SHA,
            "feature_target_contract_sha256": ALTERNATE_SHA,
            "dataset_manifest_sha256": DATASET_SHA,
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
            "manifest_sha256": DATASET_SHA,
            "source_identity": "synthetic-unit-test-only",
            "cache_restore_used": False,
            "consumed_historical_oos_accessed": False,
            "protected_final_holdout_accessed": False,
        },
        "diagnostic_artifacts": {"artifacts": []},
        "final_evidence_manifest": {"logical_artifacts": []},
        "missing_optional_fields": [],
        "self_hash_sha256": "0" * 64,
    }


def assemble(
    draft: dict[str, object] | None = None,
    *,
    parameter_digest: Any = PARAMETER_SHA,
    buffer_digest: Any = BUFFER_SHA,
    optimizer_digest: Any = None,
) -> dict[str, Any]:
    return assemble_model_state_provenance_manifest(
        manifest_fields=manifest_draft() if draft is None else draft,
        parameter_state_digest_sha256=parameter_digest,
        buffer_state_digest_sha256=buffer_digest,
        optimizer_state_digest_sha256=optimizer_digest,
    )


def reverse_object_order(value: Any) -> Any:
    if isinstance(value, dict):
        reversed_mapping: dict[str, Any] = {}
        for key, item in reversed(tuple(value.items())):
            reversed_mapping[key] = reverse_object_order(item)
        return reversed_mapping
    if isinstance(value, list):
        return [reverse_object_order(item) for item in value]
    return deepcopy(value)


def nested(payload: dict[str, object], section: str) -> dict[str, Any]:
    value = payload[section]
    assert isinstance(value, dict)
    return value


def test_equivalent_mapping_orders_produce_identical_manifest_bytes() -> None:
    first_draft = manifest_draft()
    second_draft = reverse_object_order(first_draft)

    first = assemble(first_draft, optimizer_digest=OPTIMIZER_SHA)
    second = assemble(second_draft, optimizer_digest=OPTIMIZER_SHA)

    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert first["self_hash_sha256"] == second["self_hash_sha256"]


def test_parameter_and_buffer_digests_bind_to_separate_fields() -> None:
    result = assemble()
    policy_state = nested(result, "policy_state")

    assert policy_state["trainable_parameters_digest_sha256"] == PARAMETER_SHA
    assert policy_state["buffers_digest_sha256"] == BUFFER_SHA
    assert policy_state["trainable_parameters_digest_sha256"] != policy_state[
        "buffers_digest_sha256"
    ]


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("parameter", ALTERNATE_SHA),
        ("buffer", ALTERNATE_SHA),
        ("optimizer", ALTERNATE_SHA),
    ],
)
def test_each_model_state_digest_changes_the_manifest_self_hash(
    field: str,
    replacement: str,
) -> None:
    base = assemble(optimizer_digest=OPTIMIZER_SHA)
    arguments: dict[str, Any] = {
        "parameter_digest": PARAMETER_SHA,
        "buffer_digest": BUFFER_SHA,
        "optimizer_digest": OPTIMIZER_SHA,
    }
    arguments[f"{field}_digest"] = replacement
    changed = assemble(**arguments)

    assert changed["self_hash_sha256"] != base["self_hash_sha256"]


def test_optimizer_digest_is_optional_and_explicitly_missing() -> None:
    without_optimizer = assemble()
    optimizer_state = nested(without_optimizer, "optimizer_state")
    missing = without_optimizer["missing_optional_fields"]

    assert optimizer_state["state_digest_sha256"] is None
    assert isinstance(missing, list)
    assert "optimizer_state.state_digest_sha256" in missing
    assert "policy_state.trainable_parameters_digest_sha256" not in missing
    assert "policy_state.buffers_digest_sha256" not in missing

    with_optimizer = assemble(optimizer_digest=OPTIMIZER_SHA)
    optimizer_digest = nested(with_optimizer, "optimizer_state")["state_digest_sha256"]
    missing_fields = with_optimizer["missing_optional_fields"]
    assert optimizer_digest == OPTIMIZER_SHA
    assert "optimizer_state.state_digest_sha256" not in missing_fields


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("parameter_digest", "A" * 64),
        ("buffer_digest", "b" * 63),
        ("optimizer_digest", "not-a-digest"),
    ],
)
def test_malformed_or_uppercase_digests_are_rejected(argument: str, value: str) -> None:
    arguments: dict[str, Any] = {
        "parameter_digest": PARAMETER_SHA,
        "buffer_digest": BUFFER_SHA,
        "optimizer_digest": OPTIMIZER_SHA,
    }
    arguments[argument] = value

    with pytest.raises(RLV2ProvenanceError, match="lowercase SHA-256"):
        assemble(**arguments)


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("parameter_digest", None),
        ("parameter_digest", 7),
        ("buffer_digest", None),
        ("buffer_digest", b"digest"),
    ],
)
def test_mandatory_digest_inputs_require_non_empty_strings(
    argument: str,
    value: object,
) -> None:
    arguments: dict[str, Any] = {
        "parameter_digest": PARAMETER_SHA,
        "buffer_digest": BUFFER_SHA,
    }
    arguments[argument] = value

    with pytest.raises(RLV2ProvenanceError, match="non-empty string"):
        assemble(**arguments)


@pytest.mark.parametrize("value", [7, b"digest", [], ""])
def test_optimizer_digest_requires_string_or_null(value: object) -> None:
    with pytest.raises(RLV2ProvenanceError, match="non-empty string or null"):
        assemble(optimizer_digest=value)


def test_unknown_top_level_and_nested_fields_are_rejected() -> None:
    top_level = manifest_draft()
    top_level["unexpected"] = None
    with pytest.raises(RLV2ProvenanceError, match="forbidden fields"):
        assemble(top_level)

    nested_field = manifest_draft()
    nested(nested_field, "policy_state")["unexpected"] = None
    with pytest.raises(RLV2ProvenanceError, match="forbidden fields"):
        assemble(nested_field)


def test_missing_required_field_is_rejected() -> None:
    draft = manifest_draft()
    draft.pop("dataset_manifest")

    with pytest.raises(RLV2ProvenanceError, match="missing required fields"):
        assemble(draft)


@pytest.mark.parametrize(
    ("section", "field"),
    [
        ("policy_state", "trainable_parameters_digest_sha256"),
        ("policy_state", "buffers_digest_sha256"),
        ("optimizer_state", "state_digest_sha256"),
    ],
)
def test_pre_bound_model_state_identity_is_rejected(section: str, field: str) -> None:
    draft = manifest_draft()
    nested(draft, section)[field] = ALTERNATE_SHA

    with pytest.raises(RLV2ProvenanceError, match="already bound"):
        assemble(draft)


def test_existing_helper_values_are_recomputed_coherently() -> None:
    draft = manifest_draft()
    draft["missing_optional_fields"] = ["incorrect.path"]
    draft["self_hash_sha256"] = "f" * 64

    result = assemble(draft)

    assert "incorrect.path" not in result["missing_optional_fields"]
    assert result["self_hash_sha256"] != "f" * 64
    validate_manifest(result)


def test_caller_mapping_is_not_modified() -> None:
    draft = manifest_draft()
    before = deepcopy(draft)

    assemble(draft, optimizer_digest=OPTIMIZER_SHA)

    assert draft == before


def test_finalized_manifest_self_hash_validates_and_tampering_fails() -> None:
    result = assemble(optimizer_digest=OPTIMIZER_SHA)
    validate_manifest(result)

    tampered = deepcopy(result)
    tampered["manifest_id"] = "rl-v2-model-state-assembler-tampered-v1"
    with pytest.raises(RLV2ProvenanceError, match="self-hash mismatch"):
        validate_manifest(tampered)


@pytest.mark.parametrize(
    ("source_identity", "message"),
    [
        ("Bearer synthetic-credential", "secret-like"),
        ("http://127.0.0.1/private", "private endpoint"),
    ],
)
def test_existing_validator_rejects_sensitive_values(
    source_identity: str,
    message: str,
) -> None:
    draft = manifest_draft()
    nested(draft, "dataset_manifest")["source_identity"] = source_identity

    with pytest.raises(RLV2ProvenanceError, match=message):
        assemble(draft)


@pytest.mark.parametrize(
    "field",
    ["consumed_historical_oos_accessed", "protected_final_holdout_accessed"],
)
def test_protected_dataset_access_is_rejected(field: str) -> None:
    draft = manifest_draft()
    nested(draft, "dataset_manifest")[field] = True

    with pytest.raises(RLV2ProvenanceError, match="access is forbidden"):
        assemble(draft)


def test_phase6_and_selected_model_null_are_preserved() -> None:
    result = assemble()
    authorization = nested(result, "authorization")

    assert authorization["phase6_changed"] is False
    assert authorization["phase6_selected_model"] is None

    changed = manifest_draft()
    nested(changed, "authorization")["phase6_changed"] = True
    with pytest.raises(RLV2ProvenanceError, match="must remain false"):
        assemble(changed)

    selected = manifest_draft()
    nested(selected, "authorization")["phase6_selected_model"] = "synthetic-model"
    with pytest.raises(RLV2ProvenanceError, match="must remain null"):
        assemble(selected)


def test_assembler_has_no_torch_model_file_network_data_or_execution_path() -> None:
    source_path = Path(__file__).parents[2]
    source_path /= "ai_platform/provenance/rl_v2_model_state_manifest.py"
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

    allowed_import_roots = {"__future__", "collections", "copy", "typing", "ai_platform"}
    assert imported_roots <= allowed_import_roots
    forbidden = (
        "torch",
        "stable_baselines3",
        "gymnasium",
        "freqtrade",
        ".state_dict(",
        "named_parameters(",
        "named_buffers(",
        "load_state_dict(",
        "pickle",
        "safetensors",
        ".forward(",
        ".backward(",
        ".step(",
        "open(",
        "read_text(",
        "read_bytes(",
        "urlopen(",
        "requests",
        "socket",
    )
    assert all(marker not in source for marker in forbidden)
