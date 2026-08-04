from __future__ import annotations

from pathlib import Path


CURRENT_PRODUCT_HEAD = "b8dad79ac650839e4eb77820f3cf7ae7657f6450"
BASE_PATCH_COMMIT = "bec0b0f8c424771e7b0c6fabf0ef623d8e2085bd"


def _replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def _replace_between(
    text: str,
    start: str,
    end: str,
    replacement: str,
    *,
    label: str,
) -> str:
    start_index = text.find(start)
    end_index = text.find(end, start_index + len(start))
    if start_index < 0 or end_index < 0 or end_index <= start_index:
        raise SystemExit(f"{label}: boundary mismatch")
    return text[:start_index] + replacement + text[end_index:]


def _patch_operator(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        'LIVE_POINTER_NAME = "live-state-v1.json"\n',
        'LIVE_POINTER_NAME = "live-state-v1.json"\n'
        'LIQUID20_LIVE_CONTRACT = "liquid20-live-state-v1"\n',
        label="exact Liquid20 contract constant",
    )
    text = _replace_once(
        text,
        '    if not contract:\n'
        '        raise CandidatePaperRuntimeOperatorError("Liquid20 live contract is empty")\n',
        '    if contract != LIQUID20_LIVE_CONTRACT:\n'
        '        raise CandidatePaperRuntimeOperatorError(\n'
        '            "Liquid20 live contract mismatch"\n'
        '        )\n',
        label="exact Liquid20 contract validation",
    )
    text = _replace_once(
        text,
        '        policy_version="liquid20-live-state-v1",',
        "        policy_version=LIQUID20_LIVE_CONTRACT,",
        label="universe policy identity",
    )

    public_url = '''def _public_url(base_url: str, path: str, parameters: dict[str, object]) -> str:
    parsed = urlparse(base_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise CandidatePaperRuntimeOperatorError(
            "public market base URL is not allowed"
        ) from exc
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or not parsed.hostname
        or port not in {None, 443}
    ):
        raise CandidatePaperRuntimeOperatorError("public market base URL is not allowed")
    if parsed.hostname.lower() != "fapi.binance.com":
        raise CandidatePaperRuntimeOperatorError("public market host is not allowlisted")
    return f"{base_url.rstrip('/')}{path}?{urlencode(parameters)}"


'''
    text = _replace_between(
        text,
        "def _public_url(",
        "def _read_public_json(",
        public_url,
        label="public URL boundary",
    )

    risk_context = '''def _runtime_risk_context(
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
    loss_cooldown = None
    if streak >= _risk_limits().maximum_consecutive_losses:
        latest_loss_closed_at_ms = max(
            position.closed_at_ms for position in state.closed_positions
        )
        loss_cooldown = latest_loss_closed_at_ms + parameters.cooldown_ms
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
    text = _replace_between(
        text,
        "def _runtime_risk_context(",
        "def _atomic_health(",
        risk_context,
        label="non-sliding risk cooldown",
    )

    health_payload = '''    def _health_payload(
        self,
        *,
        status: str,
        checked_at_ms: int,
        liquid20_snapshot_id: str | None,
        runtime_health: str,
        circuit_breaker_reasons: tuple[str, ...],
        error_code: str | None,
        error_message: str | None,
    ) -> dict[str, object]:
        if runtime_health not in {"healthy", "degraded", "fail_closed"}:
            raise CandidatePaperRuntimeOperatorError("runtime health is invalid")
        canonical_breaker_reasons = tuple(sorted(set(circuit_breaker_reasons)))
        state = self.service.runtime.state
        request = self.service.binding.request
        payload: dict[str, object] = {
            "schema_version": HEALTH_SCHEMA_VERSION,
            "status": status,
            "checked_at_ms": checked_at_ms,
            "last_success_at_ms": self.last_success_at_ms,
            "operator_commit": self.operator_commit,
            "binding_id": self.service.binding.binding_id,
            "run_id": request.run_id,
            "window_start_ms": request.window_start_ms,
            "window_end_ms": request.window_end_ms,
            "generation": state.generation,
            "last_observed_at_ms": state.last_observed_at_ms,
            "liquid20_snapshot_id": liquid20_snapshot_id,
            "runtime_health": runtime_health,
            "model_drift": self.model_drift.value,
            "data_drift": self.data_drift.value,
            "circuit_breaker_active": bool(canonical_breaker_reasons),
            "circuit_breaker_reasons": list(canonical_breaker_reasons),
            "error_code": error_code,
            "error_message": None if error_message is None else error_message[:240],
            **ZERO_AUTHORITY,
        }
        payload["health_sha256"] = canonical_sha256(payload)
        return payload

