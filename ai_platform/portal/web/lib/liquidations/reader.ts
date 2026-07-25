import { createReadStream } from "node:fs";
import { lstat, readdir, readFile, stat } from "node:fs/promises";
import { resolve, sep } from "node:path";

import {
  LIQUIDATION_SOURCES,
  type LiquidationAcceptanceEvidence,
  type LiquidationDataMode,
  type LiquidationHealth,
  type LiquidationPage,
  type LiquidationQuery,
  type LiquidationSource,
  type LiquidationSourceHealth,
  type LiquidationSummary,
  type LiquidationSymbolRanking,
  type LiquidationWindowSummary,
  type PortalLiquidationEvent,
} from "./contracts";
import { addDecimalStrings, compareDecimalStrings } from "./decimal";
import { parsePortalLiquidationEvent } from "./event";

const RUN_ID_PATTERN = /^liquid20-\d{8}T\d{6}Z-\d+$/;
const SYMBOL_PATTERN = /^[A-Z0-9]{2,24}$/;
const SOURCE_FILE_NAMES: Record<LiquidationSource, string> = {
  "bybit-linear": "bybit-linear.ndjson",
  "binance-usdm": "binance-usdm.ndjson",
};
const SOURCE_SUMMARY_NAMES: Record<LiquidationSource, string> = {
  "bybit-linear": "bybit-linear-summary.json",
  "binance-usdm": "binance-usdm-summary.json",
};
const SOURCE_SEMANTICS: Record<LiquidationSource, string> = {
  "bybit-linear": "All liquidation events published by Bybit linear allLiquidation.",
  "binance-usdm":
    "Latest Binance USD-M forceOrder liquidation event per symbol in each approximately 1000 ms window.",
};
const WINDOW_MS = {
  "5m": 5 * 60 * 1_000,
  "1h": 60 * 60 * 1_000,
  "24h": 24 * 60 * 60 * 1_000,
} as const;
const MAX_QUERY_LIMIT = 200;
const DEFAULT_QUERY_LIMIT = 50;
const MAX_METADATA_BYTES = 2 * 1024 * 1024;
const MAX_LINE_BYTES = 128 * 1024;

interface SourceReadState {
  identity: string | null;
  offset: number;
  partial: string;
}

interface RunState {
  runId: string;
  runRoot: string;
  events: Map<string, PortalLiquidationEvent>;
  sourceStates: Record<LiquidationSource, SourceReadState>;
  rejectedRecords: number;
  truncated: boolean;
  refreshedAtMs: number;
}

interface AcceptanceReport {
  runId: string;
  passed: boolean;
  failedGates: string[];
}

interface CursorPayload {
  occurred_at_ms: number;
  source: LiquidationSource;
  source_event_id: string;
}

export interface LiquidationReadModelOptions {
  dataRoot: string;
  maxEvents?: number;
  staleAfterMs?: number;
  now?: () => number;
}

export class LiquidationDataUnavailableError extends Error {}
export class LiquidationQueryError extends Error {}

function newSourceState(): SourceReadState {
  return { identity: null, offset: 0, partial: "" };
}

function newRunState(runId: string, runRoot: string): RunState {
  return {
    runId,
    runRoot,
    events: new Map(),
    sourceStates: {
      "bybit-linear": newSourceState(),
      "binance-usdm": newSourceState(),
    },
    rejectedRecords: 0,
    truncated: false,
    refreshedAtMs: 0,
  };
}

function fixedChild(root: string, ...segments: string[]): string {
  const resolvedRoot = resolve(root);
  const candidate = resolve(resolvedRoot, ...segments);
  if (candidate !== resolvedRoot && !candidate.startsWith(`${resolvedRoot}${sep}`)) {
    throw new LiquidationDataUnavailableError("resolved path escaped the Liquid20 data root");
  }
  return candidate;
}

async function directoryExists(path: string): Promise<boolean> {
  try {
    const entry = await lstat(path);
    return entry.isDirectory() && !entry.isSymbolicLink();
  } catch {
    return false;
  }
}

async function regularFileExists(path: string): Promise<boolean> {
  try {
    const entry = await lstat(path);
    return entry.isFile() && !entry.isSymbolicLink();
  } catch {
    return false;
  }
}

