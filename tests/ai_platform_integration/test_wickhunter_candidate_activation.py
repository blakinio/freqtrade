from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

import ai_platform.wickhunter.candidate_activation as candidate_activation
from ai_platform.wickhunter.candidate_activation import (
    CANDIDATE_FILES,
    CandidateActivationError,
    activate_verified_candidate,
    verify_candidate_package,
)
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.lightgbm_scorer import (
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    MODEL_ARTIFACT_SCHEMA_VERSION,
    MODEL_KIND,
    CalibrationCurve,
    LightGBMModelArtifact,
    LightGBMTrainingPolicy,
)
from ai_platform.wickhunter.paper_validation import (
    PaperRunRequest,
    PaperValidationPolicy,
    publish_paper_run_request,
    verify_paper_run_request,
)
from ai_platform.wickhunter.parameters import INITIAL_COMPATIBILITY_PRIOR


CODE_SHA = "a" * 40
EVALUATION_SHA = "b" * 64
MODEL_HASH = hashlib.sha256(b"model-text\n").hexdigest()
OPTIMIZER_ID = "c" * 64
COMPARISON_ID = "d" * 64
ROLLBACK_HASH = "e" * 64


def _write(path: Path, payload: object) -> None:
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _package(root: Path) -> Path:
    root.mkdir()
    parameters = replace(
        INITIAL_COMPATIBILITY_PRIOR,
        parameter_version="wickhunter-production-h180s-test",
        maximum_holding_ms=180_000,
    )
    parameter_payload = json.loads(canonical_json(parameters))
    parameter_payload["parameter_sha256"] = parameters.parameter_hash

    training_policy = LightGBMTrainingPolicy()
    calibration = CalibrationCurve(
        schema_version="wickhunter-probability-calibration-v1",
        upper_bounds=(Decimal("0.5"), Decimal("1")),
        probabilities=(Decimal("0.4"), Decimal("0.7")),
    )
    artifact = LightGBMModelArtifact(
        schema_version=MODEL_ARTIFACT_SCHEMA_VERSION,
        model_kind=MODEL_KIND,
        model_version="wickhunter-lightgbm-test",
        model_hash=MODEL_HASH,
        model_text="model-text\n",
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        feature_schema_sha256=canonical_sha256(
            {"version": FEATURE_SCHEMA_VERSION, "names": FEATURE_NAMES}
        ),
        feature_names=FEATURE_NAMES,
        training_policy=training_policy,
        dataset_id="wickhunter-test-dataset",
        dataset_manifest_sha256="1" * 64,
        market_manifest_sha256="2" * 64,
        split_geometry_sha256="3" * 64,
        price_path_manifest_sha256="4" * 64,
        replay_policy_version="wickhunter-replay-test-v1",
        replay_policy_sha256="5" * 64,
        parameter_version=parameters.parameter_version,
        parameter_sha256=parameters.parameter_hash,
        training_case_sha256s=("6" * 64,),
        calibration_case_sha256s=("7" * 64,),
        training_example_count=2,
        calibration_example_count=1,
        positive_example_count=1,
        negative_example_count=1,
        positive_return_mean=Decimal("0.01"),
        negative_return_mean=Decimal("-0.01"),
        calibration=calibration,
        protected_holdout_accessed=False,
        automatic_promotion_enabled=False,
        execution_enabled=False,
        live_capital_authorized=False,
        orders_submitted=0,
    )
    model_payload = artifact.as_registry_record()
    payloads = {
        "evaluation-identity.json": {
            "evaluation_sha256": EVALUATION_SHA,
            "case_count": 824,
            "split_counts": {"train": 565, "validation": 178, "test": 81},
            "protected_holdout_accessed": False,
            "execution_enabled": False,
            "live_capital_authorized": False,
            "orders_submitted": 0,
        },
        "finite-search-audit.json": {
            "selection_source": "validation_only",
            "test_used_for_selection": False,
            "protected_holdout_accessed": False,
            "execution_enabled": False,
            "live_capital_authorized": False,
            "orders_submitted": 0,
        },
        "selected-parameters.json": parameter_payload,
        "optimizer-result.json": {
            "result_id": OPTIMIZER_ID,
            "selection_source": "validation_only",
            "test_used_for_selection": False,
            "model_promoted": False,
            "profitability_claimed": False,
            "execution_enabled": False,
            "live_capital_authorized": False,
            "orders_submitted": 0,
        },
        "model-artifact.json": model_payload,
        "comparison-report.json": {
            "report_id": COMPARISON_ID,
            "model_promoted": False,
            "profitability_claimed": False,
            "execution_enabled": False,
            "live_capital_authorized": False,
            "orders_submitted": 0,
        },
        "rollback.json": {
            "model_version": "wickhunter-deterministic-baseline-v1",
            "model_hash": ROLLBACK_HASH,
            "parameter_version": parameters.parameter_version,
            "parameter_hash": parameters.parameter_hash,
            "automatic_activation": False,
            "owner_decision_required": True,
            "execution_enabled": False,
            "live_capital_authorized": False,
            "orders_submitted": 0,
        },
    }
    assert set(payloads) == set(CANDIDATE_FILES)
    records = []
    for name, payload in payloads.items():
        path = root / name
        _write(path, payload)
        records.append(
            {
                "logical_name": name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
            }
        )
    records.sort(key=lambda item: item["logical_name"])
    manifest_seed = {
        "schema_version": "wickhunter-candidate-materialization-manifest-v1",
        "package_id": "wickhunter-candidate-test",
        "source_commit_sha": CODE_SHA,
        "evaluation_sha256": EVALUATION_SHA,
        "parameter_version": parameters.parameter_version,
        "parameter_sha256": parameters.parameter_hash,
        "model_version": model_payload["model_version"],
        "model_hash": MODEL_HASH,
        "model_artifact_sha256": model_payload["artifact_sha256"],
        "optimizer_result_id": OPTIMIZER_ID,
        "comparison_report_id": COMPARISON_ID,
        "rollback_model_version": "wickhunter-deterministic-baseline-v1",
        "rollback_model_hash": ROLLBACK_HASH,
        "rollback_parameter_version": parameters.parameter_version,
        "rollback_parameter_hash": parameters.parameter_hash,
        "selection_source": "validation_only",
        "test_used_for_selection": False,
        "candidate_only": True,
        "owner_decision_required": True,
        "automatic_promotion_enabled": False,
        "protected_holdout_accessed": False,
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "execution_enabled": False,
        "live_capital_authorized": False,
        "orders_submitted": 0,
        "files": records,
    }
    manifest = {
        **manifest_seed,
        "manifest_sha256": canonical_sha256(manifest_seed),
    }
    _write(root / "manifest.json", manifest)
    checksum_entries = [f"{record['sha256']}  {record['logical_name']}" for record in records]
    checksum_entries.append(
        f"{hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest()}  manifest.json"
    )
    (root / "artifact-sha256.txt").write_text(
        "\n".join(sorted(checksum_entries)) + "\n",
        encoding="utf-8",
    )
    return root


