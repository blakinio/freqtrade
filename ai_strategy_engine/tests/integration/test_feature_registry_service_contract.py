from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import jsonschema
import yaml
from strategy_engine.registry import FeatureRegistry


ROOT = Path(__file__).resolve().parents[2]


def _fixture() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(
            (ROOT / "fixtures" / "feature_registry_parity.v1.json").read_text(
                encoding="utf-8"
            )
        ),
    )


def test_feature_registry_manifest_validates_against_published_schema() -> None:
    manifest = yaml.safe_load(
        (ROOT / "configs" / "feature_registry.v1.yaml").read_text(encoding="utf-8")
    )
    schema = json.loads(
        (ROOT / "schemas" / "feature-registry.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(manifest, schema)


def test_feature_registry_parity_prefix_is_append_only() -> None:
    registry = FeatureRegistry.load(ROOT / "configs" / "feature_registry.v1.yaml")
    fixture = _fixture()
    prefix = tuple(cast(list[str], fixture["append_only_prefix"]))

    assert registry.version == fixture["registry_version"]
    assert tuple(registry.features)[: len(prefix)] == prefix


def test_feature_registry_selected_semantics_match_parity_fixture() -> None:
    registry = FeatureRegistry.load(ROOT / "configs" / "feature_registry.v1.yaml")
    fixture = _fixture()
    semantic_parity = cast(dict[str, dict[str, Any]], fixture["semantic_parity"])

    for feature_id, expected in semantic_parity.items():
        definition = registry.get(feature_id)
        actual = {
            "status": definition.status,
            "approved_for_ai": definition.approved_for_ai,
            "research_only": definition.research_only,
            "roles": list(definition.roles),
            "dependencies": list(definition.dependencies),
            "required_sources": list(definition.required_sources),
            "warmup": definition.warmup,
            "timestamp_policy": definition.timestamp_policy,
            "normalization_policy": definition.normalization_policy,
            "license_origin": definition.license_origin,
            "parameter_defaults": {
                name: spec.default for name, spec in definition.parameters.items()
            },
        }
        assert actual == expected


def test_feature_registry_dependency_replay_is_deterministic() -> None:
    registry = FeatureRegistry.load(ROOT / "configs" / "feature_registry.v1.yaml")
    fixture = _fixture()
    replay = cast(list[dict[str, list[str]]], fixture["dependency_replays"])[0]

    first = registry.resolve_dependencies(tuple(replay["requested"]))
    second = registry.resolve_dependencies(tuple(replay["requested"]))

    assert first == second == tuple(replay["resolved"])
