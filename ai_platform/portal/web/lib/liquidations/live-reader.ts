import { lstat, readdir, readFile, stat } from "node:fs/promises";
import { resolve, sep } from "node:path";

import {
  LIQUIDATION_HEALTH_SOURCES,
  type LiquidationDataMode,
  type LiquidationHealth,
  type LiquidationHealthSource,
  type LiquidationPage,
  type LiquidationQuery,
  type LiquidationSource,
  type LiquidationSourceHealth,
  type LiquidationSummary,
} from "./contracts";
import { LiquidationDataUnavailableError, LiquidationReadModel } from "./reader";

const LIVE_CONTRACT = "liquidation-live-state-v1";
const LIVE_STATE_FILE = "live-state-v1.json";
const RUN_ID_PATTERN = /^liquid20-\d{8}T\d{6}Z-\d+$/;
const MAX_METADATA_BYTES = 2 * 1024 * 1024;
const SOURCE_SEMANTICS: Record<LiquidationHealthSource, string> = {
  "bybit-linear": "All liquidation events published by Bybit linear allLiquidation.",
  "binance-usdm":
    "Latest Binance USD-M forceOrder event per symbol in each approximately 1000 ms window.",
  "okx-swap":
    "Public OKX SWAP liquidation-orders events normalized with verified public ctVal metadata.",
};

interface LiveSourceState {
  configured: boolean;
  connected: boolean;
  last_event_at_ms: number | null;
  last_event_received_at_ms: number | null;
  last_heartbeat_at_ms: number | null;
  ingest_lag_ms: number | null;
  reconnect_count: number;
  observed_symbol_count: number;
  subscription_symbol_count: number;
  events_written: number;
  error_count: number;
  parse_error_count: number;
  latest_error: string | null;
}

interface LiveState {
  run_id: string;
  run_state: "active" | "completed";
  collector_started_at_ms: number;
  collector_heartbeat_at_ms: number;
  last_event_at_ms: number | null;
  last_event_received_at_ms: number | null;
  sources: Record<LiquidationHealthSource, LiveSourceState>;
  execution_enabled: false;
  trading_authorized: false;
  trading_credentials_present: false;
  orders_submitted: 0;
}

export interface LiquidationLiveReadModelOptions {
  dataRoot: string;
  maxEvents?: number;
  collectorStaleAfterMs?: number;
  collectorOfflineAfterMs?: number;
  eventStaleAfterMs?: number;
  sourceStaleAfterMs?: number;
  now?: () => number;
}

function fixedChild(root: string, ...segments: string[]): string {
  const resolvedRoot = resolve(root);
  const candidate = resolve(resolvedRoot, ...segments);
  if (candidate !== resolvedRoot && !candidate.startsWith(`${resolvedRoot}${sep}`)) {
    throw new LiquidationDataUnavailableError("resolved path escaped the liquidation data root");
  }
  return candidate;
}

async function regularFile(path: string): Promise<boolean> {
  try {
    const entry = await lstat(path);
    return entry.isFile() && !entry.isSymbolicLink();
  } catch {
    return false;
  }
}

async function regularDirectory(path: string): Promise<boolean> {
  try {
    const entry = await lstat(path);
    return entry.isDirectory() && !entry.isSymbolicLink();
  } catch {
    return false;
  }
}

function record(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function integer(value: unknown, field: string): number {
  if (!Number.isSafeInteger(value) || Number(value) < 0) {
    throw new LiquidationDataUnavailableError(`${field} is invalid`);
  }
  return Number(value);
}

function integerOrNull(value: unknown, field: string): number | null {
  return value === null ? null : integer(value, field);
}

function boundedError(value: unknown): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value !== "string") {
    throw new LiquidationDataUnavailableError("latest_error is invalid");
  }
  return value
    .replace(/(api[_-]?key|secret|token|password)=([^\s&]+)/gi, "$1=[redacted]")
    .replace(/([?&](signature|token|key|secret)=)[^&\s]+/gi, "$1[redacted]")
    .slice(0, 500);
}

