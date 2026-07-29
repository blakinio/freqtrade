import type {
  ExperimentBundle,
  ExperimentComparison,
  ExperimentCreateRequest,
  ExperimentDetail,
  ExperimentSummary,
  StrategyLabDefinition,
} from "./strategy-lab-contracts";

const hash = "a".repeat(64);

export const fixtureStrategies: StrategyLabDefinition[] = [
  {
    strategy_id: "tv_supertrend_v1",
    strategy_version: "1.0.0",
    display_name: "TradingView-inspired Supertrend v1",
    source_type: "tradingview_inspired_clean_room",
    provenance: { parity_claim: false, license_boundary: "No proprietary Pine Script copied" },
    features: ["supertrend_direction.v1"],
    entry_rules: ["Confirmed direction flip to long", "Execution at next bar open"],
    exit_rules: ["Confirmed direction flip to short", "Execution at next bar open"],
    parameters: [
      { name: "atr_period", kind: "integer", default: 10, minimum: "2", maximum: "100", choices: [] },
      { name: "multiplier", kind: "number", default: 3, minimum: "0.5", maximum: "10", choices: [] },
      { name: "atr_type", kind: "enum", default: "rma", minimum: null, maximum: null, choices: ["rma", "sma"] },
      { name: "source", kind: "enum", default: "hl2", minimum: null, maximum: null, choices: ["hl2", "close", "ohlc4"] },
    ],
    timeframe_semantics: "Confirmed closed base-timeframe bars; next-bar-open fills.",
    warm_up: 12,
    confirmation_policy: "closed_bar",
    risk_defaults: { research_only: true, position_mode: "single_long" },
    supported_directions: ["long"],
  },
  {
    strategy_id: "tv_squeeze_momentum_v1",
    strategy_version: "1.0.0",
    display_name: "TradingView-inspired Squeeze Momentum v1",
    source_type: "tradingview_inspired_clean_room",
    provenance: { parity_claim: false, license_boundary: "No proprietary Pine Script copied" },
    features: ["squeeze_ratio.v1"],
    entry_rules: ["Squeeze release", "Positive momentum and slope", "Execution at next bar open"],
    exit_rules: ["Negative momentum or slope", "Execution at next bar open"],
    parameters: [
      { name: "bb_length", kind: "integer", default: 20, minimum: "5", maximum: "100", choices: [] },
      { name: "bb_mult", kind: "number", default: 2, minimum: "0.5", maximum: "4", choices: [] },
      { name: "kc_length", kind: "integer", default: 20, minimum: "5", maximum: "100", choices: [] },
      { name: "kc_mult", kind: "number", default: 1.5, minimum: "0.5", maximum: "4", choices: [] },
      { name: "use_true_range", kind: "boolean", default: true, minimum: null, maximum: null, choices: [] },
      { name: "compatibility_mode", kind: "enum", default: "corrected", minimum: null, maximum: null, choices: ["corrected"] },
    ],
    timeframe_semantics: "Confirmed closed base-timeframe bars; no HTF interpolation.",
    warm_up: 22,
    confirmation_policy: "closed_bar",
    risk_defaults: { research_only: true, position_mode: "single_long" },
    supported_directions: ["long"],
  },
];

function detail(id: string, parameters: Record<string, unknown>, profit: string): ExperimentDetail {
  return {
    experiment_id: id,
    tenant_id: "fixture-tenant",
    status: "COMPLETED",
    strategy_id: "tv_supertrend_v1",
    strategy_version: "1.0.0",
    pair: "BTC/USDT",
    timeframe: "15m",
    timerange: { start_at: "2026-01-01T00:00:00Z", end_at: "2026-01-01T09:30:00Z" },
    data_identity: hash,
    code_identity: hash,
    parameters,
    started_at: "2026-01-02T00:00:00Z",
    finished_at: "2026-01-02T00:00:01Z",
    trade_count: 1,
    wins: Number(profit) > 0 ? 1 : 0,
    losses: Number(profit) > 0 ? 0 : 1,
    win_rate: Number(profit) > 0 ? "1" : "0",
    profit_abs: profit,
    profit_pct: String(Number(profit) / 10000),
    max_drawdown: "0.031",
    average_trade: String(Number(profit) / 10000),
    exposure: "0.333",
    result_hash: hash,
    research_only: true,
    order_submission_performed: false,
  };
}

