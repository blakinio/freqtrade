
import json
from pathlib import Path

from jsonschema import Draft202012Validator


def test_all_strategy_examples_match_schema() -> None:
    root = Path(__file__).parents[2]
    schema = json.loads((root / "schemas/strategy-definition.v1.schema.json").read_text())
    validator = Draft202012Validator(schema)
    for path in sorted((root / "examples").glob("strategy_*.json")):
        document = json.loads(path.read_text())
        errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
        assert not errors, f"{path.name}: {[error.message for error in errors]}"