'''
    text = _replace_between(
        text,
        "    def _health_payload(\n",
        "    def run_once(\n",
        health_payload,
        label="runtime health payload",
    )

    run_once = '''    def run_once(self, *, observed_at_ms: int | None = None) -> int:
        now_ms = time.time_ns() // 1_000_000 if observed_at_ms is None else observed_at_ms
        request = self.service.binding.request
        if not request.window_start_ms <= now_ms < request.window_end_ms:
            raise CandidatePaperRuntimeOperatorError(
                "current time is outside the immutable activation window"
            )
        liquid20 = load_liquid20_snapshot(
            self.liquid20_root_path,
            now_ms=now_ms,
            maximum_age_ms=self.maximum_source_age_ms,
        )
        markets = tuple(
            fetch_public_market_snapshot(
                symbol=symbol,
                observed_at_ms=now_ms,
                base_url=self.public_market_base_url,
                opener=self.opener,
            )
            for symbol in liquid20.universe.selected_symbols
        )
        tick = self._compose_tick(
            liquid20=liquid20,
            markets=markets,
            observed_at_ms=now_ms,
        )
        result = self.service.step(tick)
        breaker_reasons = set(result.snapshot.circuit_breaker_reasons)
        if self.circuit_breaker_active:
            breaker_reasons.add("operator_circuit_breaker_active")
        canonical_breaker_reasons = tuple(sorted(breaker_reasons))
        runtime_health = (
            "fail_closed"
            if canonical_breaker_reasons
            else result.snapshot.health.value
        )
        self.last_success_at_ms = now_ms
        _atomic_health(
            self.health_path,
            self._health_payload(
                status="healthy",
                checked_at_ms=now_ms,
                liquid20_snapshot_id=liquid20.snapshot_id,
                runtime_health=runtime_health,
                circuit_breaker_reasons=canonical_breaker_reasons,
                error_code=None,
                error_message=None,
            ),
        )
        return result.state.generation

'''
    text = _replace_between(
        text,
        "    def run_once(\n",
        "    def publish_failure(\n",
        run_once,
        label="truthful successful health publication",
    )

    publish_failure = '''    def publish_failure(self, error: BaseException, *, checked_at_ms: int) -> None:
        _atomic_health(
            self.health_path,
            self._health_payload(
                status="fail_closed",
                checked_at_ms=checked_at_ms,
                liquid20_snapshot_id=None,
                runtime_health="fail_closed",
                circuit_breaker_reasons=(),
                error_code=type(error).__name__,
                error_message=str(error),
            ),
        )

'''
    text = _replace_between(
        text,
        "    def publish_failure(\n",
        "    def run_forever(\n",
        publish_failure,
        label="fail-closed health publication",
    )

    run_forever = '''    def run_forever(self, *, poll_seconds: int) -> None:
        if not 60 <= poll_seconds <= 900:
            raise CandidatePaperRuntimeOperatorError(
                "poll cadence must be within 60..900 seconds"
            )
        while True:
            checked_at_ms = time.time_ns() // 1_000_000
            try:
                self.run_once(observed_at_ms=checked_at_ms)
            except Exception as exc:  # noqa: BLE001
                self.publish_failure(exc, checked_at_ms=checked_at_ms)
            time.sleep(poll_seconds)


'''
    text = _replace_between(
        text,
        "    def run_forever(\n",
        "def _parser()",
        run_forever,
        label="unexpected exception fail-closed boundary",
    )

    parser_and_main = '''def _boolean(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("boolean value must be true or false")


def _parser() -> argparse.ArgumentParser:
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
    parser.add_argument(
        "--circuit-breaker-active",
        type=_boolean,
        default=False,
    )
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
        "def _parser()",
        'if __name__ == "__main__":',
        parser_and_main,
        label="bounded circuit-breaker CLI",
    )

    required = (
        'LIQUID20_LIVE_CONTRACT = "liquid20-live-state-v1"',
        "contract != LIQUID20_LIVE_CONTRACT",
        "port not in {None, 443}",
        "latest_loss_closed_at_ms + parameters.cooldown_ms",
        '"runtime_health": runtime_health',
        '"circuit_breaker_reasons": list(canonical_breaker_reasons)',
        'breaker_reasons.add("operator_circuit_breaker_active")',
        "except Exception as exc",
        'type=_boolean',
    )
    forbidden = (
        'raise CandidatePaperRuntimeOperatorError("Liquid20 live contract is empty")',
        "observed_at_ms + parameters.cooldown_ms",
        '"circuit_breaker_active": self.circuit_breaker_active',
        'action="store_true"',
    )
    if not all(marker in text for marker in required):
        raise SystemExit("final operator repair contract is incomplete")
    if any(marker in text for marker in forbidden):
        raise SystemExit("a superseded operator contract remains")
    compile(text, str(path), "exec")
    path.write_text(text, encoding="utf-8")


