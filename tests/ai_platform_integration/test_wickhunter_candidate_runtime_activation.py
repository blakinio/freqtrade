from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import ai_platform.wickhunter.candidate_runtime_activation as runtime_activation
from ai_platform.wickhunter.parameters import INITIAL_COMPATIBILITY_PRIOR


CREATED_AT_MS = 1_800_000_000_000
EVALUATION_SHA = "b" * 64
DATASET_MANIFEST_SHA = "7" * 64


def test_runtime_activation_uses_verified_replay_dataset_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity = SimpleNamespace(
        model_version="wickhunter-lightgbm-candidate-v1",
        model_hash="c" * 64,
        parameter_version=INITIAL_COMPATIBILITY_PRIOR.parameter_version,
        parameter_hash=INITIAL_COMPATIBILITY_PRIOR.parameter_hash,
        evaluation_sha256=EVALUATION_SHA,
        source_commit_sha="a" * 40,
        rollback_model_version="wickhunter-rollback-model-v1",
        rollback_model_hash="d" * 64,
        rollback_parameter_version="wickhunter-rollback-parameters-v1",
        rollback_parameter_hash="e" * 64,
    )
    package = SimpleNamespace(
        identity=identity,
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        model_artifact=SimpleNamespace(dataset_manifest_sha256=DATASET_MANIFEST_SHA),
    )
    published: dict[str, object] = {}

    monkeypatch.setattr(
        runtime_activation,
        "load_verified_candidate_package",
        lambda _root: package,
    )
    monkeypatch.setattr(
        runtime_activation,
        "_activation_binding",
        lambda _identity, request: {"dataset_hash": request.dataset_hash},
    )
    monkeypatch.setattr(
        runtime_activation,
        "_publish_or_verify_activation",
        lambda _root, *, request, policy: published.update({"request": request, "policy": policy}),
    )
    monkeypatch.setattr(
        runtime_activation,
        "_write_or_verify_activation_binding",
        lambda _path, binding: published.update({"binding": binding}),
    )

    result = runtime_activation.activate_verified_runtime_candidate(
        candidate_root=tmp_path / "candidate",
        activation_root=tmp_path / "activation",
        created_at_ms=CREATED_AT_MS,
    )

    assert result.request.dataset_hash == DATASET_MANIFEST_SHA
    assert result.request.dataset_hash != EVALUATION_SHA
    assert result.request.code_sha == identity.source_commit_sha
    assert published["request"] is result.request
    assert published["binding"] == {"dataset_hash": DATASET_MANIFEST_SHA}
    assert result.request.protected_holdout_accessed is False
    assert result.request.automatic_promotion_enabled is False
    assert result.request.trading_credentials_present is False
    assert result.request.execution_enabled is False
    assert result.request.orders_submitted == 0
    assert result.request.live_capital_authorized is False
