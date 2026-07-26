from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_platform.scripts import rl_v2_seed_effectiveness_audit as audit
from ai_platform.scripts.rl_v2_action_observability_execution_run_request import (
    materialize_runtime_config,
    runtime_identifier,
)


def test_descriptor_matches_canonical_static_evidence() -> None:
    assert audit.validate_descriptor() == audit.canonical_descriptor()


def test_all_authorizations_remain_false() -> None:
    descriptor = audit.canonical_descriptor()
    assert descriptor["authorization"]
    assert set(descriptor["authorization"].values()) == {False}


def test_seed_path_conclusion_is_bounded() -> None:
    descriptor = audit.canonical_descriptor()
    conclusion = descriptor["bounded_conclusion"]
    assert descriptor["repository_seed_path"]["repository_seed_wiring_supported"] is True
    assert conclusion["incomplete_seed_propagation_defect_supported"] is False
    assert conclusion["identical_output_mechanism_explained"] is False
    assert conclusion["runtime_code_change_authorized"] is False
    assert conclusion["seed_rerun_authorized"] is False


@pytest.mark.parametrize("seed", audit.EXECUTION_SEEDS)
def test_materialized_config_uses_exact_seed_and_identifier(tmp_path: Path, seed: int) -> None:
    output = tmp_path / f"seed-{seed}.json"
    materialize_runtime_config(output, seed)
    config = json.loads(output.read_text(encoding="utf-8"))

    freqai = config["freqai"]
    assert freqai["identifier"] == runtime_identifier(seed)
    assert freqai["model_training_parameters"] == {
        "seed": seed,
        "n_steps": 128,
        "batch_size": 64,
    }
    assert freqai["data_split_parameters"] == {
        "test_size": 0.2,
        "random_state": 42,
        "shuffle": False,
    }
    assert freqai["rl_config"]["randomize_starting_position"] is False


def test_source_hash_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(audit.EXPECTED_SOURCE_BLOBS, audit.CONFIG_PATH, "0" * 40)
    with pytest.raises(audit.RLV2SeedEffectivenessAuditError, match="source drifted"):
        audit.canonical_descriptor()


def test_descriptor_tampering_fails_closed(tmp_path: Path) -> None:
    descriptor = audit.canonical_descriptor()
    descriptor["bounded_conclusion"]["seed_rerun_authorized"] = True
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(descriptor), encoding="utf-8")

    with pytest.raises(audit.RLV2SeedEffectivenessAuditError, match="descriptor drifted"):
        audit.validate_descriptor(path)


def test_completed_trigger_request_remains_absent() -> None:
    assert not (audit.REPO_ROOT / audit.REQUEST_PATH).exists()


def test_exact_runtime_provenance_gaps_remain_explicit() -> None:
    gaps = audit.canonical_descriptor()["retained_evidence_gaps"]
    assert set(gaps.values()) == {False}
    assert gaps["stable_baselines3_version_retained"] is False
    assert gaps["final_policy_parameter_digest_retained"] is False
    assert gaps["serialized_trained_policy_retained"] is False
