import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "ai_platform" / "configs" / "freqai-baseline.example.json"
STRATEGY_PATH = ROOT / "ai_platform" / "strategies" / "AiBaselineStrategy.py"


def test_baseline_config_is_research_only() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert config["dry_run"] is True
    assert config["trading_mode"] == "spot"
    assert config["force_entry_enable"] is False
    assert config["exchange"]["key"] == ""
    assert config["exchange"]["secret"] == ""


def test_baseline_strategy_is_valid_python_and_long_only() -> None:
    source = STRATEGY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    strategy_classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "AiBaselineStrategy"
    ]
    assert len(strategy_classes) == 1

    assignments = {
        target.id: node.value
        for node in strategy_classes[0].body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }

    assert isinstance(assignments["can_short"], ast.Constant)
    assert assignments["can_short"].value is False