function parseSource(value: unknown, source: LiquidationHealthSource): LiveSourceState {
  const payload = record(value);
  if (
    !payload ||
    typeof payload.configured !== "boolean" ||
    typeof payload.connected !== "boolean"
  ) {
    throw new LiquidationDataUnavailableError(`live source state is invalid for ${source}`);
  }
  return {
    configured: payload.configured,
    connected: payload.connected,
    last_event_at_ms: integerOrNull(payload.last_event_at_ms, `${source}.last_event_at_ms`),
    last_event_received_at_ms: integerOrNull(
      payload.last_event_received_at_ms,
      `${source}.last_event_received_at_ms`,
    ),
    last_heartbeat_at_ms: integerOrNull(
      payload.last_heartbeat_at_ms,
      `${source}.last_heartbeat_at_ms`,
    ),
    ingest_lag_ms: integerOrNull(payload.ingest_lag_ms, `${source}.ingest_lag_ms`),
    reconnect_count: integer(payload.reconnect_count, `${source}.reconnect_count`),
    observed_symbol_count: integer(
      payload.observed_symbol_count,
      `${source}.observed_symbol_count`,
    ),
    subscription_symbol_count: integer(
      payload.subscription_symbol_count,
      `${source}.subscription_symbol_count`,
    ),
    events_written: integer(payload.events_written, `${source}.events_written`),
    error_count: integer(payload.error_count, `${source}.error_count`),
    parse_error_count: integer(payload.parse_error_count, `${source}.parse_error_count`),
    latest_error: boundedError(payload.latest_error),
  };
}

function validateThreshold(name: string, value: number): number {
  if (!Number.isSafeInteger(value) || value < 1) {
    throw new LiquidationDataUnavailableError(`${name} must be a positive safe integer`);
  }
  return value;
}

export class LiquidationLiveReadModel {
  private readonly dataRoot: string;
  private readonly liveRoot: string;
  private readonly historical: LiquidationReadModel;
  private readonly live: LiquidationReadModel;
  private readonly now: () => number;
  private readonly collectorStaleAfterMs: number;
  private readonly collectorOfflineAfterMs: number;
  private readonly eventStaleAfterMs: number;
  private readonly sourceStaleAfterMs: number;

  constructor(options: LiquidationLiveReadModelOptions) {
    this.dataRoot = resolve(options.dataRoot);
    this.liveRoot = fixedChild(this.dataRoot, "live");
    this.now = options.now ?? Date.now;
    this.collectorStaleAfterMs = validateThreshold(
      "collectorStaleAfterMs",
      options.collectorStaleAfterMs ?? 30_000,
    );
    this.collectorOfflineAfterMs = validateThreshold(
      "collectorOfflineAfterMs",
      options.collectorOfflineAfterMs ?? 120_000,
    );
    this.eventStaleAfterMs = validateThreshold(
      "eventStaleAfterMs",
      options.eventStaleAfterMs ?? 5 * 60_000,
    );
    this.sourceStaleAfterMs = validateThreshold(
      "sourceStaleAfterMs",
      options.sourceStaleAfterMs ?? 45_000,
    );
    if (this.collectorOfflineAfterMs <= this.collectorStaleAfterMs) {
      throw new LiquidationDataUnavailableError(
        "collectorOfflineAfterMs must be greater than collectorStaleAfterMs",
      );
    }
    this.historical = new LiquidationReadModel({
      dataRoot: this.dataRoot,
      maxEvents: options.maxEvents,
      now: this.now,
    });
    this.live = new LiquidationReadModel({
      dataRoot: this.liveRoot,
      maxEvents: options.maxEvents,
      staleAfterMs: this.collectorStaleAfterMs,
      now: this.now,
    });
  }

