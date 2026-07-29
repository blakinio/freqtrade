from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


def _validate(example: Path, schema: Path) -> None:
    validator = Draft202012Validator(json.loads(schema.read_text(encoding="utf-8")))
    document = json.loads(example.read_text(encoding="utf-8"))
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    assert not errors, f"{example.name}: {[error.message for error in errors]}"


def test_all_examples_match_their_canonical_schema() -> None:
    root = Path(__file__).parents[2]
    _validate(
        root / "examples/feature_record.json",
        root / "schemas/feature-record.v1.schema.json",
    )
    _validate(
        root / "examples/signal_event.json",
        root / "schemas/signal-event.v1.schema.json",
    )
    strategy_schema = root / "schemas/strategy-definition.v1.schema.json"
    for path in sorted((root / "examples").glob("strategy_*.json")):
        _validate(path, strategy_schema)
