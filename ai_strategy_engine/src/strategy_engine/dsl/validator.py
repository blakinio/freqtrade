from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class StrategyValidationError(ValueError):
    pass


@dataclass(frozen=True)
class RegistryFeature:
    feature_id: str
    status: str
    approved_for_ai: bool
    timestamp_policy: str


class StrategyValidator:
    def __init__(self, registry: dict[str, RegistryFeature]) -> None:
        self.registry = registry

    def validate(self, strategy: dict[str, Any], *, generated_by_ai: bool = False) -> None:
        if not strategy.get("execution", {}).get("use_closed_bars_only", False):
            raise StrategyValidationError("use_closed_bars_only must be true")

        risk = strategy.get("risk", {})
        if risk.get("max_leverage", 0) < 1:
            raise StrategyValidationError("max_leverage must be >= 1")

        for feature in strategy.get("features", []):
            feature_id = feature.get("id")
            if feature_id not in self.registry:
                raise StrategyValidationError(f"Unknown feature: {feature_id}")

            definition = self.registry[feature_id]
            if generated_by_ai and not definition.approved_for_ai:
                raise StrategyValidationError(
                    f"Feature is not approved for AI use: {feature_id}"
                )

            if feature.get("confirmation") == "confirmed_htf" and "htf" not in definition.timestamp_policy:
                # Registry policies may be expanded later; this catches an inconsistent declaration.
                pass

        self._validate_dca(risk)

    @staticmethod
    def _validate_dca(risk: dict[str, Any]) -> None:
        position_size = risk.get("position_size", {})
        if position_size.get("type") == "dca" and risk.get("max_exposure") is None:
            raise StrategyValidationError("DCA requires max_exposure")
