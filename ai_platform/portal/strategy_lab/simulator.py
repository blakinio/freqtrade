from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Any
from uuid import UUID

from ai_platform.portal.strategy_lab.schema import (
    Candle,
    EquityPoint,
    ExperimentCreateRequest,
    ExperimentResult,
    ExperimentStatus,
    ExperimentTrade,
    SignalDecision,
    SignalExplanation,
    StrategyLabDefinition,
)
import pandas as pd
from pydantic import JsonValue
from strategy_engine.features.squeeze import squeeze_features
from strategy_engine.features.supertrend import supertrend_features


getcontext().prec = 28


class StrategySimulationError(ValueError):
    pass


class MissingMarketDataError(StrategySimulationError):
    pass


class TimeIntegrityError(StrategySimulationError):
    pass


@dataclass(frozen=True)
class PendingAction:
    decision: SignalDecision
    signal: SignalExplanation


@dataclass
class OpenPosition:
    entry_at: datetime
    entry_price: Decimal
    quantity: Decimal
    entry_cost: Decimal
    entry_fee: Decimal
    entry_signal: SignalExplanation


class DeterministicStrategySimulator:
    CODE_VERSION = "ase-01-deterministic-simulator-v1"

    def run(
        self,
        *,
        experiment_id: UUID,
        tenant_id: str,
        request: ExperimentCreateRequest,
        definition: StrategyLabDefinition,
        parameters: dict[str, Any],
        candles: tuple[Candle, ...],
        started_at: datetime,
        finished_at: datetime,
    ) -> ExperimentResult:
        ordered = self._validate_candles(request, candles)
        frame = _to_frame(ordered)
        features = self._features(definition.strategy_id, frame, parameters)
        data_identity = _sha256_json([candle.model_dump(mode="json") for candle in ordered])
        code_identity = _sha256_json(
            {"version": self.CODE_VERSION, "dsl": definition.dsl, "parameters": parameters}
        )

        cash = request.starting_balance
        position: OpenPosition | None = None
        pending: PendingAction | None = None
        trades: list[ExperimentTrade] = []
        signals: list[SignalExplanation] = []
        equity_points: list[EquityPoint] = []
        holding_bars = 0
        peak_equity = cash

        dynamic_warm_up = self._warm_up(definition, parameters)
        for index, candle in enumerate(ordered):
            if pending is not None:
                if pending.decision is SignalDecision.ENTER_LONG and position is None:
                    position, cash = self._enter(
                        candle,
                        cash,
                        request.fee_rate,
                        request.slippage_rate,
                        pending.signal,
                    )
                elif pending.decision is SignalDecision.EXIT_LONG and position is not None:
                    trade, cash = self._exit(
                        candle,
                        position,
                        request.fee_rate,
                        request.slippage_rate,
                        pending.signal,
                    )
                    trades.append(trade)
                    position = None
                pending = None

            if position is not None:
                holding_bars += 1
            equity = cash + (
                position.quantity * candle.close if position is not None else Decimal(0)
            )
            peak_equity = max(peak_equity, equity)
            drawdown = Decimal(0) if peak_equity == 0 else (peak_equity - equity) / peak_equity
            equity_points.append(
                EquityPoint(timestamp=candle.timestamp, equity=equity, drawdown_pct=drawdown)
            )

            if index < dynamic_warm_up - 1 or index >= len(ordered) - 1:
                continue
            signal = self._evaluate_signal(
                definition,
                parameters,
                candle,
                features.iloc[index],
                position is not None,
            )
            if signal is not None:
                signals.append(signal)
                pending = PendingAction(signal.decision, signal)

        if position is not None:
            last = ordered[-1]
            forced_signal = _signal(
                candle=last,
                definition=definition,
                parameters=parameters,
                decision=SignalDecision.EXIT_LONG,
                matched_conditions=("timerange_end",),
                feature_values={},
                reason_codes=("LAB_EXIT_TIMERANGE_END",),
            )
            signals.append(forced_signal)
            trade, cash = self._exit_at_close(last, position, request.fee_rate, forced_signal)
            trades.append(trade)
            final_drawdown = (
                Decimal(0) if peak_equity == 0 else (peak_equity - cash) / peak_equity
            )
            equity_points[-1] = EquityPoint(
                timestamp=last.timestamp,
                equity=cash,
                drawdown_pct=final_drawdown,
            )

        wins = sum(1 for trade in trades if trade.profit_abs > 0)
        losses = sum(1 for trade in trades if trade.profit_abs <= 0)
        profit_abs = cash - request.starting_balance
        profit_pct = profit_abs / request.starting_balance
        average_trade = (
            sum((trade.profit_pct for trade in trades), Decimal(0)) / len(trades)
            if trades
            else Decimal(0)
        )
        win_rate = Decimal(wins) / len(trades) if trades else Decimal(0)
        exposure = Decimal(holding_bars) / len(ordered)
        max_drawdown = max(
            (point.drawdown_pct for point in equity_points),
            default=Decimal(0),
        )

        payload = {
            "experiment_id": experiment_id,
            "tenant_id": tenant_id,
            "status": ExperimentStatus.COMPLETED,
            "strategy_id": definition.strategy_id,
            "strategy_version": definition.strategy_version,
            "pair": request.pair,
            "timeframe": request.timeframe,
            "timerange": request.timerange,
            "data_identity": data_identity,
            "code_identity": code_identity,
            "parameters": parameters,
            "started_at": started_at,
            "finished_at": finished_at,
            "trade_count": len(trades),
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "profit_abs": profit_abs,
            "profit_pct": profit_pct,
            "max_drawdown": max_drawdown,
            "average_trade": average_trade,
            "exposure": exposure,
            "equity_curve": tuple(equity_points),
            "trades": tuple(trades),
            "signal_explanations": tuple(signals),
            "research_only": True,
            "order_submission_performed": False,
        }
        canonical = ExperimentResult.model_construct(**payload, result_hash="0" * 64)
        result_hash = _sha256_json(canonical.model_dump(mode="json", exclude={"result_hash"}))
        return ExperimentResult(**payload, result_hash=result_hash)

    @staticmethod
    def _validate_candles(
        request: ExperimentCreateRequest, candles: tuple[Candle, ...]
    ) -> tuple[Candle, ...]:
        if not candles:
            raise MissingMarketDataError("no market data available for experiment")
        ordered = tuple(sorted(candles, key=lambda candle: candle.timestamp))
        timestamps: set[datetime] = set()
        for candle in ordered:
            if candle.timestamp in timestamps:
                raise TimeIntegrityError("duplicate candle timestamp")
            timestamps.add(candle.timestamp)
            if candle.pair != request.pair or candle.timeframe != request.timeframe:
                raise TimeIntegrityError("candle identity does not match experiment request")
            if not candle.is_closed:
                raise TimeIntegrityError("unclosed candle is not available to the strategy")
            if not candle.is_confirmed:
                raise TimeIntegrityError("unconfirmed timeframe candle is not available")
            if not request.timerange.start_at <= candle.timestamp <= request.timerange.end_at:
                raise TimeIntegrityError("candle lies outside requested timerange")
        return ordered

    @staticmethod
    def _features(
        strategy_id: str, frame: pd.DataFrame, parameters: dict[str, Any]
    ) -> pd.DataFrame:
        if strategy_id == "tv_supertrend_v1":
            return supertrend_features(frame, **parameters)
        if strategy_id == "tv_squeeze_momentum_v1":
            return squeeze_features(frame, **parameters)
        raise StrategySimulationError(f"unsupported strategy: {strategy_id}")

    @staticmethod
    def _warm_up(definition: StrategyLabDefinition, parameters: dict[str, Any]) -> int:
        period_candidates = [
            value
            for name, value in parameters.items()
            if name.endswith(("length", "period"))
            if isinstance(value, int)
        ]
        return max((definition.warm_up, *(value + 2 for value in period_candidates)))

    @staticmethod
    def _evaluate_signal(
        definition: StrategyLabDefinition,
        parameters: dict[str, Any],
        candle: Candle,
        row: pd.Series,
        has_position: bool,
    ) -> SignalExplanation | None:
        values = {name: _json_value(value) for name, value in row.items()}
        if definition.strategy_id == "tv_supertrend_v1":
            flip = values.get("supertrend_flip") is True
            direction = values.get("supertrend_direction")
            if not has_position and flip and direction == 1:
                return _signal(
                    candle=candle,
                    definition=definition,
                    parameters=parameters,
                    decision=SignalDecision.ENTER_LONG,
                    matched_conditions=("supertrend_flip", "supertrend_direction_long"),
                    feature_values=values,
                    reason_codes=("LAB_SUPERTREND_FLIP_LONG", "LAB_NEXT_BAR_OPEN"),
                )
            if has_position and flip and direction == -1:
                return _signal(
                    candle=candle,
                    definition=definition,
                    parameters=parameters,
                    decision=SignalDecision.EXIT_LONG,
                    matched_conditions=("supertrend_flip", "supertrend_direction_short"),
                    feature_values=values,
                    reason_codes=("LAB_SUPERTREND_FLIP_EXIT", "LAB_NEXT_BAR_OPEN"),
                )
            return None

        release = values.get("squeeze_release") is True
        momentum = _number(values.get("linreg_momentum"))
        slope = _number(values.get("momentum_slope"))
        if not has_position and release and momentum > 0 and slope > 0:
            return _signal(
                candle=candle,
                definition=definition,
                parameters=parameters,
                decision=SignalDecision.ENTER_LONG,
                matched_conditions=("squeeze_release", "momentum_positive", "slope_positive"),
                feature_values=values,
                reason_codes=("LAB_SQUEEZE_RELEASE_LONG", "LAB_NEXT_BAR_OPEN"),
            )
        if has_position and (momentum < 0 or slope < 0):
            conditions = tuple(
                condition
                for condition, matched in (
                    ("momentum_negative", momentum < 0),
                    ("slope_negative", slope < 0),
                )
                if matched
            )
            return _signal(
                candle=candle,
                definition=definition,
                parameters=parameters,
                decision=SignalDecision.EXIT_LONG,
                matched_conditions=conditions,
                feature_values=values,
                reason_codes=("LAB_SQUEEZE_MOMENTUM_EXIT", "LAB_NEXT_BAR_OPEN"),
            )
        return None

    @staticmethod
    def _enter(
        candle: Candle,
        cash: Decimal,
        fee_rate: Decimal,
        slippage_rate: Decimal,
        signal: SignalExplanation,
    ) -> tuple[OpenPosition, Decimal]:
        entry_price = candle.open * (Decimal(1) + slippage_rate)
        quantity = cash / (entry_price * (Decimal(1) + fee_rate))
        notional = quantity * entry_price
        fee = notional * fee_rate
        total_cost = notional + fee
        return (
            OpenPosition(
                entry_at=candle.timestamp,
                entry_price=entry_price,
                quantity=quantity,
                entry_cost=total_cost,
                entry_fee=fee,
                entry_signal=signal,
            ),
            cash - total_cost,
        )

    @staticmethod
    def _exit(
        candle: Candle,
        position: OpenPosition,
        fee_rate: Decimal,
        slippage_rate: Decimal,
        signal: SignalExplanation,
    ) -> tuple[ExperimentTrade, Decimal]:
        exit_price = candle.open * (Decimal(1) - slippage_rate)
        return _close_position(candle.timestamp, exit_price, position, fee_rate, signal)

    @staticmethod
    def _exit_at_close(
        candle: Candle,
        position: OpenPosition,
        fee_rate: Decimal,
        signal: SignalExplanation,
    ) -> tuple[ExperimentTrade, Decimal]:
        return _close_position(candle.timestamp, candle.close, position, fee_rate, signal)


