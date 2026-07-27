from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts.bot_management.configuration import (
    BotManagementConfiguration,
)
from ai_platform.portal.contracts.bot_management.pagination import (
    BotManagementSortField,
    BoundedPagination,
)
from ai_platform.portal.contracts.bot_management.policies import (
    DcaPolicyVersion,
    DcaSizeMode,
    DcaStep,
    DcaTriggerBasis,
    EntryPolicyVersion,
    ExitPolicyVersion,
    GridAllocationMode,
    GridPolicyVersion,
    GridSpacing,
    MarketPolicyVersion,
    OrderType,
    PositionSizingMode,
    PositionSizingPolicyVersion,
    RuntimePolicyVersion,
    SignalAuthority,
    SignalCommand,
    SignalPolicyVersion,
    StopLossPolicy,
    TakeProfitLevel,
    TakeProfitPolicy,
    TrailingStopPolicy,
)
from ai_platform.portal.contracts.bot_management.templates import (
    CatalogVersionRef,
    MarketType,
    TradeDirection,
)
from ai_platform.portal.contracts.environment import Environment, ExecutionMode


NOW = datetime(2026, 7, 27, 9, 0, tzinfo=UTC)


def market_policy() -> MarketPolicyVersion:
    return MarketPolicyVersion(
        policy_id="market-v1",
        revision=1,
        pairs=("BTC/USDT", "ETH/USDT"),
        market_type=MarketType.SPOT,
        direction=TradeDirection.LONG,
        timeframe="5m",
    )


def entry_policy() -> EntryPolicyVersion:
    return EntryPolicyVersion(
        policy_id="entry-v1",
        revision=1,
        order_type=OrderType.MARKET,
        max_concurrent_positions=2,
    )


def sizing_policy() -> PositionSizingPolicyVersion:
    return PositionSizingPolicyVersion(
        policy_id="sizing-v1",
        revision=1,
        mode=PositionSizingMode.FIXED_QUOTE_AMOUNT,
        fixed_quote_amount=Decimal("25.00"),
        max_per_pair_allocation_percent=Decimal("20"),
        max_total_allocation_percent=Decimal("40"),
    )


def exit_policy() -> ExitPolicyVersion:
    return ExitPolicyVersion(
        policy_id="exit-v1",
        revision=1,
        take_profit=TakeProfitPolicy(
            levels=(
                TakeProfitLevel(
                    level_number=1,
                    profit_percent=Decimal("2.5"),
                    close_fraction=Decimal("0.5"),
                ),
                TakeProfitLevel(
                    level_number=2,
                    profit_percent=Decimal("5"),
                    close_fraction=Decimal("0.5"),
                ),
            )
        ),
        stop_loss=StopLossPolicy(loss_percent=Decimal("3")),
        trailing_stop=TrailingStopPolicy(
            activation_profit_percent=Decimal("2"),
            trail_distance_percent=Decimal("0.5"),
        ),
    )


def runtime_policy() -> RuntimePolicyVersion:
    return RuntimePolicyVersion(
        policy_id="runtime-v1",
        revision=1,
        runtime_version="freqtrade-2026.7",
        execution_mode=ExecutionMode.DRY_RUN,
        heartbeat_timeout_seconds=30,
        command_timeout_seconds=10,
        reconciliation_timeout_seconds=60,
    )


def configuration(**overrides: object) -> BotManagementConfiguration:
    values: dict[str, object] = {
        "configuration_id": "config-1",
        "tenant_id": "tenant-a",
        "bot_id": "bot-1",
        "revision": 7,
        "template_ref": CatalogVersionRef(catalog_id="template-grid", version="1"),
        "compatibility_decision_ref": "compat-1",
        "strategy_version": "strategy-v3",
        "model_version": "model-v2",
        "exchange_connection_ref": "connection-1",
        "market_policy": market_policy(),
        "entry_policy": entry_policy(),
        "position_sizing_policy": sizing_policy(),
        "exit_policy": exit_policy(),
        "risk_policy_version": "risk-v4",
        "runtime_policy": runtime_policy(),
        "environment": Environment.STAGING,
        "execution_mode": ExecutionMode.DRY_RUN,
        "created_by_actor_id": "actor-1",
        "created_at": NOW,
    }
    values.update(overrides)
    return BotManagementConfiguration(**values)


def test_unknown_fields_are_rejected_and_models_are_frozen() -> None:
    with pytest.raises(ValidationError):
        BoundedPagination(
            page_size=10,
            sort_field=BotManagementSortField.CREATED_AT,
            unexpected="nope",
        )

    page = BoundedPagination(page_size=10, sort_field=BotManagementSortField.CREATED_AT)
    with pytest.raises(ValidationError):
        page.page_size = 20


def test_canonical_serialization_is_deterministic_and_decimal_safe() -> None:
    first = configuration()
    second = configuration()

    assert first.canonical_json() == second.canonical_json()
    assert '"fixed_quote_amount":"25.00"' in first.canonical_json()
    assert first.canonical_json().startswith('{"bot_id"')


def test_invalid_decimal_values_fail_closed() -> None:
    invalid_values = (Decimal("NaN"), Decimal("Infinity"), Decimal("0"), Decimal("-1"))
    for value in invalid_values:
        with pytest.raises(ValidationError):
            PositionSizingPolicyVersion(
                policy_id="bad-sizing",
                revision=1,
                mode=PositionSizingMode.FIXED_QUOTE_AMOUNT,
                fixed_quote_amount=value,
                max_per_pair_allocation_percent=Decimal("20"),
                max_total_allocation_percent=Decimal("40"),
            )


