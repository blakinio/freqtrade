from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def replace_exact(text: str, old: str, new: str, *, count: int = 1) -> str:
    if text.count(old) != count:
        raise RuntimeError(f"expected {count} occurrence(s) of repair anchor")
    return text.replace(old, new, count)


def prepare_test_package() -> None:
    path = ROOT / "tests" / "ai_platform_integration" / "__init__.py"
    path.write_text('"""AI Platform integration tests."""\n', encoding="utf-8")


def repair_dsl_tests() -> None:
    path = ROOT / "ai_strategy_engine" / "tests" / "integration" / "test_registry_dsl.py"
    text = path.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        "from pathlib import Path\n\nimport pytest",
        "from pathlib import Path\nfrom typing import cast\n\nimport pytest",
    )
    text = replace_exact(
        text,
        '    features = list(document["features"])  # type: ignore[arg-type]',
        "    features = [\n"
        "        dict(feature)\n"
        '        for feature in cast(list[dict[str, object]], document["features"])\n'
        "    ]",
        count=2,
    )
    text = replace_exact(
        text,
        '    features[0] = {**features[0], "timeframe": "1h"}  # type: ignore[arg-type]',
        '    features[0] = {**features[0], "timeframe": "1h"}',
    )
    path.write_text(text, encoding="utf-8")


def repair_adapter() -> None:
    path = ROOT / "ai_platform" / "research" / "strategy_engine" / "ase00_adapter.py"
    text = path.read_text(encoding="utf-8")
    squeeze = '''            columns = (
                "squeeze_ratio",
                "squeeze_state",
                "squeeze_duration",
                "bars_since_release",
                "linreg_momentum",
                "momentum_slope",
                "momentum_acceleration",
            )
            value = _row_mapping(squeeze, -1, columns)
'''
    text = replace_exact(text, squeeze, squeeze.replace("columns", "squeeze_columns"))
    text = replace_exact(
        text,
        "_row_mapping(squeeze, -2, columns)",
        "_row_mapping(squeeze, -2, squeeze_columns)",
    )
    supertrend = '''            columns = (
                "supertrend_band",
                "supertrend_direction",
                "supertrend_flip",
                "supertrend_distance_atr",
            )
            value = _row_mapping(supertrend, -1, columns)
'''
    text = replace_exact(
        text,
        supertrend,
        supertrend.replace("columns", "supertrend_columns"),
    )
    text = replace_exact(
        text,
        "_row_mapping(supertrend, -2, columns)",
        "_row_mapping(supertrend, -2, supertrend_columns)",
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    prepare_test_package()
    repair_dsl_tests()
    repair_adapter()


if __name__ == "__main__":
    main()