def _close_position(
    exit_at: datetime,
    exit_price: Decimal,
    position: OpenPosition,
    fee_rate: Decimal,
    signal: SignalExplanation,
) -> tuple[ExperimentTrade, Decimal]:
    gross = position.quantity * exit_price
    exit_fee = gross * fee_rate
    proceeds = gross - exit_fee
    profit_abs = proceeds - position.entry_cost
    profit_pct = profit_abs / position.entry_cost
    trade_id = _stable_id(
        "trade",
        position.entry_signal.signal_id,
        signal.signal_id,
        str(position.entry_price),
        str(exit_price),
    )
    trade = ExperimentTrade(
        trade_id=trade_id,
        pair=signal.pair,
        entry_at=position.entry_at,
        exit_at=exit_at,
        entry_price=position.entry_price,
        exit_price=exit_price,
        quantity=position.quantity,
        fee_abs=position.entry_fee + exit_fee,
        profit_abs=profit_abs,
        profit_pct=profit_pct,
        entry_signal_id=position.entry_signal.signal_id,
        exit_signal_id=signal.signal_id,
        entry_reason_codes=position.entry_signal.reason_codes,
        exit_reason_codes=signal.reason_codes,
    )
    return trade, proceeds


def _signal(
    *,
    candle: Candle,
    definition: StrategyLabDefinition,
    parameters: dict[str, Any],
    decision: SignalDecision,
    matched_conditions: tuple[str, ...],
    feature_values: dict[str, JsonValue],
    reason_codes: tuple[str, ...],
) -> SignalExplanation:
    signal_id = _stable_id(
        "signal",
        definition.strategy_id,
        definition.strategy_version,
        candle.pair,
        candle.timeframe,
        candle.timestamp.isoformat(),
        decision.value,
        json.dumps(parameters, sort_keys=True, separators=(",", ":")),
    )
    return SignalExplanation(
        signal_id=signal_id,
        timestamp=candle.timestamp,
        pair=candle.pair,
        timeframe=candle.timeframe,
        strategy_id=definition.strategy_id,
        strategy_version=definition.strategy_version,
        decision=decision,
        matched_conditions=matched_conditions,
        feature_values=feature_values,
        parameter_values=parameters,
        reason_codes=reason_codes,
        price=candle.close,
    )


def _to_frame(candles: tuple[Candle, ...]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [float(candle.open) for candle in candles],
            "high": [float(candle.high) for candle in candles],
            "low": [float(candle.low) for candle in candles],
            "close": [float(candle.close) for candle in candles],
            "volume": [float(candle.volume) for candle in candles],
        },
        index=pd.DatetimeIndex([candle.timestamp for candle in candles]),
    )


def _json_value(value: Any) -> JsonValue:
    if value is pd.NA or value is None:
        return None
    if isinstance(value, bool):
        return value
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _number(value: JsonValue | None) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
