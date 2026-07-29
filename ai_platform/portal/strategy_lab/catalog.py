from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strategy_engine.domain.models import StrategyDefinition
from strategy_engine.dsl.validator import StrategyValidator

from ai_platform.portal.strategy_lab.schema import ParameterKind, StrategyLabDefinition


class StrategyCatalogError(ValueError):
    pass


class UnknownStrategyError(LookupError):
    pass


class StrategyLabCatalog:
    def __init__(self, definitions: tuple[StrategyLabDefinition, ...] | None = None) -> None:
        loaded = definitions if definitions is not None else _load_builtin_definitions()
        self._definitions = {(item.strategy_id, item.strategy_version): item for item in loaded}
        if len(self._definitions) != len(loaded):
            raise StrategyCatalogError("duplicate strategy identity")
        validator = StrategyValidator()
        for item in loaded:
            validator.validate(StrategyDefinition.model_validate(item.dsl))

    def list(self) -> tuple[StrategyLabDefinition, ...]:
        return tuple(self._definitions[key] for key in sorted(self._definitions))

    def get(self, strategy_id: str, strategy_version: str) -> StrategyLabDefinition:
        try:
            return self._definitions[(strategy_id, strategy_version)]
        except KeyError as exc:
            raise UnknownStrategyError(
                f"unknown strategy: {strategy_id}@{strategy_version}"
            ) from exc

    def resolve_parameters(
        self,
        definition: StrategyLabDefinition,
        overrides: dict[str, Any],
    ) -> dict[str, Any]:
        specs = {spec.name: spec for spec in definition.parameters}
        unknown = sorted(set(overrides) - set(specs))
        if unknown:
            raise StrategyCatalogError(f"unknown parameter(s): {', '.join(unknown)}")
        resolved: dict[str, Any] = {}
        for name, spec in specs.items():
            value = overrides.get(name, spec.default)
            if spec.kind is ParameterKind.INTEGER:
                if not isinstance(value, int) or isinstance(value, bool):
                    raise StrategyCatalogError(f"{name} must be an integer")
                numeric = value
            elif spec.kind is ParameterKind.NUMBER:
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise StrategyCatalogError(f"{name} must be numeric")
                numeric = float(value)
            elif spec.kind is ParameterKind.BOOLEAN:
                if not isinstance(value, bool):
                    raise StrategyCatalogError(f"{name} must be boolean")
                resolved[name] = value
                continue
            else:
                if value not in spec.choices:
                    raise StrategyCatalogError(f"{name} must be one of {list(spec.choices)}")
                resolved[name] = value
                continue
            if spec.minimum is not None and numeric < float(spec.minimum):
                raise StrategyCatalogError(f"{name} is below minimum {spec.minimum}")
            if spec.maximum is not None and numeric > float(spec.maximum):
                raise StrategyCatalogError(f"{name} is above maximum {spec.maximum}")
            resolved[name] = numeric
        return resolved


def _load_builtin_definitions() -> tuple[StrategyLabDefinition, ...]:
    root = Path(__file__).resolve().parents[3]
    strategy_dir = root / "ai_strategy_engine" / "strategies"
    paths = (
        strategy_dir / "tv_supertrend_v1.json",
        strategy_dir / "tv_squeeze_momentum_v1.json",
    )
    definitions: list[StrategyLabDefinition] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StrategyCatalogError(f"unable to load strategy definition {path}: {exc}") from exc
        definitions.append(StrategyLabDefinition.model_validate(payload))
    return tuple(definitions)
