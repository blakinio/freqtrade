import type {
  AuditEvent,
  BotInstance,
  CreateBotRequest,
  DashboardSnapshot,
  ExecutionActivityEntry,
  LearningHistoryEntry,
  ModelVersion,
  OperationalOrder,
  OperationalPosition,
  PerformanceSummary,
  PortalEnvironment,
  RiskDecisionRecord,
  TerminalIntentRequest,
  TerminalIntentResult,
  TradeAnalysis,
  TradeHistoryEntry,
  TradeInsight,
} from "./contracts";

const fixtureBots: BotInstance[] = [
  {
    bot_id: "bot-btc-dryrun-01",
    tenant_id: "tenant-demo",
    name: "BTC AI Dry Run",
    spec: {
      tenant_id: "tenant-demo",
      strategy_version: "ai-directional-v1",
      model_version: "model-validated-2026-07",
      risk_policy_version: "risk-default-v1",
      exchange_connection_ref: "exchange-simulated-kraken",
      pair_universe: ["BTC/USDT"],
      timeframe: "5m",
      capital_allocation: "1000",
      capital_currency: "USDT",
      runtime_version: "freqtrade-2026.7",
      config_revision: 1,
      environment: "test",
      execution_mode: "dry_run",
    },
    desired_state: "RUNNING",
    observed_state: "RUNNING",
  },
  {
    bot_id: "bot-eth-dryrun-02",
    tenant_id: "tenant-demo",
    name: "ETH Validation Bot",
    spec: {
      tenant_id: "tenant-demo",
      strategy_version: "ai-directional-v1",
      model_version: "model-validated-2026-07",
      risk_policy_version: "risk-default-v1",
      exchange_connection_ref: "exchange-simulated-kraken",
      pair_universe: ["ETH/USDT"],
      timeframe: "15m",
      capital_allocation: "750",
      capital_currency: "USDT",
      runtime_version: "freqtrade-2026.7",
      config_revision: 2,
      environment: "test",
      execution_mode: "dry_run",
    },
    desired_state: "PAUSED",
    observed_state: "PAUSED",
  },
];

const fixtureModels: ModelVersion[] = [
  {
    model_version_id: "model-validated-2026-07",
    tenant_id: "tenant-demo",
    model_family_id: "directional-lightgbm",
    artifact_id: "artifact-model-validated-2026-07",
    artifact_sha256: "1111111111111111111111111111111111111111111111111111111111111111",
    feature_schema_version_id: "features-v1",
    dataset_version_id: "dataset-pre-oos-v1",
    training_window: {
      start_at: "2026-03-01T00:00:00Z",
      end_at: "2026-05-01T00:00:00Z",
    },
    training_pipeline_version_id: "training-pipeline-v1",
    parameters: [],
    git_revision: "fixture-revision",
    created_at: "2026-07-20T10:00:00Z",
    lifecycle_state: "DRY_RUN",
    experiment_reference: {
      experiment_id: "experiment-fixture-1",
      tenant_id: "tenant-demo",
      run_id: "run-fixture-1",
    },
  },
];

const fixtureAnalyses: TradeAnalysis[] = [
  {
    analysis_id: "11111111-1111-4111-8111-111111111111",
    tenant_id: "tenant-demo",
    snapshot: {
      snapshot_id: "22222222-2222-4222-8222-222222222222",
      tenant_id: "tenant-demo",
      bot_id: "bot-btc-dryrun-01",
      trade_intent_id: "33333333-3333-4333-8333-333333333333",
      risk_decision_id: "44444444-4444-4444-8444-444444444444",
      config_revision: 1,
      strategy_version: "ai-directional-v1",
      model_version: "model-validated-2026-07",
      risk_policy_version: "risk-default-v1",
      source_runtime_id: "runtime-btc-01",
      pair: "BTC/USDT",
      side: "BUY",
      amount: "0.01",
      decision_at: "2026-07-22T12:00:00Z",
      evidence_ref: "evidence://fixture/trade-1",
      evidence_sha256: "2222222222222222222222222222222222222222222222222222222222222222",
    },
    outcome: {
      outcome_id: "55555555-5555-4555-8555-555555555555",
      tenant_id: "tenant-demo",
      trade_id: "trade-fixture-1",
      bot_id: "bot-btc-dryrun-01",
      source_runtime_id: "runtime-btc-01",
      pair: "BTC/USDT",
      realized_pnl: "12.40",
      fees: "0.80",
      exit_reason: "roi",
      opened_at: "2026-07-22T12:00:00Z",
      closed_at: "2026-07-22T13:00:00Z",
      reconciliation_status: "SYNCED",
      loss_exceeded_risk_budget: false,
    },
    diagnosis: {
      diagnosis_id: "66666666-6666-4666-8666-666666666666",
      tenant_id: "tenant-demo",
      snapshot_id: "22222222-2222-4222-8222-222222222222",
      outcome_id: "55555555-5555-4555-8555-555555555555",
      code: "PROFITABLE",
      reason_codes: ["REALIZED_PNL_NON_NEGATIVE"],
      evidence_links: ["evidence://fixture/trade-1", "trade:trade-fixture-1"],
      created_at: "2026-07-22T13:01:00Z",
    },
    insight: {
      insight_id: "77777777-7777-4777-8777-777777777777",
      tenant_id: "tenant-demo",
      diagnosis_id: "66666666-6666-4666-8666-666666666666",
      severity: "INFO",
      summary: "Trade closed with non-negative realized PNL.",
      synthesis_source: "DETERMINISTIC",
      evidence_links: ["evidence://fixture/trade-1", "trade:trade-fixture-1"],
      created_at: "2026-07-22T13:01:00Z",
    },
    created_at: "2026-07-22T13:01:00Z",
  },
];

