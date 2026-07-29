from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml
from pydantic import ValidationError

from strategy_engine.research.dataset import (
    DatasetManifest,
    DatasetManifestError,
    load_dataset_manifest,
    validate_protected_holdout,
)

ENGINE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ENGINE_ROOT.parent
MANIFEST_PATH = ENGINE_ROOT / "configs" / "dataset_manifest.v1.yaml"
DECLARATION_PATH = REPO_ROOT / "ai_platform" / "validation" / "final-holdout-v2-declaration.json"


def test_dataset_manifest_is_immutable_and_matches_canonical_holdout() -> None:
    raw = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    schema = json.loads(
        (ENGINE_ROOT / "schemas" / "dataset-manifest.v1.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(raw, schema)
    manifest = load_dataset_manifest(
        MANIFEST_PATH,
        protected_declaration_path=DECLARATION_PATH,
    )

    assert manifest.immutable is True
    assert manifest.final_holdout.locked is True
    assert manifest.final_holdout.used is False
    assert manifest.final_holdout.retuning_allowed is False
    assert manifest.final_holdout.timerange == "20260801-20260930"
    assert manifest.manifest_hash == manifest.canonical_sha256(exclude={"manifest_hash"})


def test_dataset_manifest_rejects_hash_tampering() -> None:
    raw = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    raw["symbols"] = ["ETH/USDT:USDT"]

    with pytest.raises(ValidationError, match="manifest_hash"):
        DatasetManifest.model_validate(raw)


def test_dataset_manifest_rejects_validation_overlap_with_holdout() -> None:
    raw = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    raw["validation"]["end"] = "2026-08-01T00:00:00Z"
    raw.pop("manifest_hash")

    with pytest.raises(ValidationError, match="protected final holdout"):
        DatasetManifest.create(**raw)


def test_holdout_declaration_mismatch_fails_closed() -> None:
    manifest = load_dataset_manifest(MANIFEST_PATH)
    declaration = json.loads(DECLARATION_PATH.read_text(encoding="utf-8"))
    declaration["final_holdout"]["timerange"] = "20261001-20261130"

    with pytest.raises(DatasetManifestError) as exc_info:
        validate_protected_holdout(manifest, declaration)

    assert exc_info.value.reason_code == "HOLDOUT_TIMERANGE_MISMATCH"
