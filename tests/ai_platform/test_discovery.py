import ast
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import ai_platform.scripts.discovery as discovery_module
from ai_platform.scripts.discovery import (
    CandidateArtifacts,
    DiscoveryError,
    build_candidate_payloads,
    build_import_validation_command,
    discover_candidates,
    generate_candidate_specs,
    load_base_documents,
    load_search_space,
    render_strategy,
    robustness_score,
    validate_generated_strategy,
)


ROOT = Path(__file__).resolve().parents[2]
SEARCH_PATH = ROOT / "ai_platform" / "discovery" / "search-space-v1.json"
SCHEMA_PATH = ROOT / "ai_platform" / "discovery" / "search-space-schema-v1.json"


def test_search_space_matches_schema() -> None:
    search = json.loads(SEARCH_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(search)


def test_candidate_generation_is_deterministic_and_bounded() -> None:
    search = load_search_space(SEARCH_PATH)
    first = generate_candidate_specs(search)
    second = generate_candidate_specs(search)

    assert first == second
    assert len(first) == 18
    assert len({candidate["candidate_id"] for candidate in first}) == 18
    assert len({candidate["class_name"] for candidate in first}) == 18
    assert all(candidate["model_type"] == "LightGBMRegressor" for candidate in first)


def test_search_space_rejects_unknown_feature_group(tmp_path: Path) -> None:
    search = json.loads(SEARCH_PATH.read_text(encoding="utf-8"))
    search["feature_group_sets"] = [["price_action", "arbitrary_python"]]
    search["max_candidates"] = 6
    path = tmp_path / "search.json"
    path.write_text(json.dumps(search), encoding="utf-8")

    with pytest.raises(DiscoveryError, match="Unsupported feature groups"):
        load_search_space(path)


def test_search_space_rejects_expansion_above_cap(tmp_path: Path) -> None:
    search = json.loads(SEARCH_PATH.read_text(encoding="utf-8"))
    search["max_candidates"] = 1
    path = tmp_path / "search.json"
    path.write_text(json.dumps(search), encoding="utf-8")

    with pytest.raises(DiscoveryError, match="above max_candidates"):
        load_search_space(path)


def test_generated_strategy_compiles_without_dynamic_execution() -> None:
    search = load_search_space(SEARCH_PATH)
    candidate = generate_candidate_specs(search)[0]
    source = render_strategy(candidate)

    validate_generated_strategy(source, candidate["class_name"])
    tree = ast.parse(source)
    forbidden = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } & {"eval", "exec", "compile", "__import__"}

    assert forbidden == set()
    assert f"class {candidate['class_name']}" in source
    assert "can_short = False" in source


def test_candidate_payloads_preserve_research_safety_and_identity() -> None:
    search = load_search_space(SEARCH_PATH)
    candidate = generate_candidate_specs(search)[0]
    base = load_base_documents(search)
    relative = f"ai_platform/artifacts/discovery/{candidate['candidate_id']}"

    payloads = build_candidate_payloads(candidate, search, base, relative)

    assert payloads["config"]["dry_run"] is True
    assert payloads["config"]["exchange"]["key"] == ""
    assert payloads["config"]["exchange"]["secret"] == ""
    assert payloads["config"]["freqai"]["identifier"] == candidate["candidate_id"]
    assert payloads["manifest"]["strategy"] == candidate["class_name"]
    assert payloads["manifest"]["config"] == f"{relative}/config.json"
    assert payloads["validation"]["experiment_manifest"] == f"{relative}/experiment.json"
    assert payloads["registry"]["definition_id"] == candidate["candidate_id"]
    assert payloads["registry"]["target_id"] == search["target_id"]


def test_import_validation_command_uses_generated_directory(tmp_path: Path) -> None:
    artifacts = CandidateArtifacts(
        candidate_id="disc-123",
        class_name="DiscoveryStrategy_123",
        directory=tmp_path,
        strategy_path=tmp_path / "DiscoveryStrategy_123.py",
        config_path=tmp_path / "config.json",
        manifest_path=tmp_path / "experiment.json",
        validation_plan_path=tmp_path / "validation.json",
        registry_definition_path=tmp_path / "registry.json",
        result_path=tmp_path / "candidate-result.json",
    )

    command = build_import_validation_command(artifacts, freqtrade_bin="freqtrade")

    assert command == [
        "freqtrade",
        "list-strategies",
        "--strategy-path",
        str(tmp_path),
        "--one-column",
    ]


def test_discovery_preserves_failure_without_rematerializing(tmp_path: Path, monkeypatch) -> None:
    search = load_search_space(SEARCH_PATH)

    def fail_candidate(*args, **kwargs):
        raise DiscoveryError("materialization failed")

    monkeypatch.setattr(discovery_module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(discovery_module, "DISCOVERY_ROOT", tmp_path)
    monkeypatch.setattr(discovery_module, "run_candidate", fail_candidate)

    results = discover_candidates(
        search,
        limit=1,
        freqtrade_bin="freqtrade",
        experiment_stage="backtest",
        registry_db=tmp_path / "registry.sqlite3",
    )

    assert len(results) == 1
    assert results[0]["status"] == "failed"
    assert results[0]["executed"] is False
    assert results[0]["error"] == "materialization failed"

    result_path = tmp_path / results[0]["candidate_id"] / "candidate-result.json"
    persisted = json.loads(result_path.read_text(encoding="utf-8"))
    assert persisted == results[0]


def test_robustness_score_requires_promotion_and_rewards_consistency() -> None:
    robust = {
        "promotion_allowed": True,
        "walk_forward": [
            {"profit": 0.04, "drawdown": 0.08},
            {"profit": 0.03, "drawdown": 0.09},
        ],
        "holdout": {"profit": 0.035, "drawdown": 0.08},
    }
    fragile = {
        "promotion_allowed": True,
        "walk_forward": [
            {"profit": 0.10, "drawdown": 0.20},
            {"profit": -0.02, "drawdown": 0.22},
        ],
        "holdout": {"profit": 0.02, "drawdown": 0.21},
    }
    rejected = {**robust, "promotion_allowed": False}

    robust_score = robustness_score(robust)
    fragile_score = robustness_score(fragile)

    assert robust_score is not None
    assert fragile_score is not None
    assert robust_score > fragile_score
    assert robustness_score(rejected) is None