const fixtureLearningHistory: LearningHistoryEntry[] = [
  {
    hypothesis: {
      hypothesis_id: "88888888-8888-4888-8888-888888888888",
      tenant_id: "tenant-demo",
      source_insight_id: "77777777-7777-4777-8777-777777777777",
      statement: "Validate whether the observed BTC setup remains stable across a broader pre-holdout window.",
      evidence_links: ["evidence://fixture/trade-1", "trade:trade-fixture-1"],
      created_by_actor_id: "actor-fixture",
      created_at: "2026-07-22T14:00:00Z",
    },
    experiments: [
      {
        experiment_id: "99999999-9999-4999-8999-999999999999",
        tenant_id: "tenant-demo",
        hypothesis_id: "88888888-8888-4888-8888-888888888888",
        evidence_window: {
          start_at: "2026-03-01T00:00:00Z",
          end_at: "2026-05-01T00:00:00Z",
        },
        autonomy_level: "L3",
        outcome: "POSITIVE",
        result_summary: "Fixture experiment produced a bounded candidate for review; no promotion occurred.",
        created_by_actor_id: "actor-fixture",
        created_at: "2026-07-22T15:00:00Z",
      },
    ],
    candidates: [
      {
        candidate_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        tenant_id: "tenant-demo",
        experiment_id: "99999999-9999-4999-8999-999999999999",
        model_family_id: "directional-lightgbm",
        candidate_model_version_id: "model-candidate-fixture-2",
        dataset_version_id: "dataset-pre-oos-v2",
        feature_schema_version_id: "features-v1",
        autonomy_level: "L4",
        promoted: false,
        assigned_to_bot: false,
        created_by_actor_id: "actor-fixture",
        created_at: "2026-07-22T16:00:00Z",
      },
    ],
  },
];

const fixtureOrders: OperationalOrder[] = [
  {
    tenant_id: "tenant-demo",
    bot_id: "bot-btc-dryrun-01",
    source_runtime_id: "runtime-btc-01",
    order_id: "fixture-order-1",
    execution_intent_id: "fixture-execution-intent-1",
    pair: "BTC/USDT",
    side: "BUY",
    state: "FILLED",
    amount: "0.01",
    created_at: "2026-07-22T12:00:00Z",
  },
];

const fixturePositions: OperationalPosition[] = [
  {
    tenant_id: "tenant-demo",
    bot_id: "bot-eth-dryrun-02",
    source_runtime_id: "runtime-eth-02",
    position_id: "fixture-position-1",
    pair: "ETH/USDT",
    side: "BUY",
    amount: "0.10",
    opened_at: "2026-07-23T10:00:00Z",
  },
];

const fixtureRiskEvents: RiskDecisionRecord[] = [
  {
    risk_decision_id: "44444444-4444-4444-8444-444444444444",
    tenant_id: "tenant-demo",
    trade_intent_id: "33333333-3333-4333-8333-333333333333",
    risk_policy_version: "risk-default-v1",
    decision: "APPROVED",
    reason_codes: ["RISK_APPROVED"],
    evaluated_limits: [
      {
        limit_name: "max_order_notional",
        configured_value: "1000",
        observed_value: "250",
        passed: true,
      },
    ],
    occurred_at: "2026-07-22T12:00:00Z",
    context: {
      request_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      correlation_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      causation_id: null,
    },
  },
];

