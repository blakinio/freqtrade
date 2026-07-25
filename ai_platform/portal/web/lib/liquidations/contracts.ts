export const LIQUIDATION_SOURCES = ["bybit-linear", "binance-usdm"] as const;

export type LiquidationSource = (typeof LIQUIDATION_SOURCES)[number];
export type LiquidatedPositionSide = "long" | "short";
export type LiquidationDataMode = "historical" | "live" | "stale";
export type LiquidationAcceptanceStatus = "accepted" | "failed" | "in-progress" | "missing";

export interface PortalLiquidationEvent {
  schema_version: 1;
  source: LiquidationSource;
  source_event_id: string;
  symbol: string;
  liquidated_position_side: LiquidatedPositionSide;
  occurred_at_ms: number;
  received_at_ms: number;
  ingest_latency_ms: number;
  price: string;
  quantity: string;
  notional_usd: string;
}

export interface LiquidationQuery {
  source?: LiquidationSource | "all";
  symbol?: string;
  side?: LiquidatedPositionSide;
  since?: number;
  until?: number;
  limit?: number;
  cursor?: string;
}

export interface LiquidationPage {
  schema_version: 1;
  run_id: string;
  mode: LiquidationDataMode;
  events: PortalLiquidationEvent[];
  next_cursor: string | null;
  truncated: boolean;
  rejected_records: number;
}

export interface LiquidationWindowSummary {
  window: "5m" | "1h" | "24h";
  since_ms: number;
  until_ms: number;
  event_count: number;
  notional_usd: string;
  long: {
    event_count: number;
    notional_usd: string;
  };
  short: {
    event_count: number;
    notional_usd: string;
  };
  by_source: Record<
    LiquidationSource,
    {
      event_count: number;
      notional_usd: string;
    }
  >;
}

export interface LiquidationSymbolRanking {
  symbol: string;
  event_count: number;
  notional_usd: string;
  long_event_count: number;
  long_notional_usd: string;
  short_event_count: number;
  short_notional_usd: string;
  by_source: Record<
    LiquidationSource,
    {
      event_count: number;
      notional_usd: string;
    }
  >;
}

export interface LiquidationSummary {
  schema_version: 1;
  run_id: string;
  mode: LiquidationDataMode;
  anchor_at_ms: number;
  windows: LiquidationWindowSummary[];
  ranking_24h: LiquidationSymbolRanking[];
  truncated: boolean;
}

export interface LiquidationSourceHealth {
  events: number;
  observed_symbols: number;
  availability_ratio: number | null;
  disconnects_per_hour: number | null;
  last_event_at_ms: number | null;
}

export interface LiquidationAcceptanceEvidence {
  run_id: string;
  status: "accepted" | "failed";
  failed_gates: string[];
}

export interface LiquidationHealth {
  schema_version: 1;
  mode: LiquidationDataMode;
  run_id: string;
  acceptance_status: LiquidationAcceptanceStatus;
  failed_gates: string[];
  latest_completed_acceptance: LiquidationAcceptanceEvidence | null;
  active_sources: LiquidationSource[];
  observed_symbol_count: number;
  sources: Record<LiquidationSource, LiquidationSourceHealth>;
  last_event_at_ms: number | null;
  stale: boolean;
  refreshed_at_ms: number;
  truncated: boolean;
  research_preview: true;
  trading_authorized: false;
  source_semantics: Record<LiquidationSource, string>;
}