  async list(query: LiquidationQuery = {}): Promise<LiquidationPage> {
    const state = await this.readLiveState();
    if (!state) {
      return this.historical.list(query);
    }
    const page = await this.live.list(query);
    this.requireSelectedRun(page.run_id, state.run_id);
    return { ...page, mode: this.mode(state) };
  }

  async summary(
    query: Omit<LiquidationQuery, "limit" | "cursor"> = {},
  ): Promise<LiquidationSummary> {
    const state = await this.readLiveState();
    if (!state) {
      return this.historical.summary(query);
    }
    const summary = await this.live.summary(query);
    this.requireSelectedRun(summary.run_id, state.run_id);
    return { ...summary, mode: this.mode(state), anchor_at_ms: this.now() };
  }

  async health(): Promise<LiquidationHealth> {
    const checkedAtMs = this.now();
    const state = await this.readLiveState();
    if (!state) {
      const historical = await this.historical.health();
      return this.historicalHealth(historical, checkedAtMs);
    }

    const live = await this.live.health();
    let historical: LiquidationHealth | null = null;
    try {
      historical = await this.historical.health();
    } catch (error) {
      if (!(error instanceof LiquidationDataUnavailableError)) {
        throw error;
      }
    }
    this.requireSelectedRun(live.run_id, state.run_id);
    const mode = this.mode(state);
    const sources = this.liveSourceHealth(state, checkedAtMs);
    return {
      schema_version: 1,
      contract: "portal-liquidations-health-v2",
      mode,
      run_state: state.run_state,
      run_id: state.run_id,
      acceptance_status: state.run_state === "active" ? "in-progress" : "missing",
      failed_gates: [],
      latest_completed_acceptance: historical?.latest_completed_acceptance ?? null,
      active_sources: LIQUIDATION_HEALTH_SOURCES.filter(
        (source) => state.sources[source].configured,
      ),
      observed_symbol_count: Math.max(
        live.observed_symbol_count,
        ...LIQUIDATION_HEALTH_SOURCES.map(
          (source) => state.sources[source].observed_symbol_count,
        ),
      ),
      sources,
      collector_started_at_ms: state.collector_started_at_ms,
      collector_heartbeat_at_ms: state.collector_heartbeat_at_ms,
      last_event_at_ms: state.last_event_at_ms,
      last_event_received_at_ms: state.last_event_received_at_ms,
      portal_checked_at_ms: checkedAtMs,
      refreshed_at_ms: checkedAtMs,
      stale: mode === "stale",
      truncated: live.truncated,
      research_preview: true,
      trading_authorized: false,
      source_semantics: SOURCE_SEMANTICS,
    };
  }