function bundle(value: ExperimentDetail): ExperimentBundle {
  const entry = value.parameters.atr_period === 4 ? "2026-01-01T04:30:00Z" : "2026-01-01T04:15:00Z";
  return {
    detail: value,
    trades: [
      {
        trade_id: `${value.experiment_id}-trade-1`,
        pair: value.pair,
        side: "long",
        entry_at: entry,
        exit_at: "2026-01-01T07:45:00Z",
        entry_price: "94",
        exit_price: "104",
        quantity: "106.2765957447",
        fee_abs: "21.06",
        profit_abs: value.profit_abs,
        profit_pct: value.profit_pct,
        entry_signal_id: `${value.experiment_id}-entry`,
        exit_signal_id: `${value.experiment_id}-exit`,
        entry_reason_codes: ["LAB_SUPERTREND_FLIP_LONG", "LAB_NEXT_BAR_OPEN"],
        exit_reason_codes: ["LAB_SUPERTREND_FLIP_EXIT", "LAB_NEXT_BAR_OPEN"],
      },
    ],
    signals: [
      {
        signal_id: `${value.experiment_id}-entry`,
        timestamp: entry,
        pair: value.pair,
        timeframe: value.timeframe,
        strategy_id: value.strategy_id,
        strategy_version: value.strategy_version,
        decision: "ENTER_LONG",
        matched_conditions: ["supertrend_flip", "supertrend_direction_long"],
        feature_values: { supertrend_direction: 1, supertrend_flip: true },
        parameter_values: value.parameters,
        reason_codes: ["LAB_SUPERTREND_FLIP_LONG", "LAB_NEXT_BAR_OPEN"],
        price: "92",
      },
      {
        signal_id: `${value.experiment_id}-exit`,
        timestamp: "2026-01-01T07:30:00Z",
        pair: value.pair,
        timeframe: value.timeframe,
        strategy_id: value.strategy_id,
        strategy_version: value.strategy_version,
        decision: "EXIT_LONG",
        matched_conditions: ["supertrend_flip", "supertrend_direction_short"],
        feature_values: { supertrend_direction: -1, supertrend_flip: true },
        parameter_values: value.parameters,
        reason_codes: ["LAB_SUPERTREND_FLIP_EXIT", "LAB_NEXT_BAR_OPEN"],
        price: "106",
      },
    ],
    equity: [
      { timestamp: "2026-01-01T00:00:00Z", equity: "10000", drawdown_pct: "0" },
      { timestamp: entry, equity: "9990", drawdown_pct: "0.001" },
      { timestamp: "2026-01-01T06:00:00Z", equity: "10600", drawdown_pct: "0" },
      { timestamp: "2026-01-01T07:45:00Z", equity: String(10000 + Number(value.profit_abs)), drawdown_pct: "0.031" },
    ],
  };
}

const baseline = detail("11111111-1111-5111-8111-111111111111", { atr_period: 3, multiplier: 1.5, atr_type: "rma", source: "hl2" }, "1019.6053946054");
const variant = detail("22222222-2222-5222-8222-222222222222", { atr_period: 4, multiplier: 1.2, atr_type: "rma", source: "hl2" }, "870.20");

const fixtureBundles = new Map<string, ExperimentBundle>([
  [baseline.experiment_id, bundle(baseline)],
  [variant.experiment_id, bundle(variant)],
]);

export function listFixtureStrategyLabExperiments(): ExperimentSummary[] {
  return [baseline, variant];
}

export function getFixtureStrategyLabBundle(experimentId: string): ExperimentBundle {
  return fixtureBundles.get(experimentId) ?? bundle(baseline);
}

export function createFixtureStrategyLabExperiment(request: ExperimentCreateRequest): ExperimentBundle {
  const created = detail(
    "33333333-3333-5333-8333-333333333333",
    request.parameter_overrides,
    request.strategy_id === "tv_supertrend_v1" ? "1019.6053946054" : "0",
  );
  created.strategy_id = request.strategy_id;
  created.strategy_version = request.strategy_version;
  created.pair = request.pair;
  created.timeframe = request.timeframe;
  created.timerange = request.timerange;
  return bundle(created);
}

export function compareFixtureStrategyLabExperiments(
  baselineId: string,
  variantId: string,
): ExperimentComparison {
  const first = getFixtureStrategyLabBundle(baselineId).detail;
  const second = getFixtureStrategyLabBundle(variantId).detail;
  const names = new Set([...Object.keys(first.parameters), ...Object.keys(second.parameters)]);
  const parameter_differences: Record<string, [unknown | null, unknown | null]> = {};
  for (const name of names) {
    if (first.parameters[name] !== second.parameters[name]) {
      parameter_differences[name] = [first.parameters[name] ?? null, second.parameters[name] ?? null];
    }
  }
  return {
    baseline_experiment_id: first.experiment_id,
    variant_experiment_id: second.experiment_id,
    metric_deltas: {
      trade_count: String(second.trade_count - first.trade_count),
      win_rate: String(Number(second.win_rate) - Number(first.win_rate)),
      profit_abs: String(Number(second.profit_abs) - Number(first.profit_abs)),
      profit_pct: String(Number(second.profit_pct) - Number(first.profit_pct)),
      max_drawdown: String(Number(second.max_drawdown) - Number(first.max_drawdown)),
    },
    parameter_differences,
  };
}
