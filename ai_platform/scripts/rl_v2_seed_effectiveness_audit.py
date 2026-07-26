"""Fail-closed static audit for the completed RL-v2 seed path.

This module inspects repository text and metadata only. It never imports the RL
runtime, accesses market data, or executes a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

AUDIT_ID = "rl-v2-seed-effectiveness-determinism-audit-v1"
DESCRIPTOR_PATH = Path(
    "ai_platform/experimental_model_research/"
    "rl-v2-seed-effectiveness-determinism-audit-v1.json"
)
CONFIG_PATH = Path("ai_platform/configs/rl_v2_training_research.json")
MODEL_PATH = Path("ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py")
MATERIALIZER_PATH = Path(
    "ai_platform/scripts/rl_v2_action_observability_execution_run_request.py"
)
LEARNER_PATH = Path("freqtrade/freqai/prediction_models/ReinforcementLearner.py")
BASE_RL_PATH = Path("freqtrade/freqai/RL/BaseReinforcementLearningModel.py")
ENVIRONMENT_PATH = Path("freqtrade/freqai/RL/BaseEnvironment.py")
WORKFLOW_PATH = Path(
    ".github/workflows/ai-platform-rl-v2-action-observability-execution.yml"
)
REQUEST_PATH = Path(
    "ai_platform/experimental_model_research/run-requests/"
    "rl-v2-action-observability-execution-v1.json"
)

EXECUTION_SEEDS = (271828182, 628318530, 1414213562, 1618033988)

EXPECTED_SOURCE_BLOBS = {
    CONFIG_PATH: "340972a028fe1c423a56378f7552b54ac3aff219",
    MODEL_PATH: "d133dfe8673cdc5e98d443cdd0550ee1c1f3ca34",
    MATERIALIZER_PATH: "256d56cf329ca7ea5557e64349ffa71f650405f7",
    LEARNER_PATH: "ff6b2d029166552ba664ff8aa0581fc09ee1b6eb",
    BASE_RL_PATH: "db9fba85a4fe5356e2eafd8edb09f9b62a491073",
    ENVIRONMENT_PATH: "d33cf1393b1af2268256468d519edfd1c7928d51",
    WORKFLOW_PATH: "75488401c99cbd10574801a949c0a7ddd261125b",
}

SB3_REVIEW = {
    "repository": "DLR-RM/stable-baselines3",
    "reviewed_commit": "06f613544574aa3157eba0ccee8570f5a8a8e1c9",
    "base_class_blob_sha1": "e1216ab6b33c7fa6e7253b59e6a9215e51fe4eef",
    "on_policy_algorithm_blob_sha1": "a437b5e91a970b53e62de675c6b2da2ad23d52ee",
}


class RLV2SeedEffectivenessAuditError(RuntimeError):
    """Raised when the static seed audit no longer reconciles."""


def _repo_path(path: Path) -> Path:
    return REPO_ROOT / path


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    payload = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


def _read_text(path: Path) -> str:
    resolved = _repo_path(path)
    if not resolved.is_file():
        raise RLV2SeedEffectivenessAuditError(f"Required audit source is missing: {path}")
    return resolved.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise RLV2SeedEffectivenessAuditError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RLV2SeedEffectivenessAuditError(f"Expected a JSON object in {path}")
    return payload


def _require_source_bindings() -> dict[str, str]:
    bindings: dict[str, str] = {}
    for path, expected in EXPECTED_SOURCE_BLOBS.items():
        actual = _git_blob_sha1(_repo_path(path))
        if actual != expected:
            raise RLV2SeedEffectivenessAuditError(
                f"Seed-path source drifted for {path}: expected {expected}, got {actual}"
            )
        bindings[path.as_posix()] = actual
    return bindings


def _require_snippets(path: Path, snippets: tuple[str, ...]) -> None:
    source = _read_text(path)
    for snippet in snippets:
        if snippet not in source:
            raise RLV2SeedEffectivenessAuditError(
                f"Required seed-path evidence is missing from {path}: {snippet}"
            )


def _validate_repository_seed_path() -> None:
    _require_snippets(
        MATERIALIZER_PATH,
        (
            'freqai["identifier"] = runtime_identifier(seed)',
            'freqai.setdefault("model_training_parameters", {})["seed"] = seed',
        ),
    )
    _require_snippets(
        MODEL_PATH,
        (
            'parameters = self.freqai_info.get("model_training_parameters", {})',
            'env_info["seed"] = int(parameters.get("seed", 42))',
        ),
    )
    _require_snippets(
        LEARNER_PATH,
        ('**self.freqai_info.get("model_training_parameters", {})',),
    )
    _require_snippets(BASE_RL_PATH, ("self.set_train_and_eval_environments", "model = self.fit"))
    _require_snippets(
        ENVIRONMENT_PATH,
        (
            "self.seed(seed)",
            "self.np_random, seed = seeding.np_random(seed)",
            'self.rl_config.get("randomize_starting_position", False)',
            "random.randint(self.window_size + 1, length_of_data)",
        ),
    )

    config = _read_json(CONFIG_PATH)
    freqai = config.get("freqai")
    if not isinstance(freqai, dict):
        raise RLV2SeedEffectivenessAuditError("Frozen config is missing freqai")
    training = freqai.get("model_training_parameters")
    if training != {"seed": 42, "n_steps": 128, "batch_size": 64}:
        raise RLV2SeedEffectivenessAuditError("Frozen base model-training parameters drifted")
    rl_config = freqai.get("rl_config")
    if not isinstance(rl_config, dict) or rl_config.get("randomize_starting_position") is not False:
        raise RLV2SeedEffectivenessAuditError(
            "Completed matrix must keep randomize_starting_position false"
        )
    if rl_config.get("cpu_count") != 1:
        raise RLV2SeedEffectivenessAuditError("Completed matrix CPU-count binding drifted")

    if _repo_path(REQUEST_PATH).exists():
        raise RLV2SeedEffectivenessAuditError(
            "Canonical action-observability request must remain absent from the repository"
        )


def canonical_descriptor() -> dict[str, Any]:
    """Return the only accepted static-audit descriptor."""
    source_bindings = _require_source_bindings()
    _validate_repository_seed_path()
    return {
        "schema_version": 1,
        "audit_id": AUDIT_ID,
        "status": "code_audit_complete_no_seed_propagation_defect_proven",
        "classification": "static_repository_code_audit",
        "source_bindings": source_bindings,
        "completed_execution_reference": {
            "trigger_pr": 345,
            "workflow_run_id": 30195095341,
            "execution_head": "ca10ddfd981da3a05debcec7a24a5db4ecbbd07c",
            "execution_seeds": list(EXECUTION_SEEDS),
            "identical_complete_timeline_seeds": [271828182, 628318530],
            "invariant_action_summary_pairs": ["BTC/USDT"],
            "telemetry_rows_per_seed": 29378,
            "decision": None,
        },
        "repository_seed_path": {
            "runtime_materializer_sets_per_run_seed": True,
            "runtime_materializer_sets_distinct_identifier": True,
            "project_model_passes_seed_to_environment": True,
            "inherited_learner_passes_training_parameters_to_ppo": True,
            "environment_seeds_gym_numpy_generator": True,
            "randomized_starting_position_enabled": False,
            "global_random_randint_branch_active_in_completed_matrix": False,
            "repository_seed_wiring_supported": True,
        },
        "stable_baselines3_source_review": {
            **SB3_REVIEW,
            "on_policy_setup_calls_set_random_seed_before_policy_construction": True,
            "set_random_seed_scope": [
                "python",
                "numpy",
                "pytorch",
                "action_space",
                "environment",
            ],
            "exact_completed_runtime_version_retained": False,
        },
        "retained_evidence_gaps": {
            "exact_python_version_manifest_retained": False,
            "exact_dependency_version_manifest_retained": False,
            "stable_baselines3_version_retained": False,
            "torch_version_retained": False,
            "device_and_determinism_flags_retained": False,
            "initial_policy_parameter_digest_retained": False,
            "final_policy_parameter_digest_retained": False,
            "serialized_trained_policy_retained": False,
        },
        "bounded_conclusion": {
            "incomplete_seed_propagation_defect_supported": False,
            "identical_output_mechanism_explained": False,
            "compatible_explanations": [
                "policy_output_collision",
                "deterministic_convergence",
                "pair_specific_action_boundary_saturation",
            ],
            "runtime_code_change_authorized": False,
            "seed_rerun_authorized": False,
            "ranking_or_promotion_authorized": False,
        },
        "future_provenance_requirements": [
            "exact_python_and_dependency_versions_with_hashes",
            "device_and_torch_determinism_flags",
            "per_pair_initial_policy_state_digest",
            "per_pair_final_policy_state_digest",
            "serialized_trained_policy_artifact_digest",
            "effective_runtime_config_digest",
            "seed_and_rng_provenance",
        ],
        "authorization": {
            "market_data_access": False,
            "cache_restore": False,
            "model_training": False,
            "backtest": False,
            "inference": False,
            "seed_rerun": False,
            "runtime_change": False,
            "upstream_core_change": False,
            "ranking": False,
            "promotion": False,
            "dry_run": False,
            "live": False,
            "consumed_historical_oos_access": False,
            "protected_final_holdout_access": False,
        },
        "governance": {
            "strict_oos": False,
            "protected_final_validation": False,
            "phase6_selected_model": None,
            "profitability_is_non_gating": True,
        },
    }


def validate_descriptor(path: Path = DESCRIPTOR_PATH) -> dict[str, Any]:
    """Fail closed unless the descriptor exactly equals repository evidence."""
    descriptor = _read_json(path)
    expected = canonical_descriptor()
    if descriptor != expected:
        raise RLV2SeedEffectivenessAuditError(
            "RL-v2 seed-effectiveness descriptor drifted from canonical static evidence"
        )
    return descriptor


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor", nargs="?", type=Path, default=DESCRIPTOR_PATH)
    parser.add_argument("--print-canonical", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.print_canonical:
            print(json.dumps(canonical_descriptor(), indent=2, sort_keys=True))
            return 0
        validate_descriptor(args.descriptor)
        return 0
    except RLV2SeedEffectivenessAuditError as exc:
        print(f"RL-v2 seed-effectiveness audit failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
