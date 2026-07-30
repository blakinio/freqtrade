export const MARKET_EVIDENCE_SOURCES = [
  "binance-usdm",
  "bybit-linear",
  "okx-swap",
] as const;

export type MarketEvidenceSource = (typeof MARKET_EVIDENCE_SOURCES)[number];
export type MarketEvidenceStatus = "LIVE" | "DEGRADED" | "STALE" | "BLOCKED" | "UNAVAILABLE";
export type MarketEvidenceRunState = "active" | "completed" | "failed";
export type MarketEvidenceQualityStatus = "healthy" | "degraded" | "stale" | "unavailable";

export interface MarketEvidenceAuthorityBoundary {
  execution_enabled: false;
  orders_submitted: 0;
  trading_credentials_present: false;
  model_execution_authorized: false;
  replay_authorized: false;
  performance_research_authorized: false;
  live_capital_authorized: false;
}

export interface MarketEvidenceSummary {
  schema_version: 1;
  status: MarketEvidenceStatus;
  updated_at_ms: number;
  active_run_id: string | null;
  latest_immutable_run_id: string | null;
  capture_start_ms: number | null;
  capture_end_ms: number | null;
  pre_roll_ms: number | null;
  completeness: number;
  instrument_count: number;
  completed_candle_count: number;
  market_quality_observation_count: number;
  gap_count: number;
  gap_duration_ms: number;
  wh01: {
    ready: boolean;
    market_evidence_ready: boolean;
    blocker_code: string | null;
    blocker_detail: string | null;
  };
  identities: {
    request_sha256: string | null;
    policy_sha256: string | null;
    code_sha: string | null;
    manifest_sha256: string | null;
  };
  authority: MarketEvidenceAuthorityBoundary;
}

export interface MarketEvidenceSourceStatus {
  source: MarketEvidenceSource;
  display_name: string;
  connected: boolean;
  healthy: boolean;
  last_event_at_ms: number | null;
  last_ticker_at_ms: number | null;
  last_completed_candle_at_ms: number | null;
  freshness_ms: number | null;
  active_symbols: number;
  errors: string[];
  reconnect_count: number;
  gaps: number;
  records_written: number;
  required_scope: string;
  liquidation_feed: "available" | "unavailable" | "unknown";
  candle_evidence: "available" | "unavailable";
  market_quality_evidence: "available" | "unavailable";
  instrument_history: "available" | "unavailable";
  wickhunter_available: boolean;
  exclusion_reason: string | null;
}

export interface MarketEvidenceInstrument {
  source: MarketEvidenceSource;
  symbol: string;
  native_symbol: string;
  market: string;
  active: boolean;
  included: boolean;
  latest_price: string | null;
  spread_bps: string | null;
  quote_volume_24h: string | null;
  last_completed_candle_at_ms: number | null;
  history_depth_rows: number;
  freshness_ms: number | null;
  reason_codes: string[];
  quality_status: MarketEvidenceQualityStatus;
}

export interface MarketEvidenceInstrumentQuery {
  source?: MarketEvidenceSource | "all";
  symbol?: string;
  market?: string;
  active?: boolean;
  included?: boolean;
  quality?: MarketEvidenceQualityStatus;
  sort?: "symbol" | "source" | "spread" | "volume" | "freshness";
  direction?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export interface MarketEvidenceInstrumentPage {
  schema_version: 1;
  items: MarketEvidenceInstrument[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface MarketEvidenceRun {
  run_id: string;
  state: MarketEvidenceRunState;
  capture_start_ms: number | null;
  capture_end_ms: number | null;
  pre_roll_ms: number | null;
  completeness: number;
  source_coverage: string[];
  instrument_count: number;
  completed_candle_count: number;
  market_quality_observation_count: number;
  gap_count: number;
  gap_duration_ms: number;
  verification_result: "accepted" | "rejected" | "pending";
  manifest_sha256: string | null;
  request_sha256: string | null;
  policy_sha256: string | null;
  code_sha: string | null;
  wh01_eligible: boolean;
  reason_codes: string[];
}

export interface MarketEvidenceRunPage {
  schema_version: 1;
  items: MarketEvidenceRun[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}