  private async readLiveState(): Promise<LiveState | null> {
    const pointerPath = fixedChild(this.liveRoot, LIVE_STATE_FILE);
    if (!(await regularFile(pointerPath))) {
      if (await regularDirectory(this.liveRoot)) {
        const entry = await lstat(pointerPath).catch(() => null);
        if (entry?.isSymbolicLink()) {
          throw new LiquidationDataUnavailableError("live state pointer must not be a symlink");
        }
      }
      return null;
    }
    const metadata = await stat(pointerPath);
    if (metadata.size > MAX_METADATA_BYTES) {
      throw new LiquidationDataUnavailableError("live state exceeded the bounded size limit");
    }
    let parsed: unknown;
    try {
      parsed = JSON.parse(await readFile(pointerPath, "utf8"));
    } catch {
      throw new LiquidationDataUnavailableError("live state is not valid JSON");
    }
    const pointer = record(parsed);
    const state = record(pointer?.state);
    if (
      pointer?.schema_version !== 1 ||
      pointer.contract !== LIVE_CONTRACT ||
      !state ||
      state.schema_version !== 1 ||
      state.contract !== LIVE_CONTRACT
    ) {
      throw new LiquidationDataUnavailableError("live state contract is invalid");
    }
    const runId = state.run_id;
    if (typeof runId !== "string" || !RUN_ID_PATTERN.test(runId)) {
      throw new LiquidationDataUnavailableError("live run_id is invalid");
    }
    if (state.run_state !== "active" && state.run_state !== "completed") {
      throw new LiquidationDataUnavailableError("live run_state is invalid");
    }
    if (
      state.execution_enabled !== false ||
      state.trading_authorized !== false ||
      state.trading_credentials_present !== false ||
      state.orders_submitted !== 0
    ) {
      throw new LiquidationDataUnavailableError("live state crossed the no-trading boundary");
    }
    const sources = record(state.sources);
    if (!sources) {
      throw new LiquidationDataUnavailableError("live source states are missing");
    }
    const result: LiveState = {
      run_id: runId,
      run_state: state.run_state,
      collector_started_at_ms: integer(
        state.collector_started_at_ms,
        "collector_started_at_ms",
      ),
      collector_heartbeat_at_ms: integer(
        state.collector_heartbeat_at_ms,
        "collector_heartbeat_at_ms",
      ),
      last_event_at_ms: integerOrNull(state.last_event_at_ms, "last_event_at_ms"),
      last_event_received_at_ms: integerOrNull(
        state.last_event_received_at_ms,
        "last_event_received_at_ms",
      ),
      sources: {
        "bybit-linear": parseSource(sources["bybit-linear"], "bybit-linear"),
        "binance-usdm": parseSource(sources["binance-usdm"], "binance-usdm"),
        "okx-swap": parseSource(sources["okx-swap"], "okx-swap"),
      },
      execution_enabled: false,
      trading_authorized: false,
      trading_credentials_present: false,
      orders_submitted: 0,
    };
    await this.requireLiveRunIsLatest(runId);
    const activeRunId = pointer.active_run_id;
    if (result.run_state === "active" && activeRunId !== runId) {
      throw new LiquidationDataUnavailableError("active live pointer does not match run state");
    }
    if (result.run_state === "completed" && activeRunId !== null) {
      throw new LiquidationDataUnavailableError(
        "completed live pointer must not name an active run",
      );
    }
    return result;
  }

  private async requireLiveRunIsLatest(runId: string): Promise<void> {
    const runsRoot = fixedChild(this.liveRoot, "runs");
    if (!(await regularDirectory(runsRoot))) {
      throw new LiquidationDataUnavailableError("live runs root is unavailable");
    }
    const runIds = (await readdir(runsRoot, { withFileTypes: true }))
      .filter(
        (entry) =>
          entry.isDirectory() && !entry.isSymbolicLink() && RUN_ID_PATTERN.test(entry.name),
      )
      .map((entry) => entry.name)
      .sort()
      .reverse();
    if (runIds[0] !== runId) {
      throw new LiquidationDataUnavailableError("live pointer does not select the newest live run");
    }
  }

  private requireSelectedRun(selected: string, expected: string): void {
    if (selected !== expected) {
      throw new LiquidationDataUnavailableError("read-model selected a different live run");
    }
  }

  private mode(state: LiveState): LiquidationDataMode {
    if (state.run_state === "completed") {
      return "offline";
    }
    const now = this.now();
    const heartbeatAge = Math.max(0, now - state.collector_heartbeat_at_ms);
    if (heartbeatAge > this.collectorOfflineAfterMs) {
      return "offline";
    }
    if (heartbeatAge > this.collectorStaleAfterMs) {
      return "stale";
    }
    const eventReference = state.last_event_received_at_ms ?? state.collector_started_at_ms;
    if (Math.max(0, now - eventReference) > this.eventStaleAfterMs) {
      return "stale";
    }
    if (LIQUIDATION_HEALTH_SOURCES.some((source) => !state.sources[source].configured)) {
      return "stale";
    }
    if (
      LIQUIDATION_HEALTH_SOURCES.some((source) => {
        const item = state.sources[source];
        const sourceEventReference =
          item.last_event_received_at_ms ?? state.collector_started_at_ms;
        return (
          !item.connected ||
          item.last_heartbeat_at_ms === null ||
          now - item.last_heartbeat_at_ms > this.sourceStaleAfterMs ||
          now - sourceEventReference > this.eventStaleAfterMs
        );
      })
    ) {
      return "stale";
    }
    return "live";
  }

