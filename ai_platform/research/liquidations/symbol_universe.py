from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SYMBOL_UNIVERSE_PATH = Path(
    "ai_platform/research/liquidations/symbol-universes-v1.json"
)
DEFAULT_SYMBOL_PROFILE = "liquid20-v1"


@dataclass(frozen=True, slots=True)
class SymbolProfile:
    name: str
    frozen_at: str
    selection_basis: str
    symbols: tuple[str, ...]
    recommended_default_symbol_count: int
    broad_universe_review_threshold: int
    hard_max_symbol_count: int


def _required_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    if value <= 0:
        raise ValueError(f"{key} must be > 0")
    return value


def _required_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{key} must be non-empty")
    return normalized


def _validate_symbol(symbol: object) -> str:
    if not isinstance(symbol, str):
        raise TypeError("every symbol must be a string")
    normalized = symbol.strip()
    if normalized != normalized.upper():
        raise ValueError(f"symbol must be uppercase: {symbol!r}")
    if not normalized.endswith("USDT"):
        raise ValueError(f"symbol must be a USDT contract: {symbol!r}")
    if not normalized.isalnum():
        raise ValueError(f"symbol must be alphanumeric: {symbol!r}")
    return normalized


def _load_catalog(universe_path: Path) -> Mapping[str, object]:
    payload = json.loads(universe_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("symbol universe root must be an object")
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported symbol universe schema_version")
    return payload


def _parse_limits(payload: Mapping[str, object]) -> tuple[int, int, int]:
    recommended = _required_int(payload, "recommended_default_symbol_count")
    review_threshold = _required_int(payload, "broad_universe_review_threshold")
    hard_maximum = _required_int(payload, "hard_max_symbol_count")
    if recommended > review_threshold:
        raise ValueError("recommended default exceeds broad-universe review threshold")
    if review_threshold > hard_maximum:
        raise ValueError("broad-universe review threshold exceeds hard maximum")
    return recommended, review_threshold, hard_maximum


def _find_profile(profiles: Sequence[object], requested_name: str) -> Mapping[str, object]:
    for raw_profile in profiles:
        if not isinstance(raw_profile, dict):
            raise TypeError("every profile must be an object")
        if raw_profile.get("name") == requested_name:
            return raw_profile
    raise KeyError(f"unknown symbol profile: {requested_name}")


def _parse_symbols(raw_profile: Mapping[str, object], *, hard_maximum: int) -> tuple[str, ...]:
    symbols_payload = raw_profile.get("symbols")
    if not isinstance(symbols_payload, list):
        raise TypeError("profile symbols must be a list")
    symbols = tuple(_validate_symbol(symbol) for symbol in symbols_payload)
    if not symbols:
        raise ValueError("profile must contain at least one symbol")
    if len(symbols) != len(set(symbols)):
        raise ValueError("profile contains duplicate symbols")
    if len(symbols) > hard_maximum:
        raise ValueError("profile exceeds hard_max_symbol_count")
    if _required_int(raw_profile, "symbol_count") != len(symbols):
        raise ValueError("profile symbol_count does not match symbols")
    return symbols


def load_symbol_profile(
    profile_name: str = DEFAULT_SYMBOL_PROFILE,
    *,
    universe_path: Path = DEFAULT_SYMBOL_UNIVERSE_PATH,
) -> SymbolProfile:
    payload = _load_catalog(universe_path)
    recommended, review_threshold, hard_maximum = _parse_limits(payload)
    profiles = payload.get("profiles")
    if not isinstance(profiles, list):
        raise TypeError("profiles must be a list")

    raw_profile = _find_profile(profiles, profile_name.strip())
    symbols = _parse_symbols(raw_profile, hard_maximum=hard_maximum)
    return SymbolProfile(
        name=_required_text(raw_profile, "name"),
        frozen_at=_required_text(raw_profile, "frozen_at"),
        selection_basis=_required_text(raw_profile, "selection_basis"),
        symbols=symbols,
        recommended_default_symbol_count=recommended,
        broad_universe_review_threshold=review_threshold,
        hard_max_symbol_count=hard_maximum,
    )
