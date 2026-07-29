from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from strategy_engine.registry import FeatureRegistry, SearchSpaceRegistry
from strategy_engine.research.candidate import (
    CandidateGenerationError,
    CandidateGenerator,
    CandidateRequest,
)

ENGINE_ROOT = Path(__file__).resolve().parents[2]
REQUEST_PATH = ENGINE_ROOT / "examples" / "ai_candidate_request.json"


def _generator() -> CandidateGenerator:
    return CandidateGenerator(
        FeatureRegistry.load(ENGINE_ROOT / "configs" / "feature_registry.v1.yaml"),
        SearchSpaceRegistry.load(ENGINE_ROOT / "configs" / "search_spaces.v1.yaml"),
    )


def _request_payload() -> dict[str, object]:
    return json.loads(REQUEST_PATH.read_text(encoding="utf-8"))


def test_ai_candidate_is_registry_only_and_valid_strategy_dsl() -> None:
    request_payload = _request_payload()
    jsonschema.validate(
        request_payload,
        json.loads(
            (ENGINE_ROOT / "schemas" / "ai-candidate-request.v1.schema.json").read_text(
                encoding="utf-8"
            )
        ),
    )
    candidate = _generator().generate(CandidateRequest.model_validate(request_payload))
    schema = json.loads(
        (ENGINE_ROOT / "schemas" / "strategy-definition.v1.schema.json").read_text(encoding="utf-8")
    )

    jsonschema.validate(candidate.model_dump(mode="json"), schema)
    assert [feature.id for feature in candidate.features] == ["roc.v1", "atr.v1"]
    assert candidate.execution["execution_authority"] is False
    assert candidate.execution["order_submission"] is False
    assert candidate.provenance.details["final_holdout_used"] is False


def test_ai_candidate_rejects_feature_not_approved_for_ai() -> None:
    payload = _request_payload()
    payload["features"] = [
        {
            "feature_id": "squeeze_ratio.v1",
            "timeframe": "5m",
            "parameter_overrides": {},
        }
    ]

    with pytest.raises(CandidateGenerationError) as exc_info:
        _generator().generate(CandidateRequest.model_validate(payload))

    assert exc_info.value.reason_code == "FEATURE_NOT_APPROVED_FOR_AI"


def test_ai_candidate_rejects_unknown_registry_parameter() -> None:
    payload = _request_payload()
    features = payload["features"]
    assert isinstance(features, list)
    first = features[0]
    assert isinstance(first, dict)
    first["parameter_overrides"] = {"period": 12, "future_shift": -1}

    with pytest.raises(CandidateGenerationError) as exc_info:
        _generator().generate(CandidateRequest.model_validate(payload))

    assert exc_info.value.reason_code == "FEATURE_PARAMETERS_REJECTED"


def test_ai_candidate_requires_concrete_falsification_contract() -> None:
    payload = _request_payload()
    falsification = payload["falsification_test"]
    assert isinstance(falsification, dict)
    falsification["hypothesis"] = ""

    with pytest.raises(ValidationError):
        CandidateRequest.model_validate(payload)