def _rehash(root: Path) -> None:
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = []
    for name in sorted(CANDIDATE_FILES):
        path = root / name
        records.append(
            {
                "logical_name": name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
            }
        )
    manifest["files"] = records
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    _write(manifest_path, manifest)
    checksum_entries = [f"{record['sha256']}  {record['logical_name']}" for record in records]
    checksum_entries.append(
        f"{hashlib.sha256(manifest_path.read_bytes()).hexdigest()}  manifest.json"
    )
    (root / "artifact-sha256.txt").write_text(
        "\n".join(sorted(checksum_entries)) + "\n",
        encoding="utf-8",
    )


def test_verified_candidate_activates_immutable_paper_run(tmp_path: Path) -> None:
    candidate_root = _package(tmp_path / "candidate")
    activation_root = tmp_path / "activation"

    result = activate_verified_candidate(
        candidate_root=candidate_root,
        activation_root=activation_root,
        created_at_ms=1_800_000_000_000,
    )

    assert result.identity.evaluation_sha256 == EVALUATION_SHA
    assert result.request.dataset_hash == EVALUATION_SHA
    assert result.request.model_hash == MODEL_HASH
    assert result.request.orders_submitted == 0
    verified = verify_paper_run_request(activation_root)
    assert verified["run_id"] == result.request.run_id
    binding = json.loads(
        (tmp_path / "activation-candidate-binding.json").read_text(encoding="utf-8")
    )
    claimed = binding.pop("binding_sha256")
    assert claimed == canonical_sha256(binding)
    assert not binding["execution_enabled"]
    assert not binding["live_capital_authorized"]


