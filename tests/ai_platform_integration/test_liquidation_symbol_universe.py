from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_platform.research.liquidations.symbol_universe import (
    DEFAULT_SYMBOL_UNIVERSE_PATH,
    SymbolProfile,
    load_symbol_profile,
)
from ai_platform.scripts.liquidation_multi_source_runner import (
    _require_unused_targets,
    _target_paths,
    _validate_profile_scope,
)


def _write_universe(path: Path, *, symbols: list[str], declared_count: int | None = None) -> None:
    payload = {
        "schema_version": 1,
        "recommended_default_symbol_count": 20,
        "broad_universe_review_threshold": 50,
        "hard_max_symbol_count": 100,
        "profiles": [
            {
                "name": "test-v1",
                "frozen_at": "2026-07-24",
                "symbol_count": declared_count if declared_count is not None else len(symbols),
                "selection_basis": "test fixture",
                "symbols": symbols,
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_default_profile_is_frozen_twenty_symbol_usdt_universe() -> None:
    profile = load_symbol_profile(universe_path=DEFAULT_SYMBOL_UNIVERSE_PATH)

    assert profile.name == "liquid20-v1"
    assert profile.frozen_at == "2026-07-24"
    assert len(profile.symbols) == 20
    assert profile.symbols[:4] == ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT")
    assert len(profile.symbols) == len(set(profile.symbols))
    assert all(symbol.endswith("USDT") and symbol == symbol.upper() for symbol in profile.symbols)


def test_loader_rejects_duplicate_symbols(tmp_path: Path) -> None:
    universe_path = tmp_path / "universe.json"
    _write_universe(universe_path, symbols=["BTCUSDT", "BTCUSDT"])

    with pytest.raises(ValueError, match="duplicate"):
        load_symbol_profile("test-v1", universe_path=universe_path)


def test_loader_rejects_declared_count_mismatch(tmp_path: Path) -> None:
    universe_path = tmp_path / "universe.json"
    _write_universe(universe_path, symbols=["BTCUSDT", "ETHUSDT"], declared_count=3)

    with pytest.raises(ValueError, match="symbol_count"):
        load_symbol_profile("test-v1", universe_path=universe_path)


def test_loader_rejects_non_usdt_or_lowercase_symbols(tmp_path: Path) -> None:
    universe_path = tmp_path / "universe.json"
    _write_universe(universe_path, symbols=["btcusdt"])

    with pytest.raises(ValueError, match="uppercase"):
        load_symbol_profile("test-v1", universe_path=universe_path)

    _write_universe(universe_path, symbols=["BTCUSD"])
    with pytest.raises(ValueError, match="USDT"):
        load_symbol_profile("test-v1", universe_path=universe_path)


def test_broad_profile_requires_explicit_capacity_override() -> None:
    profile = SymbolProfile(
        name="broad-v1",
        frozen_at="2026-07-24",
        selection_basis="test",
        symbols=tuple(f"ASSET{index}USDT" for index in range(51)),
        recommended_default_symbol_count=20,
        broad_universe_review_threshold=50,
        hard_max_symbol_count=100,
    )

    with pytest.raises(ValueError, match="allow-broad-universe"):
        _validate_profile_scope(profile, allow_broad_universe=False)

    _validate_profile_scope(profile, allow_broad_universe=True)


def test_require_new_output_checks_every_multi_source_target(tmp_path: Path) -> None:
    paths = _target_paths(tmp_path)
    _require_unused_targets(paths)

    paths["manifest"].parent.mkdir(parents=True)
    paths["manifest"].write_text("{}", encoding="utf-8")

    with pytest.raises(FileExistsError, match="multi-source output targets"):
        _require_unused_targets(paths)