  private liveSourceHealth(
    state: LiveState,
    checkedAtMs: number,
  ): LiquidationHealth["sources"] {
    const result = {} as LiquidationHealth["sources"];
    for (const source of LIQUIDATION_HEALTH_SOURCES) {
      const item = state.sources[source];
      const heartbeatFresh =
        item.last_heartbeat_at_ms !== null &&
        checkedAtMs - item.last_heartbeat_at_ms <= this.sourceStaleAfterMs;
      const eventReference = item.last_event_received_at_ms ?? state.collector_started_at_ms;
      const eventFresh = checkedAtMs - eventReference <= this.eventStaleAfterMs;
      result[source] = {
        configured: item.configured,
        connected: item.configured && item.connected && heartbeatFresh,
        healthy: item.configured && item.connected && heartbeatFresh && eventFresh,
        events: item.events_written,
        observed_symbols: item.observed_symbol_count,
        subscription_symbol_count: item.subscription_symbol_count,
        availability_ratio: null,
        disconnects_per_hour: null,
        last_event_at_ms: item.last_event_at_ms,
        last_event_received_at_ms: item.last_event_received_at_ms,
        last_heartbeat_at_ms: item.last_heartbeat_at_ms,
        ingest_lag_ms: item.ingest_lag_ms,
        reconnect_count: item.reconnect_count,
        error_count: item.error_count,
        parse_error_count: item.parse_error_count,
        latest_error: item.latest_error,
      };
    }
    return result;
  }

  private historicalHealth(
    historical: LiquidationHealth,
    checkedAtMs: number,
  ): LiquidationHealth {
    const enrich = (source: LiquidationSource): LiquidationSourceHealth => ({
      ...historical.sources[source],
      configured: true,
      connected: false,
      healthy: false,
      subscription_symbol_count: 0,
      last_event_received_at_ms: null,
      last_heartbeat_at_ms: null,
      ingest_lag_ms: null,
      reconnect_count: 0,
      error_count: 0,
      parse_error_count: 0,
      latest_error: null,
    });
    return {
      ...historical,
      schema_version: 1,
      contract: "portal-liquidations-health-v2",
      mode: "historical",
      run_state: "completed",
      active_sources: [...historical.active_sources],
      sources: {
        "bybit-linear": enrich("bybit-linear"),
        "binance-usdm": enrich("binance-usdm"),
        "okx-swap": {
          ...historical.sources["okx-swap"],
          configured: false,
          connected: false,
          healthy: false,
          events: historical.sources["okx-swap"].events,
          observed_symbols: historical.sources["okx-swap"].observed_symbols,
          subscription_symbol_count: 0,
          availability_ratio: historical.sources["okx-swap"].availability_ratio,
          disconnects_per_hour: historical.sources["okx-swap"].disconnects_per_hour,
          last_event_at_ms: historical.sources["okx-swap"].last_event_at_ms,
          last_event_received_at_ms: null,
          last_heartbeat_at_ms: null,
          ingest_lag_ms: null,
          reconnect_count: 0,
          error_count: 0,
          parse_error_count: 0,
          latest_error: null,
        },
      },
      collector_started_at_ms: null,
      collector_heartbeat_at_ms: null,
      last_event_received_at_ms: null,
      portal_checked_at_ms: checkedAtMs,
      refreshed_at_ms: checkedAtMs,
      source_semantics: SOURCE_SEMANTICS,
    };
  }
}