def _patch_tests(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        "    execution_enabled: bool = False,\n) -> Path:\n",
        "    execution_enabled: bool = False,\n"
        '    contract: str = "liquid20-live-state-v1",\n'
        ") -> Path:\n",
        label="test live contract input",
    )
    text = _replace_once(
        text,
        '        "contract": "liquid20-live-state-v1",',
        '        "contract": contract,',
        label="test live contract payload",
    )
    text = _replace_once(
        text,
        '        ("authority", "forbidden authority"),\n'
        '        ("source", "source does not match"),\n',
        '        ("authority", "forbidden authority"),\n'
        '        ("contract", "contract mismatch"),\n'
        '        ("source", "source does not match"),\n',
        label="contract tamper case",
    )
    text = _replace_once(
        text,
        '    elif mutation == "authority":\n'
        '        _write_live_root(root, execution_enabled=True)\n'
        "    else:\n",
        '    elif mutation == "authority":\n'
        '        _write_live_root(root, execution_enabled=True)\n'
        '    elif mutation == "contract":\n'
        '        _write_live_root(root, contract="liquid20-live-state-v0")\n'
        "    else:\n",
        label="contract tamper fixture",
    )
    text = _replace_once(
        text,
        '    with pytest.raises(CandidatePaperRuntimeOperatorError, match="forbidden"):\n'
        '        assert_closed_authority_environment({"HTTPS_PROXY": "https://proxy.invalid"})\n',
        '    with pytest.raises(CandidatePaperRuntimeOperatorError, match="allowed"):\n'
        '        fetch_public_market_snapshot(\n'
        '            symbol="BTCUSDT",\n'
        '            observed_at_ms=NOW_MS,\n'
        '            base_url="https://fapi.binance.com:8443",\n'
        '            opener=cast(Any, _Opener()),\n'
        '        )\n'
        '    with pytest.raises(CandidatePaperRuntimeOperatorError, match="forbidden"):\n'
        '        assert_closed_authority_environment({"HTTPS_PROXY": "https://proxy.invalid"})\n',
        label="non-standard public port test",
    )

    cooldown_test = '''def test_consecutive_loss_cooldown_is_anchored_to_latest_loss() -> None:
    latest_loss_closed_at_ms = NOW_MS - 100_000
    closed_positions = tuple(
        SimpleNamespace(
            closed_at_ms=latest_loss_closed_at_ms - index * 1_000,
            closed_position_id=f"{index + 1:064x}",
            symbol="BTCUSDT",
            realized_pnl_quote=Decimal("-10"),
        )
        for index in range(5)
    )
    state = SimpleNamespace(
        positions=(),
        closed_positions=closed_positions,
        cumulative_realized_pnl_quote=Decimal("-50"),
        drawdown_ratio=Decimal("0.01"),
    )
    policy = SimpleNamespace(simulated_initial_equity_quote=Decimal("10000"))
    expected_until = latest_loss_closed_at_ms + INITIAL_COMPATIBILITY_PRIOR.cooldown_ms

    active = _runtime_risk_context(
        state=state,
        policy=cast(Any, policy),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        symbol="BTCUSDT",
        observed_at_ms=NOW_MS,
        market=_market(),
        model_drift=DriftState.HEALTHY,
        data_drift=DriftState.HEALTHY,
        circuit_breaker_active=False,
    )
    expired = _runtime_risk_context(
        state=state,
        policy=cast(Any, policy),
        parameters=INITIAL_COMPATIBILITY_PRIOR,
        symbol="BTCUSDT",
        observed_at_ms=NOW_MS + 300_000,
        market=_market(observed_at_ms=NOW_MS + 300_000),
        model_drift=DriftState.HEALTHY,
        data_drift=DriftState.HEALTHY,
        circuit_breaker_active=False,
    )

    assert active.consecutive_losses == 5
    assert active.consecutive_loss_cooldown_until_ms == expected_until
    assert expired.consecutive_loss_cooldown_until_ms == expected_until
    assert expected_until > active.evaluated_at_ms
    assert expected_until <= expired.evaluated_at_ms


'''
    text = _replace_once(
        text,
        "def _service(*, mode: BotMode = BotMode.PAPER) -> Any:\n",
        cooldown_test + "def _service(*, mode: BotMode = BotMode.PAPER) -> Any:\n",
        label="non-sliding cooldown regression",
    )
    text = _replace_once(
        text,
        '        liquid20_snapshot_id=None,\n'
        '        error_code="SyntheticError",\n',
        '        liquid20_snapshot_id=None,\n'
        '        runtime_health="fail_closed",\n'
        '        circuit_breaker_reasons=("operator_circuit_breaker_active",),\n'
        '        error_code="SyntheticError",\n',
        label="health contract test arguments",
    )
    text = _replace_once(
        text,
        '    assert payload["circuit_breaker_active"] is True\n',
        '    assert payload["runtime_health"] == "fail_closed"\n'
        '    assert payload["circuit_breaker_active"] is True\n'
        '    assert payload["circuit_breaker_reasons"] == [\n'
        '        "operator_circuit_breaker_active"\n'
        '    ]\n',
        label="health contract assertions",
    )
    text = _replace_once(
        text,
        '            "--circuit-breaker-active",\n',
        '            "--circuit-breaker-active",\n'
        '            "true",\n',
        label="bounded circuit-breaker CLI test",
    )
    text = _replace_once(
        text,
        '    assert source.count("def _market_wide_liquidation_intensity(") == 1\n',
        '    assert source.count("def _market_wide_liquidation_intensity(") == 1\n'
        '    assert "except Exception as exc" in source\n'
        '    assert args.circuit_breaker_active is True\n',
        label="unexpected exception and breaker source assertions",
    )
    text = _replace_once(
        text,
        '    assert "--liquid20-root" in compose\n',
        '    assert "--liquid20-root" in compose\n'
        '    assert "CIRCUIT_BREAKER_ACTIVE" in compose\n',
        label="Compose breaker control test",
    )
    compile(text, str(path), "exec")
    path.write_text(text, encoding="utf-8")