const fixtureAuditEvents: AuditEvent[] = [
  {
    audit_id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
    occurred_at: "2026-07-22T11:59:00Z",
    actor_type: "user",
    actor_id: "actor-fixture",
    tenant_id: "tenant-demo",
    resource_type: "bot",
    resource_id: "bot-btc-dryrun-01",
    action: "bot.created",
    result: "SUCCEEDED",
    request_id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
    correlation_id: "ffffffff-ffff-4fff-8fff-ffffffffffff",
    causation_id: null,
    reason_code: null,
    details: { config_revision: 1 },
  },
  {
    audit_id: "12121212-1212-4212-8212-121212121212",
    occurred_at: "2026-07-22T12:00:00Z",
    actor_type: "user",
    actor_id: "actor-fixture",
    tenant_id: "tenant-demo",
    resource_type: "bot",
    resource_id: "bot-btc-dryrun-01",
    action: "trade.manual_intent",
    result: "SUCCEEDED",
    request_id: "13131313-1313-4313-8313-131313131313",
    correlation_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    causation_id: null,
    reason_code: null,
    details: { pair: "BTC/USDT" },
  },
];

export function listFixtureBots(): BotInstance[] {
  return structuredClone(fixtureBots);
}

export function createFixtureBot(request: CreateBotRequest): BotInstance {
  return {
    bot_id: request.bot_id,
    tenant_id: request.spec.tenant_id,
    name: request.name,
    spec: request.spec,
    desired_state: "CREATED",
    observed_state: "CREATED",
  };
}

export function fixtureDashboard(environment: PortalEnvironment): DashboardSnapshot {
  const bots = listFixtureBots();
  return {
    environment,
    freshnessLabel: "Fixture snapshot · deterministic E2E data",
    activeBots: bots.filter((bot) => bot.observed_state === "RUNNING").length,
    attentionBots: bots.filter((bot) => bot.observed_state === "ERROR").length,
    runtimeHealth: "healthy",
    modelHealth: "healthy",
    riskStatus: "normal",
    bots,
  };
}

export function listFixtureModels(): ModelVersion[] {
  return structuredClone(fixtureModels);
}

export function listFixtureTradeAnalyses(): TradeAnalysis[] {
  return structuredClone(fixtureAnalyses);
}

export function listFixtureInsights(): TradeInsight[] {
  return listFixtureTradeAnalyses().map((analysis) => analysis.insight);
}

export function listFixtureLearningHistory(): LearningHistoryEntry[] {
  return structuredClone(fixtureLearningHistory);
}

export function listFixtureOrders(): OperationalOrder[] {
  return structuredClone(fixtureOrders);
}

export function listFixturePositions(): OperationalPosition[] {
  return structuredClone(fixturePositions);
}

export function listFixtureTrades(): TradeHistoryEntry[] {
  return listFixtureTradeAnalyses().map((analysis) => ({
    tenant_id: analysis.tenant_id,
    bot_id: analysis.outcome.bot_id,
    trade_id: analysis.outcome.trade_id,
    source_runtime_id: analysis.outcome.source_runtime_id,
    pair: analysis.outcome.pair,
    side: analysis.snapshot.side,
    amount: analysis.snapshot.amount,
    realized_pnl: analysis.outcome.realized_pnl,
    fees: analysis.outcome.fees,
    exit_reason: analysis.outcome.exit_reason,
    opened_at: analysis.outcome.opened_at,
    closed_at: analysis.outcome.closed_at,
    reconciliation_status: analysis.outcome.reconciliation_status,
    analysis_id: analysis.analysis_id,
  }));
}

export function listFixturePerformance(): PerformanceSummary[] {
  return [
    {
      tenant_id: "tenant-demo",
      bot_id: "bot-btc-dryrun-01",
      realized_pnl: "12.40",
      fees: "0.80",
      net_pnl: "11.60",
      trade_count: 1,
      winning_trades: 1,
      losing_trades: 0,
      reconciliation_gaps: 0,
    },
  ];
}

export function listFixtureRiskEvents(): RiskDecisionRecord[] {
  return structuredClone(fixtureRiskEvents);
}

export function listFixtureAuditEvents(): AuditEvent[] {
  return structuredClone(fixtureAuditEvents);
}

export function listFixtureExecutionActivity(): ExecutionActivityEntry[] {
  return listFixtureAuditEvents()
    .filter((event) => event.action === "trade.manual_intent")
    .map((audit) => ({ audit }));
}

export function submitFixtureTerminalIntent(request: TerminalIntentRequest): TerminalIntentResult {
  const rejected = Number(request.amount) > 0.5;
  return {
    risk_decision: {
      risk_decision_id: "fixture-risk-decision-1",
      trade_intent_id: "fixture-trade-intent-1",
      risk_policy_version: "risk-default-v1",
      decision: rejected ? "REJECTED" : "APPROVED",
      reason_codes: [rejected ? "ORDER_NOTIONAL_LIMIT_EXCEEDED" : "RISK_APPROVED"],
    },
    execution_state: rejected ? "REJECTED" : "BLOCKED",
    execution_reason_code: rejected
      ? "ORDER_NOTIONAL_LIMIT_EXCEEDED"
      : "ORDER_SUBMISSION_NOT_IMPLEMENTED",
    order: null,
  };
}