def test_activation_resumes_after_request_publication_is_interrupted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_root = _package(tmp_path / "candidate")
    activation_root = tmp_path / "activation"

    def interrupted_publish(
        destination: Path,
        *,
        request: PaperRunRequest,
        policy: PaperValidationPolicy,
    ) -> dict[str, object]:
        result = publish_paper_run_request(
            destination,
            request=request,
            policy=policy,
        )
        assert result["run_id"] == request.run_id
        raise RuntimeError("simulated interruption after request publication")

    monkeypatch.setattr(
        candidate_activation,
        "publish_paper_run_request",
        interrupted_publish,
    )
    with pytest.raises(RuntimeError, match="simulated interruption"):
        activate_verified_candidate(
            candidate_root=candidate_root,
            activation_root=activation_root,
            created_at_ms=1_800_000_000_000,
        )
    binding_path = tmp_path / "activation-candidate-binding.json"
    assert activation_root.is_dir()
    assert not binding_path.exists()

    monkeypatch.setattr(
        candidate_activation,
        "publish_paper_run_request",
        publish_paper_run_request,
    )
    result = activate_verified_candidate(
        candidate_root=candidate_root,
        activation_root=activation_root,
        created_at_ms=1_800_000_000_000,
    )
    assert verify_paper_run_request(activation_root)["run_id"] == result.request.run_id
    assert binding_path.is_file()


def test_conflicting_existing_binding_blocks_request_publication(tmp_path: Path) -> None:
    candidate_root = _package(tmp_path / "candidate")
    activation_root = tmp_path / "activation"
    binding_path = tmp_path / "activation-candidate-binding.json"
    binding_path.write_text('{"run_id":"conflicting"}\n', encoding="utf-8")

    with pytest.raises(CandidateActivationError, match="binding identity mismatch"):
        activate_verified_candidate(
            candidate_root=candidate_root,
            activation_root=activation_root,
            created_at_ms=1_800_000_000_000,
        )
    assert not activation_root.exists()


def test_coordinated_model_text_tampering_is_rejected(tmp_path: Path) -> None:
    root = _package(tmp_path / "candidate")
    model_path = root / "model-artifact.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["model_text"] = "tampered-model-text"
    _write(model_path, model)
    _rehash(root)

    with pytest.raises(
        CandidateActivationError,
        match="model artifact semantic validation failed",
    ):
        verify_candidate_package(root)


def test_coordinated_model_schema_tampering_is_rejected(tmp_path: Path) -> None:
    root = _package(tmp_path / "candidate")
    model_path = root / "model-artifact.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["feature_names"] = [*model["feature_names"], "future_return"]
    model["feature_schema_sha256"] = canonical_sha256(
        {
            "version": model["feature_schema_version"],
            "names": model["feature_names"],
        }
    )
    base = {
        key: value
        for key, value in model.items()
        if key not in {"artifact_sha256", "promotion_state", "advisory_only"}
    }
    model["artifact_sha256"] = canonical_sha256(base)
    _write(model_path, model)
    _rehash(root)

    with pytest.raises(
        CandidateActivationError,
        match="model artifact semantic validation failed",
    ):
        verify_candidate_package(root)


def test_manifest_authority_tampering_is_rejected(tmp_path: Path) -> None:
    root = _package(tmp_path / "candidate")
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["execution_enabled"] = True
    manifest.pop("manifest_sha256")
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    _write(manifest_path, manifest)
    checksum_path = root / "artifact-sha256.txt"
    lines = [
        line
        for line in checksum_path.read_text(encoding="utf-8").splitlines()
        if not line.endswith("  manifest.json")
    ]
    lines.append(f"{hashlib.sha256(manifest_path.read_bytes()).hexdigest()}  manifest.json")
    checksum_path.write_text("\n".join(sorted(lines)) + "\n", encoding="utf-8")

    with pytest.raises(CandidateActivationError, match="unsafe authority"):
        verify_candidate_package(root)