def _patch_compose(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        "      - --data-drift\n"
        "      - ${DATA_DRIFT:-healthy}\n",
        "      - --data-drift\n"
        "      - ${DATA_DRIFT:-healthy}\n"
        "      - --circuit-breaker-active\n"
        "      - ${CIRCUIT_BREAKER_ACTIVE:-false}\n",
        label="Compose circuit-breaker control",
    )
    path.write_text(text, encoding="utf-8")


def _patch_readme(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        "The operator accepts only the deployed directory contract. It validates the active-run "
        "pointer, state/run identity, collector and source heartbeats, configured-source state, "
        "event/source identity, availability time, path safety, and zero-authority fields. Legacy "
        "single-file snapshot input is not accepted.",
        "The operator accepts only the exact `liquid20-live-state-v1` deployed directory contract. "
        "It validates the active-run pointer, state/run identity, collector and source heartbeats, "
        "configured-source state, event/source identity, availability time, path safety, and "
        "zero-authority fields. Legacy single-file snapshot input and contract substitution are "
        "not accepted.",
        label="README exact live contract",
    )
    text = _replace_once(
        text,
        "HTTPS GET is restricted in process to `https://fapi.binance.com`.",
        "HTTPS GET is restricted in process to `https://fapi.binance.com` on the standard TLS "
        "port 443.",
        label="README exact public endpoint",
    )
    text = _replace_once(
        text,
        "The immutable activation authorizes candidate validation only. It never authorizes "
        "execution. The risk context derives projected exposure, daily loss, drawdown, and "
        "consecutive losses from the simulated journal. `MODEL_DRIFT` and `DATA_DRIFT` default to "
        "`healthy`; a separately reviewed deployment request may set an explicit enum value for "
        "bounded acceptance exercises.",
        "The immutable activation authorizes candidate validation only. It never authorizes "
        "execution. The risk context derives projected exposure, daily loss, drawdown, and "
        "consecutive losses from the simulated journal. Consecutive-loss cooldown is anchored to "
        "the latest closed loss and therefore expires instead of sliding on every tick. "
        "`MODEL_DRIFT` and `DATA_DRIFT` default to `healthy`; `CIRCUIT_BREAKER_ACTIVE` defaults to "
        "`false`. A separately reviewed deployment request may set these bounded controls for "
        "acceptance exercises.",
        label="README risk controls",
    )
    text = _replace_once(
        text,
        "It reports exact operator, binding, run, window, generation, source, drift, breaker, and "
        "zero-authority state.",
        "It reports exact operator, binding, run, window, generation, runtime health, canonical "
        "circuit-breaker reasons, drift, and zero-authority state.",
        label="README truthful health contract",
    )
    path.write_text(text, encoding="utf-8")


def patch_bundle(root: Path) -> None:
    operator = root / "operator.py"
    tests = root / "tests.py"
    compose = root / "compose.yaml"
    readme = root / "README.md"
    healthcheck = root / "paper_runtime_healthcheck.py"
    _patch_operator(operator)
    _patch_tests(tests)
    _patch_compose(compose)
    _patch_readme(readme)
    for path in (operator, tests, healthcheck):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
