from __future__ import annotations

import argparse
from pathlib import Path


def _replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def _replace_between(text: str, start: str, end: str, replacement: str, *, label: str) -> str:
    start_index = text.find(start)
    end_index = text.find(end, start_index + len(start))
    if start_index < 0 or end_index < 0 or end_index <= start_index:
        raise SystemExit(f"{label}: boundary mismatch")
    return text[:start_index] + replacement + text[end_index:]


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    legacy_start = text.find("\ndef _source_health(value: object) -> SourceHealth:")
    public_start = text.find("\ndef _public_url(")
    if legacy_start < 0 or public_start <= legacy_start:
        raise SystemExit("legacy snapshot boundary mismatch")
    loader = '''

def load_liquid20_snapshot(
    path: Path,
    *,
    now_ms: int,
    maximum_age_ms: int = DEFAULT_MAX_SOURCE_AGE_MS,
) -> Liquid20Snapshot:
    if maximum_age_ms < 1:
        raise CandidatePaperRuntimeOperatorError(
            "maximum Liquid20 age must be positive"
        )
    return _load_liquid20_live_root(
        path,
        now_ms=now_ms,
        maximum_age_ms=maximum_age_ms,
    )

'''
    text = text[:legacy_start] + loader + text[public_start:]

    marker = "\ndef _market_wide_liquidation_intensity("
    starts: list[int] = []
    offset = 0
    while True:
        index = text.find(marker, offset)
        if index < 0:
            break
        starts.append(index)
        offset = index + len(marker)
    if len(starts) != 2:
        raise SystemExit(f"unexpected intensity definition count: {len(starts)}")
    fetch_start = text.find("\ndef fetch_public_market_snapshot(", starts[1])
    if fetch_start <= starts[1]:
        raise SystemExit("duplicate intensity boundary mismatch")
    text = text[: starts[1]] + "\n" + text[fetch_start:]

    text = _replace_once(
        text,
        "    StrategyHypothesis,\n)",
        "    StrategyHypothesis,\n    TradeDirection,\n)",
        label="TradeDirection import",
    )
    text = _replace_once(
        text,
        '        maximum_leverage=Decimal("5"),',
        '        maximum_leverage=Decimal("15"),',
        label="candidate leverage ceiling",
    )
    text = _replace_once(
        text,
        "    histories = tuple(\n"
        "        _live_history(symbol, tuple(by_symbol[symbol])) for symbol in selected_symbols\n"
        "    )\n",
        "    histories = tuple(\n"
        "        _live_history(\n"
        "            symbol,\n"
        "            tuple(\n"
        "                sorted(\n"
        "                    by_symbol[symbol],\n"
        "                    key=lambda item: (item.received_at_ms, item.source_event_id),\n"
        "                )[-MAX_EVENTS_PER_SYMBOL:]\n"
        "            ),\n"
        "        )\n"
        "        for symbol in selected_symbols\n"
        "    )\n",
        label="bounded per-symbol history",
    )

    risk_helpers = '''

def _current_equity(state: Any, policy: ShadowRuntimePolicy) -> Decimal:
    unrealized = sum(
        (position.unrealized_pnl_quote for position in state.positions),
        Decimal("0"),
    )
    equity = (
        policy.simulated_initial_equity_quote
        + state.cumulative_realized_pnl_quote
        + unrealized
    )
    return max(equity, Decimal("0.00000001"))


def _consecutive_losses(state: Any) -> int:
    streak = 0
    ordered = sorted(
        state.closed_positions,
        key=lambda position: (position.closed_at_ms, position.closed_position_id),
        reverse=True,
    )
    for position in ordered:
        if position.realized_pnl_quote < 0:
            streak += 1
        else:
            break
    return streak


def _runtime_risk_context(
    *,
    state: Any,
    policy: ShadowRuntimePolicy,
    parameters: Any,
    symbol: str,
    observed_at_ms: int,
    market: PublicMarketSnapshot,
    model_drift: DriftState,
    data_drift: DriftState,
    circuit_breaker_active: bool,
) -> WickHunterRiskContext:
    equity = _current_equity(state, policy)
    symbol_exposure = Decimal("0")
    total_exposure = Decimal("0")
    long_exposure = Decimal("0")
    short_exposure = Decimal("0")
    normalized_symbol = symbol.upper()
    for position in state.positions:
        exposure = position.mark_price * position.quantity / equity
        total_exposure += exposure
        if position.symbol.upper() == normalized_symbol:
            symbol_exposure += exposure
        if position.side is TradeDirection.LONG:
            long_exposure += exposure
        else:
            short_exposure += exposure

    candidate_exposure = (
        max(parameters.base_risk_ratio, parameters.dca_total_risk_ratio)
        * parameters.leverage
    )
    day_start_ms = observed_at_ms - 86_400_000
    gross_daily_loss = sum(
        (
            -position.realized_pnl_quote
            for position in state.closed_positions
            if day_start_ms <= position.closed_at_ms <= observed_at_ms
            and position.realized_pnl_quote < 0
        ),
        Decimal("0"),
    )
    streak = _consecutive_losses(state)
    loss_cooldown = (
        observed_at_ms + parameters.cooldown_ms
        if streak >= _risk_limits().maximum_consecutive_losses
        else None
    )
    symbol_closes = [
        position.closed_at_ms
        for position in state.closed_positions
        if position.symbol.upper() == normalized_symbol
    ]
    symbol_cooldown = None
    if symbol_closes:
        candidate = max(symbol_closes) + parameters.cooldown_ms
        if candidate > observed_at_ms:
            symbol_cooldown = candidate

    return WickHunterRiskContext(
        evaluated_at_ms=observed_at_ms,
        global_kill_switch_active=False,
        circuit_breaker_active=circuit_breaker_active,
        model_drift=model_drift,
        data_drift=data_drift,
        projected_concurrent_positions=len(state.positions) + 1,
        projected_symbol_exposure_ratio=symbol_exposure + candidate_exposure,
        projected_correlated_exposure_ratio=total_exposure + candidate_exposure,
        projected_directional_exposure_ratio=(
            max(long_exposure, short_exposure) + candidate_exposure
        ),
        daily_loss_ratio=(gross_daily_loss / policy.simulated_initial_equity_quote),
        drawdown_ratio=state.drawdown_ratio,
        consecutive_losses=streak,
        consecutive_loss_cooldown_until_ms=loss_cooldown,
        symbol_cooldown_until_ms=symbol_cooldown,
        setup_still_valid=True,
        dca_adverse_condition_met=True,
        dca_timing_condition_met=True,
        spread_bps=market.spread_bps,
        quote_volume_usd=market.quote_volume_24h_usd,
        candidate_paper_validation_authorized=True,
    )

'''
    atomic_marker = "\ndef _atomic_health(path: Path, payload: dict[str, object]) -> None:\n"
    if text.count(atomic_marker) != 1:
        raise SystemExit("risk helper insertion marker mismatch")
    text = text.replace(atomic_marker, risk_helpers + atomic_marker, 1)

    fields_old = '''    public_market_base_url: str = DEFAULT_PUBLIC_MARKET_BASE_URL
    maximum_source_age_ms: int = DEFAULT_MAX_SOURCE_AGE_MS
    opener: OpenerDirector | None = None
    last_success_at_ms: int | None = None
'''
    fields_new = '''    public_market_base_url: str = DEFAULT_PUBLIC_MARKET_BASE_URL
    maximum_source_age_ms: int = DEFAULT_MAX_SOURCE_AGE_MS
    model_drift: DriftState = DriftState.HEALTHY
    data_drift: DriftState = DriftState.HEALTHY
    circuit_breaker_active: bool = False
    opener: OpenerDirector | None = None
    last_success_at_ms: int | None = None
'''
    text = _replace_once(text, fields_old, fields_new, label="operator control fields")

    compose = '''    def _compose_tick(
        self,
        *,
        liquid20: Liquid20Snapshot,
        markets: tuple[PublicMarketSnapshot, ...],
        observed_at_ms: int,
    ) -> ShadowRuntimeTick:
        market_by_symbol = {item.symbol: item for item in markets}
        if set(market_by_symbol) != set(liquid20.universe.selected_symbols):
            raise CandidatePaperRuntimeOperatorError(
                "public market symbols do not match the selected Liquid20 universe"
            )

        latest_state = self.service.runtime.state
        market_wide_liquidation_intensity = _market_wide_liquidation_intensity(
            liquid20.events,
            decision_timestamp_ms=observed_at_ms,
            burst_window_ms=self.service.binding.parameters.burst_window_ms,
        )
        requests: list[ShadowDecisionRequest] = []
        for symbol in liquid20.universe.selected_symbols:
            events = tuple(
                item for item in liquid20.events if item.symbol.upper() == symbol
            )
            if not events:
                continue
            market = market_by_symbol[symbol]
            requests.append(
                ShadowDecisionRequest(
                    bot_instance=self.service.binding.request.bot_instance,
                    mode=self.service.binding.request.mode,
                    events=events,
                    market=market.market_context(
                        market_wide_liquidation_intensity=(
                            market_wide_liquidation_intensity
                        )
                    ),
                    history=liquid20.history_for(symbol),
                    source_states=liquid20.source_states,
                    universe=liquid20.universe,
                    parameters=self.service.binding.parameters,
                    parameter_bounds=DEFAULT_RESEARCH_BOUNDS,
                    hypothesis=StrategyHypothesis.REVERSAL,
                    scorer=self.service.binding.scorer,
                    signal_memory=SignalMemory(),
                    risk_limits=_risk_limits(),
                    risk_context=_runtime_risk_context(
                        state=latest_state,
                        policy=self.service.runtime.policy,
                        parameters=self.service.binding.parameters,
                        symbol=symbol,
                        observed_at_ms=observed_at_ms,
                        market=market,
                        model_drift=self.model_drift,
                        data_drift=self.data_drift,
                        circuit_breaker_active=self.circuit_breaker_active,
                    ),
                    dataset_hash=self.service.binding.request.dataset_hash,
                    code_sha=self.service.binding.request.code_sha,
                )
            )
        return ShadowRuntimeTick(
            observed_at_ms=observed_at_ms,
            universe=liquid20.universe,
            decision_requests=tuple(requests),
            mark_prices=tuple(
                sorted((item.symbol, item.decision_price) for item in markets)
            ),
            source_states=liquid20.source_states,
            model_drift=self.model_drift,
            data_drift=self.data_drift,
            validation_state="collecting",
            retraining_state="disabled",
        )

'''
    text = _replace_between(
        text,
        "    def _compose_tick(\n",
        "    def _health_payload(\n",
        compose,
        label="compose tick replacement",
    )

    health_old = '''            "liquid20_snapshot_id": liquid20_snapshot_id,
            "error_code": error_code,
'''
    health_new = '''            "liquid20_snapshot_id": liquid20_snapshot_id,
            "model_drift": self.model_drift.value,
            "data_drift": self.data_drift.value,
            "circuit_breaker_active": self.circuit_breaker_active,
            "error_code": error_code,
'''
    text = _replace_once(text, health_old, health_new, label="truthful health controls")

    parser_and_main = '''def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Persistent fail-closed WickHunter candidate PAPER operator"
    )
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--activation-root", type=Path, required=True)
    parser.add_argument("--journal-root", type=Path, required=True)
    parser.add_argument("--liquid20-root", type=Path, required=True)
    parser.add_argument("--health-root", type=Path, required=True)
    parser.add_argument("--operator-commit", required=True)
    parser.add_argument("--public-market-base-url", default=DEFAULT_PUBLIC_MARKET_BASE_URL)
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--maximum-source-age-ms", type=int, default=DEFAULT_MAX_SOURCE_AGE_MS)
    parser.add_argument(
        "--model-drift",
        choices=tuple(item.value for item in DriftState),
        default=DriftState.HEALTHY.value,
    )
    parser.add_argument(
        "--data-drift",
        choices=tuple(item.value for item in DriftState),
        default=DriftState.HEALTHY.value,
    )
    parser.add_argument("--circuit-breaker-active", action="store_true")
    parser.add_argument("--once", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    assert_closed_authority_environment()
    for path, field in (
        (args.candidate_root, "candidate root"),
        (args.activation_root, "activation root"),
        (args.journal_root, "journal root"),
        (args.liquid20_root, "Liquid20 root"),
        (args.health_root, "health root"),
    ):
        _assert_regular_absolute(
            path,
            field=field,
            must_exist=field not in {"journal root", "health root"},
        )
    if not args.liquid20_root.is_dir():
        raise CandidatePaperRuntimeOperatorError(
            "Liquid20 root must be a regular directory"
        )
    args.journal_root.mkdir(parents=True, exist_ok=True)
    args.health_root.mkdir(parents=True, exist_ok=True)
    binding = build_candidate_paper_runtime_binding(
        candidate_root=args.candidate_root,
        activation_root=args.activation_root,
    )
    service = CandidatePaperRuntimeService(
        binding=binding,
        runtime_policy=_runtime_policy(),
        journal_root=args.journal_root,
    )
    operator = CandidatePaperRuntimeOperator(
        service=service,
        liquid20_root_path=args.liquid20_root,
        health_path=args.health_root / "health.json",
        operator_commit=args.operator_commit,
        public_market_base_url=args.public_market_base_url,
        maximum_source_age_ms=args.maximum_source_age_ms,
        model_drift=DriftState(args.model_drift),
        data_drift=DriftState(args.data_drift),
        circuit_breaker_active=args.circuit_breaker_active,
    )
    if args.once:
        operator.run_once()
        return 0
    operator.run_forever(poll_seconds=args.poll_seconds)
    return 0


'''
    text = _replace_between(
        text,
        "def _parser() -> argparse.ArgumentParser:\n",
        'if __name__ == "__main__":\n',
        parser_and_main,
        label="parser and main replacement",
    )

    required = (
        'LIVE_POINTER_NAME = "live-state-v1.json"',
        '"/fapi/v1/ticker/bookTicker"',
        '"atr_ratio"',
        '"market_wide_liquidation_intensity"',
        '"--liquid20-root"',
        '"--model-drift"',
        '"--data-drift"',
        '"--circuit-breaker-active"',
        "def _runtime_risk_context(",
        'maximum_leverage=Decimal("15")',
        "[-MAX_EVENTS_PER_SYMBOL:]",
    )
    forbidden = (
        "def _source_health(",
        "def _history_from_payload(",
        "if path.is_dir():",
        '"/fapi/v1/ticker/24hr"',
        '"--liquid20-snapshot"',
        'projected_symbol_exposure_ratio=Decimal("0")',
        'daily_loss_ratio=Decimal("0")',
    )
    if not all(value in text for value in required):
        raise SystemExit("required repaired operator contract is incomplete")
    if any(value in text for value in forbidden):
        raise SystemExit("legacy or under-reported operator contract remains")
    if text.count("def _market_wide_liquidation_intensity(") != 1:
        raise SystemExit("market-wide intensity definition is not unique")
    compile(text, str(path), "exec")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    patch(args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
