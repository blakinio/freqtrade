from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SYMBOL_UNIVERSE_PATH = Path(
    "ai_platform/research/liquidations/symbol-universes-v1.json"
)
DEFAULT_SYMBOL_PROFILE = "liquid20-v1"


@dataclass(frozen=True)
class SymbolProfile:
    name: str
    frozen_at: str
    selection_basis: str
    symbols: tuple[str, ...]
    recommended_default_symbol_count: int
    broad_universe_review_threshold: int
    hard_max_symbol_count: int


def _required_int(payload: dict[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    if value <= 0:
        raise ValueError(f"{key} must be > 0")
    return value


def _required_text(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _validate_symbol(symbol: object) -> str:
    if not isinstance(symbol, str):
        raise ValueError("every symbol must be a string")
    normalized = symbol.strip()
    if normalized != normalized.upper():
        raise ValueError(f"symbol must be uppercase: {symbol!r}")
    if not normalized.endswith("USDT"):
        raise ValueError(f"symbol must be a USDT contract: {symbol!r}")
    if not normalized.isalnum():
        raise ValueError(f"symbol must be alphanumeric: {symbol!r}")
    return normalized


def load_symbol_profile(
    profile_name: str = DEFAULT_SYMBOL_PROFILE,
    *,
    universe_path: Path = DEFAULT_SYMBOL_UNIVERSE_PATH,
) -> SymbolProfile:
    payload = json.loads(universe_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("symbol universe root must be an object")
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported symbol universe schema_version")

    recommended_default_symbol_count = _required_int(
        payload,
        "recommended_default_symbol_count",
    )
    broad_universe_review_threshold = _required_int(
        payload,
        "broad_universe_review_threshold",
    )
    hard_max_symbol_count = _required_int(payload, "hard_max_symbol_count")
    if recommended_default_symbol_count > broad_universe_review_threshold:
        raise ValueError("recommended default exceeds broad-universe review threshold")
    if broad_universe_review_threshold > hard_max_symbol_count:
        raise ValueError("broad-universe review threshold exceeds hard maximum")

    profiles = payload.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("profiles must be a list")

    requested_name = profile_name.strip()
    for raw_profile in profiles:
        if not isinstance(raw_profile, dict):
            raise ValueError("every profile must be an object")
        if raw_profile.get("name") != requested_name:
            continue

        symbols_payload = raw_profile.get("symbols")
        if not isinstance(symbols_payload, list):
            raise ValueError("profile symbols must be a list")
        symbols = tuple(_validate_symbol(symbol) for symbol in symbols_payload)
        if not symbols:
            raise ValueError("profile must contain at least one symbol")
        if len(symbols) != len(set(symbols)):
            raise ValueError("profile contains duplicate symbols")
        if len(symbols) > hard_max_symbol_count:
            raise ValueError("profile exceeds hard_max_symbol_count")

        declared_count = _required_int(raw_profile, "symbol_count")
        if declared_count != len(symbols):
            raise ValueError("profile symbol_count does not match symbols")

        return SymbolProfile(
            name=_required_text(raw_profile, "name"),
            frozen_at=_required_text(raw_profile, "frozen_at"),
            selection_basis=_required_text(raw_profile, "selection_basis"),
            symbols=symbols,
            recommended_default_symbol_count=recommended_default_symbol_count,
            broad_universe_review_threshold=broad_universe_review_threshold,
            hard_max_symbol_count=hard_max_symbol_count,
        )

    raise KeyError(f"unknown symbol profile: {requested_name}")