async function readJsonObject(path: string): Promise<Record<string, unknown> | null> {
  if (!(await regularFileExists(path))) {
    return null;
  }
  const metadata = await stat(path);
  if (metadata.size > MAX_METADATA_BYTES) {
    throw new LiquidationDataUnavailableError("Liquid20 metadata exceeded the bounded size limit");
  }
  const parsed: unknown = JSON.parse(await readFile(path, "utf8"));
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new LiquidationDataUnavailableError("Liquid20 metadata must be a JSON object");
  }
  return parsed as Record<string, unknown>;
}

function numberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function nonNegativeIntegerOrNull(value: unknown): number | null {
  const parsed = numberOrNull(value);
  return parsed !== null && Number.isSafeInteger(parsed) && parsed >= 0 ? parsed : null;
}

function recordOrNull(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

function compareEvents(left: PortalLiquidationEvent, right: PortalLiquidationEvent): number {
  if (left.occurred_at_ms !== right.occurred_at_ms) {
    return right.occurred_at_ms - left.occurred_at_ms;
  }
  const sourceOrder = left.source.localeCompare(right.source);
  return sourceOrder || left.source_event_id.localeCompare(right.source_event_id);
}

function compareEventToCursor(event: PortalLiquidationEvent, cursor: CursorPayload): number {
  if (event.occurred_at_ms !== cursor.occurred_at_ms) {
    return cursor.occurred_at_ms - event.occurred_at_ms;
  }
  const sourceOrder = event.source.localeCompare(cursor.source);
  return sourceOrder || event.source_event_id.localeCompare(cursor.source_event_id);
}

function encodeCursor(event: PortalLiquidationEvent): string {
  const payload: CursorPayload = {
    occurred_at_ms: event.occurred_at_ms,
    source: event.source,
    source_event_id: event.source_event_id,
  };
  return Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
}

function decodeCursor(value: string): CursorPayload {
  try {
    const decoded: unknown = JSON.parse(Buffer.from(value, "base64url").toString("utf8"));
    const record = recordOrNull(decoded);
    if (!record) {
      throw new Error("cursor is not an object");
    }
    const occurredAtMs = nonNegativeIntegerOrNull(record.occurred_at_ms);
    const source = record.source;
    const sourceEventId = record.source_event_id;
    if (
      occurredAtMs === null ||
      !LIQUIDATION_SOURCES.includes(source as LiquidationSource) ||
      typeof sourceEventId !== "string" ||
      !sourceEventId ||
      sourceEventId.length > 256
    ) {
      throw new Error("cursor fields are invalid");
    }
    return {
      occurred_at_ms: occurredAtMs,
      source: source as LiquidationSource,
      source_event_id: sourceEventId,
    };
  } catch (error) {
    void error;
    throw new LiquidationQueryError("cursor is invalid");
  }
}

function validateQuery(query: LiquidationQuery): Required<Pick<LiquidationQuery, "source" | "limit">> &
  Omit<LiquidationQuery, "source" | "limit"> {
  const source = query.source ?? "all";
  if (source !== "all" && !LIQUIDATION_SOURCES.includes(source)) {
    throw new LiquidationQueryError("source is invalid");
  }
  const symbol = query.symbol?.trim().toUpperCase();
  if (symbol && !SYMBOL_PATTERN.test(symbol)) {
    throw new LiquidationQueryError("symbol is invalid");
  }
  if (query.side && query.side !== "long" && query.side !== "short") {
    throw new LiquidationQueryError("side is invalid");
  }
  for (const [name, value] of [
    ["since", query.since],
    ["until", query.until],
  ] as const) {
    if (value !== undefined && (!Number.isSafeInteger(value) || value < 0)) {
      throw new LiquidationQueryError(`${name} must be a non-negative safe integer`);
    }
  }
  if (query.since !== undefined && query.until !== undefined && query.since > query.until) {
    throw new LiquidationQueryError("since must not be after until");
  }
  const limit = query.limit ?? DEFAULT_QUERY_LIMIT;
  if (!Number.isSafeInteger(limit) || limit < 1 || limit > MAX_QUERY_LIMIT) {
    throw new LiquidationQueryError(`limit must be between 1 and ${MAX_QUERY_LIMIT}`);
  }
  if (query.cursor !== undefined) {
    decodeCursor(query.cursor);
  }
  return { ...query, source, symbol, limit };
}

function filterEvents(events: PortalLiquidationEvent[], query: LiquidationQuery): PortalLiquidationEvent[] {
  const validated = validateQuery(query);
  const cursor = validated.cursor ? decodeCursor(validated.cursor) : null;
  return events.filter((event) => {
    if (validated.source !== "all" && event.source !== validated.source) {
      return false;
    }
    if (validated.symbol && event.symbol !== validated.symbol) {
      return false;
    }
    if (validated.side && event.liquidated_position_side !== validated.side) {
      return false;
    }
    if (validated.since !== undefined && event.occurred_at_ms < validated.since) {
      return false;
    }
    if (validated.until !== undefined && event.occurred_at_ms > validated.until) {
      return false;
    }
    return !cursor || compareEventToCursor(event, cursor) > 0;
  });
}

function emptySourceBuckets(): Record<
  LiquidationSource,
  { event_count: number; notional_usd: string }
> {
  return {
    "bybit-linear": { event_count: 0, notional_usd: "0" },
    "binance-usdm": { event_count: 0, notional_usd: "0" },
  };
}

function aggregateWindow(
  events: PortalLiquidationEvent[],
  window: keyof typeof WINDOW_MS,
  anchorAtMs: number,
): LiquidationWindowSummary {
  const sinceMs = Math.max(0, anchorAtMs - WINDOW_MS[window]);
  const included = events.filter(
    (event) => event.occurred_at_ms >= sinceMs && event.occurred_at_ms <= anchorAtMs,
  );
  const bySource = emptySourceBuckets();
  let notional = "0";
  let longCount = 0;
  let longNotional = "0";
  let shortCount = 0;
  let shortNotional = "0";
  for (const event of included) {
    notional = addDecimalStrings(notional, event.notional_usd);
    const sourceBucket = bySource[event.source];
    sourceBucket.event_count += 1;
    sourceBucket.notional_usd = addDecimalStrings(
      sourceBucket.notional_usd,
      event.notional_usd,
    );
    if (event.liquidated_position_side === "long") {
      longCount += 1;
      longNotional = addDecimalStrings(longNotional, event.notional_usd);
    } else {
      shortCount += 1;
      shortNotional = addDecimalStrings(shortNotional, event.notional_usd);
    }
  }
  return {
    window,
    since_ms: sinceMs,
    until_ms: anchorAtMs,
    event_count: included.length,
    notional_usd: notional,
    long: { event_count: longCount, notional_usd: longNotional },
    short: { event_count: shortCount, notional_usd: shortNotional },
    by_source: bySource,
  };
}

function rankSymbols(
  events: PortalLiquidationEvent[],
  anchorAtMs: number,
): LiquidationSymbolRanking[] {
  const sinceMs = Math.max(0, anchorAtMs - WINDOW_MS["24h"]);
  const rankings = new Map<string, LiquidationSymbolRanking>();
  for (const event of events) {
    if (event.occurred_at_ms < sinceMs || event.occurred_at_ms > anchorAtMs) {
      continue;
    }
    let ranking = rankings.get(event.symbol);
    if (!ranking) {
      ranking = {
        symbol: event.symbol,
        event_count: 0,
        notional_usd: "0",
        long_event_count: 0,
        long_notional_usd: "0",
        short_event_count: 0,
        short_notional_usd: "0",
        by_source: emptySourceBuckets(),
      };
      rankings.set(event.symbol, ranking);
    }
    ranking.event_count += 1;
    ranking.notional_usd = addDecimalStrings(ranking.notional_usd, event.notional_usd);
    const sourceBucket = ranking.by_source[event.source];
    sourceBucket.event_count += 1;
    sourceBucket.notional_usd = addDecimalStrings(
      sourceBucket.notional_usd,
      event.notional_usd,
    );
    if (event.liquidated_position_side === "long") {
      ranking.long_event_count += 1;
      ranking.long_notional_usd = addDecimalStrings(
        ranking.long_notional_usd,
        event.notional_usd,
      );
    } else {
      ranking.short_event_count += 1;
      ranking.short_notional_usd = addDecimalStrings(
        ranking.short_notional_usd,
        event.notional_usd,
      );
    }
  }
  return [...rankings.values()].sort((left, right) => {
    const byNotional = compareDecimalStrings(right.notional_usd, left.notional_usd);
    return byNotional || right.event_count - left.event_count || left.symbol.localeCompare(right.symbol);
  });
}

export class LiquidationReadModel {
  private readonly dataRoot: string;
  private readonly maxEvents: number;
  private readonly staleAfterMs: number;
  private readonly now: () => number;
  private state: RunState | null = null;

  constructor(options: LiquidationReadModelOptions) {
    this.dataRoot = resolve(options.dataRoot);
    this.maxEvents = options.maxEvents ?? 250_000;
    this.staleAfterMs = options.staleAfterMs ?? 5 * 60 * 1_000;
    this.now = options.now ?? Date.now;
    if (!this.dataRoot) {
      throw new LiquidationDataUnavailableError("Liquid20 data root is required");
    }
    if (!Number.isSafeInteger(this.maxEvents) || this.maxEvents < 1) {
      throw new LiquidationDataUnavailableError("maxEvents must be a positive safe integer");
    }
    if (!Number.isSafeInteger(this.staleAfterMs) || this.staleAfterMs < 1) {
      throw new LiquidationDataUnavailableError("staleAfterMs must be a positive safe integer");
    }
  }

  async list(query: LiquidationQuery = {}): Promise<LiquidationPage> {
    const snapshot = await this.refresh();
    const validated = validateQuery(query);
    const filtered = filterEvents(snapshot.events, validated);
    const pageEvents = filtered.slice(0, validated.limit);
    return {
      schema_version: 1,
      run_id: snapshot.runId,
      mode: snapshot.mode,
      events: pageEvents,
      next_cursor:
        filtered.length > validated.limit && pageEvents.length > 0
          ? encodeCursor(pageEvents[pageEvents.length - 1])
          : null,
      truncated: snapshot.truncated,
      rejected_records: snapshot.rejectedRecords,
    };
  }

  async summary(query: Omit<LiquidationQuery, "limit" | "cursor"> = {}): Promise<LiquidationSummary> {
    const snapshot = await this.refresh();
    const filtered = filterEvents(snapshot.events, { ...query, limit: MAX_QUERY_LIMIT });
    const latestEventAt = snapshot.events[0]?.occurred_at_ms ?? snapshot.activityAtMs;
    const anchorAtMs = snapshot.mode === "historical" ? latestEventAt : this.now();
    return {
      schema_version: 1,
      run_id: snapshot.runId,
      mode: snapshot.mode,
      anchor_at_ms: anchorAtMs,
      windows: (["5m", "1h", "24h"] as const).map((window) =>
        aggregateWindow(filtered, window, anchorAtMs),
      ),
      ranking_24h: rankSymbols(filtered, anchorAtMs),
      truncated: snapshot.truncated,
    };
  }

  async health(): Promise<LiquidationHealth> {
    const snapshot = await this.refresh();
    const acceptance = await this.readAcceptance(snapshot.runRoot);
    const latestCompletedAcceptance = await this.latestCompletedAcceptance(snapshot.runsRoot);
    const sourceHealth = await this.sourceHealth(snapshot.runRoot, snapshot.events);
    const activeSources = LIQUIDATION_SOURCES.filter(
      (source) => sourceHealth[source].events > 0 || snapshot.availableSources.has(source),
    );
    const observedSymbols = new Set(snapshot.events.map((event) => event.symbol));
    const lastEventAtMs = snapshot.events[0]?.occurred_at_ms ?? null;
    return {
      schema_version: 1,
      mode: snapshot.mode,
      run_id: snapshot.runId,
      acceptance_status: acceptance?.passed
        ? "accepted"
        : acceptance
          ? "failed"
          : snapshot.mode === "live" || snapshot.mode === "stale"
            ? "in-progress"
            : "missing",
      failed_gates: acceptance?.failedGates ?? [],
      latest_completed_acceptance: latestCompletedAcceptance,
      active_sources: activeSources,
      observed_symbol_count: Math.max(
        observedSymbols.size,
        ...LIQUIDATION_SOURCES.map((source) => sourceHealth[source].observed_symbols),
      ),
      sources: sourceHealth,
      last_event_at_ms: lastEventAtMs,
      stale: snapshot.mode === "stale",
      refreshed_at_ms: snapshot.refreshedAtMs,
      truncated: snapshot.truncated,
      research_preview: true,
      trading_authorized: false,
      source_semantics: SOURCE_SEMANTICS,
    };
  }

  private async refresh(): Promise<{
    runId: string;
    runRoot: string;
    runsRoot: string;
    mode: LiquidationDataMode;
    events: PortalLiquidationEvent[];
    rejectedRecords: number;
    truncated: boolean;
    refreshedAtMs: number;
    activityAtMs: number;
    availableSources: Set<LiquidationSource>;
  }> {
    const { runsRoot, runId, runRoot } = await this.discoverLatestRun();
    if (!this.state || this.state.runId !== runId || this.state.runRoot !== runRoot) {
      this.state = newRunState(runId, runRoot);
    }
    const availableSources = new Set<LiquidationSource>();
    for (const source of LIQUIDATION_SOURCES) {
      if (await this.refreshSource(this.state, source)) {
        availableSources.add(source);
      }
    }
    this.pruneEvents(this.state);
    this.state.refreshedAtMs = this.now();
    const events = [...this.state.events.values()].sort(compareEvents);
    const acceptance = await this.readAcceptance(runRoot);
    const activityAtMs = await this.runActivityAt(runRoot, events);
    const stale = !acceptance && this.now() - activityAtMs > this.staleAfterMs;
    const mode: LiquidationDataMode = acceptance ? "historical" : stale ? "stale" : "live";
    return {
      runId,
      runRoot,
      runsRoot,
      mode,
      events,
      rejectedRecords: this.state.rejectedRecords,
      truncated: this.state.truncated,
      refreshedAtMs: this.state.refreshedAtMs,
      activityAtMs,
      availableSources,
    };
  }

  private async discoverLatestRun(): Promise<{
    runsRoot: string;
    runId: string;
    runRoot: string;
  }> {
    if (!(await directoryExists(this.dataRoot))) {
      throw new LiquidationDataUnavailableError("Liquid20 data root is unavailable");
    }
    const nestedRuns = fixedChild(this.dataRoot, "runs");
    const runsRoot = (await directoryExists(nestedRuns)) ? nestedRuns : this.dataRoot;
    const entries = await readdir(runsRoot, { withFileTypes: true });
    const runIds = entries
      .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink() && RUN_ID_PATTERN.test(entry.name))
      .map((entry) => entry.name)
      .sort()
      .reverse();
    if (runIds.length === 0) {
      throw new LiquidationDataUnavailableError("no valid Liquid20 run directory was found");
    }
    const runId = runIds[0];
    const runRoot = fixedChild(runsRoot, runId);
    if (!(await directoryExists(runRoot))) {
      throw new LiquidationDataUnavailableError("latest Liquid20 run is not a regular directory");
    }
    return { runsRoot, runId, runRoot };
  }

  private async refreshSource(state: RunState, source: LiquidationSource): Promise<boolean> {
    const path = fixedChild(state.runRoot, SOURCE_FILE_NAMES[source]);
    if (!(await regularFileExists(path))) {
      return false;
    }
    const metadata = await stat(path);
    const identity = `${metadata.dev}:${metadata.ino}`;
    const sourceState = state.sourceStates[source];
    if (sourceState.identity !== identity || metadata.size < sourceState.offset) {
      this.removeSourceEvents(state, source);
      state.sourceStates[source] = newSourceState();
      state.sourceStates[source].identity = identity;
    }
    const activeState = state.sourceStates[source];
    if (metadata.size === activeState.offset) {
      return true;
    }
    const decoder = new TextDecoder();
    let buffered = activeState.partial;
    const stream = createReadStream(path, {
      start: activeState.offset,
      end: metadata.size - 1,
    });
    for await (const chunk of stream) {
      buffered += decoder.decode(chunk as Buffer, { stream: true });
      let newline = buffered.indexOf("\n");
      while (newline >= 0) {
        const line = buffered.slice(0, newline).replace(/\r$/, "");
        buffered = buffered.slice(newline + 1);
        this.consumeLine(state, source, line);
        newline = buffered.indexOf("\n");
      }
      if (Buffer.byteLength(buffered, "utf8") > MAX_LINE_BYTES) {
        state.rejectedRecords += 1;
        buffered = "";
      }
    }
    buffered += decoder.decode();
    activeState.partial = buffered;
    activeState.offset = metadata.size;
    return true;
  }

  private consumeLine(state: RunState, source: LiquidationSource, line: string): void {
    if (!line.trim()) {
      return;
    }
    if (Buffer.byteLength(line, "utf8") > MAX_LINE_BYTES) {
      state.rejectedRecords += 1;
      return;
    }
    try {
      const event = parsePortalLiquidationEvent(JSON.parse(line), source);
      const key = `${event.source}:${event.source_event_id}`;
      const existing = state.events.get(key);
      if (existing && JSON.stringify(existing) !== JSON.stringify(event)) {
        state.rejectedRecords += 1;
        return;
      }
      state.events.set(key, event);
      if (state.events.size > this.maxEvents * 2) {
        this.pruneEvents(state);
      }
    } catch {
      state.rejectedRecords += 1;
    }
  }

  private removeSourceEvents(state: RunState, source: LiquidationSource): void {
    for (const [key, event] of state.events) {
      if (event.source === source) {
        state.events.delete(key);
      }
    }
  }

  private pruneEvents(state: RunState): void {
    if (state.events.size <= this.maxEvents) {
      return;
    }
    const retained = [...state.events.values()].sort(compareEvents).slice(0, this.maxEvents);
    state.events = new Map(
      retained.map((event) => [`${event.source}:${event.source_event_id}`, event]),
    );
    state.truncated = true;
  }

  private async readAcceptance(runRoot: string): Promise<AcceptanceReport | null> {
    const payload = await readJsonObject(
      fixedChild(runRoot, "multi-source-acceptance-report.json"),
    );
    if (!payload || typeof payload.passed !== "boolean") {
      return null;
    }
    const runId = typeof payload.run_id === "string" ? payload.run_id : "";
    if (!RUN_ID_PATTERN.test(runId)) {
      throw new LiquidationDataUnavailableError("acceptance report run_id is invalid");
    }
    return {
      runId,
      passed: payload.passed,
      failedGates: stringArray(payload.failed_gates),
    };
  }

  private async latestCompletedAcceptance(
    runsRoot: string,
  ): Promise<LiquidationAcceptanceEvidence | null> {
    const entries = await readdir(runsRoot, { withFileTypes: true });
    const runIds = entries
      .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink() && RUN_ID_PATTERN.test(entry.name))
      .map((entry) => entry.name)
      .sort()
      .reverse()
      .slice(0, 100);
    for (const runId of runIds) {
      const report = await this.readAcceptance(fixedChild(runsRoot, runId));
      if (report) {
        return {
          run_id: report.runId,
          status: report.passed ? "accepted" : "failed",
          failed_gates: report.failedGates,
        };
      }
    }
    return null;
  }

  private async runActivityAt(
    runRoot: string,
    events: PortalLiquidationEvent[],
  ): Promise<number> {
    let activityAtMs = events[0]?.received_at_ms ?? 0;
    for (const source of LIQUIDATION_SOURCES) {
      const path = fixedChild(runRoot, SOURCE_FILE_NAMES[source]);
      if (await regularFileExists(path)) {
        activityAtMs = Math.max(activityAtMs, (await stat(path)).mtimeMs);
      }
    }
    if (activityAtMs === 0) {
      activityAtMs = (await stat(runRoot)).mtimeMs;
    }
    return Math.floor(activityAtMs);
  }

  private async sourceHealth(
    runRoot: string,
    events: PortalLiquidationEvent[],
  ): Promise<Record<LiquidationSource, LiquidationSourceHealth>> {
    const result = {} as Record<LiquidationSource, LiquidationSourceHealth>;
    for (const source of LIQUIDATION_SOURCES) {
      const sourceEvents = events.filter((event) => event.source === source);
      const summary = await readJsonObject(fixedChild(runRoot, SOURCE_SUMMARY_NAMES[source]));
      const stats = recordOrNull(summary?.stats);
      const eventsBySymbol = recordOrNull(stats?.events_by_symbol);
      result[source] = {
        events:
          nonNegativeIntegerOrNull(stats?.events_written) ??
          nonNegativeIntegerOrNull(stats?.events_parsed) ??
          sourceEvents.length,
        observed_symbols: eventsBySymbol
          ? Object.values(eventsBySymbol).filter(
              (count) => nonNegativeIntegerOrNull(count) !== null && Number(count) > 0,
            ).length
          : new Set(sourceEvents.map((event) => event.symbol)).size,
        availability_ratio: numberOrNull(stats?.availability_ratio),
        disconnects_per_hour: numberOrNull(stats?.disconnects_per_hour),
        last_event_at_ms:
          nonNegativeIntegerOrNull(stats?.last_event_at_ms) ??
          sourceEvents[0]?.occurred_at_ms ??
          null,
      };
    }
    return result;
  }
}