def test_duplicate_and_unsorted_identifiers_fail_closed() -> None:
    with pytest.raises(ValidationError, match="duplicates"):
        MarketPolicyVersion(
            policy_id="market-bad",
            revision=1,
            pairs=("BTC/USDT", "BTC/USDT"),
            market_type=MarketType.SPOT,
            direction=TradeDirection.LONG,
            timeframe="5m",
        )

    with pytest.raises(ValidationError, match="sorted"):
        MarketPolicyVersion(
            policy_id="market-bad",
            revision=1,
            pairs=("ETH/USDT", "BTC/USDT"),
            market_type=MarketType.SPOT,
            direction=TradeDirection.LONG,
            timeframe="5m",
        )


def test_contradictory_dca_and_take_profit_fail_closed() -> None:
    with pytest.raises(ValidationError, match="strictly increasing"):
        DcaPolicyVersion(
            policy_id="dca-bad",
            revision=1,
            trigger_basis=DcaTriggerBasis.PRICE_DEVIATION_PERCENT,
            size_mode=DcaSizeMode.SIZE_MULTIPLIER,
            max_steps=2,
            max_cumulative_allocation_percent=Decimal("50"),
            steps=(
                DcaStep(
                    step_number=1,
                    trigger_deviation_percent=Decimal("5"),
                    size_value=Decimal("1.5"),
                ),
                DcaStep(
                    step_number=2,
                    trigger_deviation_percent=Decimal("5"),
                    size_value=Decimal("2"),
                ),
            ),
        )

    with pytest.raises(ValidationError, match="must not exceed 1"):
        TakeProfitPolicy(
            levels=(
                TakeProfitLevel(
                    level_number=1,
                    profit_percent=Decimal("2"),
                    close_fraction=Decimal("0.75"),
                ),
                TakeProfitLevel(
                    level_number=2,
                    profit_percent=Decimal("4"),
                    close_fraction=Decimal("0.5"),
                ),
            )
        )


def test_contradictory_stop_trailing_and_grid_fail_closed() -> None:
    with pytest.raises(ValidationError, match="requires an explicit stop-loss"):
        ExitPolicyVersion(
            policy_id="exit-bad",
            revision=1,
            trailing_stop=TrailingStopPolicy(
                activation_profit_percent=Decimal("2"),
                trail_distance_percent=Decimal("0.5"),
            ),
        )

    with pytest.raises(ValidationError, match="below the grid range"):
        GridPolicyVersion(
            policy_id="grid-bad",
            revision=1,
            lower_price=Decimal("100"),
            upper_price=Decimal("120"),
            level_count=5,
            spacing=GridSpacing.ARITHMETIC,
            allocation_mode=GridAllocationMode.TOTAL_QUOTE,
            total_quote_allocation=Decimal("500"),
            direction=TradeDirection.LONG,
            stop_loss_price=Decimal("105"),
        )


def test_configuration_rejects_dca_grid_and_duplicate_exit_sources() -> None:
    dca = DcaPolicyVersion(
        policy_id="dca-v1",
        revision=1,
        trigger_basis=DcaTriggerBasis.PRICE_DEVIATION_PERCENT,
        size_mode=DcaSizeMode.FIXED_QUOTE_AMOUNT,
        max_steps=1,
        max_cumulative_allocation_percent=Decimal("20"),
        steps=(
            DcaStep(
                step_number=1,
                trigger_deviation_percent=Decimal("5"),
                size_value=Decimal("20"),
            ),
        ),
    )
    grid = GridPolicyVersion(
        policy_id="grid-v1",
        revision=1,
        lower_price=Decimal("100"),
        upper_price=Decimal("120"),
        level_count=5,
        spacing=GridSpacing.ARITHMETIC,
        allocation_mode=GridAllocationMode.TOTAL_QUOTE,
        total_quote_allocation=Decimal("500"),
        direction=TradeDirection.LONG,
    )
    with pytest.raises(ValidationError, match="cannot be enabled together"):
        configuration(dca_policy=dca, grid_policy=grid)

    grid_with_tp = GridPolicyVersion(
        policy_id="grid-v2",
        revision=1,
        lower_price=Decimal("100"),
        upper_price=Decimal("120"),
        level_count=5,
        spacing=GridSpacing.ARITHMETIC,
        allocation_mode=GridAllocationMode.TOTAL_QUOTE,
        total_quote_allocation=Decimal("500"),
        direction=TradeDirection.LONG,
        take_profit_price=Decimal("125"),
    )
    with pytest.raises(ValidationError, match="both declare take profit"):
        configuration(grid_policy=grid_with_tp)


def test_signal_dca_command_requires_dca_policy() -> None:
    signal = SignalPolicyVersion(
        policy_id="signal-v1",
        revision=1,
        signal_schema_ref="schema-v1",
        allowed_commands=(SignalCommand.DCA,),
        authority=SignalAuthority.EXECUTION_AUTHORIZED,
        max_signal_age_seconds=60,
        replay_window_seconds=30,
    )
    with pytest.raises(ValidationError, match="requires a DCA policy"):
        configuration(signal_policy=signal)


def test_pagination_is_bounded() -> None:
    BoundedPagination(page_size=100, sort_field=BotManagementSortField.BOT_ID)
    with pytest.raises(ValidationError):
        BoundedPagination(page_size=101, sort_field=BotManagementSortField.BOT_ID)
    with pytest.raises(ValidationError):
        BoundedPagination(page_size=0, sort_field=BotManagementSortField.BOT_ID)
