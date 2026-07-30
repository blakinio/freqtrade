import { createReadStream } from "node:fs";
import { lstat } from "node:fs/promises";
import { resolve, sep } from "node:path";
import { createInterface } from "node:readline";

import type {
  LiquidatedPositionSide,
  LiquidationHealth,
  LiquidationHealthSource,
} from "./contracts";
import { addDecimalStrings, compareDecimalStrings, normalizeDecimal } from "./decimal";
import { LiquidationLiveReadModel } from "./live-reader";
import { LiquidationDataUnavailableError, LiquidationQueryError } from "./reader";

export const LIQUIDATION_DATA_SOURCES = [
  "bybit-linear",
  "binance-usdm",
  "okx-swap",
] as const;

export type LiquidationDataSource = (typeof LIQUIDATION_DATA_SOURCES)[number];

export interface LiquidationDataEvent {
  schema_version: 1;
  source: LiquidationDataSource;
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

export interface LiquidationDataQuery {
  source?: LiquidationDataSource | "all";
  symbol?: string;
  side?: LiquidatedPositionSide;
  since?: number;
  until?: number;
  limit?: number;
  cursor?: string;
}

export interface LiquidationDataPage {
  schema_version: 1;
  run_id: string;
  mode: LiquidationHealth["mode"];
  events: LiquidationDataEvent[];
  next_cursor: string | null;
  truncated: boolean;
  rejected_records: number;
}

interface SourceBucket {
  event_count: number;
  notional_usd: string;
}

export interface LiquidationDataWindowSummary {
  window: "5m" | "1h" | "24h";
  since_ms: number;
  until_ms: number;
  event_count: number;
  notional_usd: string;
  long: SourceBucket;
  short: SourceBucket;
  by_source: Record<LiquidationDataSource, SourceBucket>;
}

export interface LiquidationDataSymbolRanking {
  symbol: string;
  event_count: number;
  notional_usd: string;
  long_event_count: number;
  long_notional_usd: string;
  short_event_count: number;
  short_notional_usd: string;
  by_source: Record<LiquidationDataSource, SourceBucket>;
}

export interface LiquidationDataSummary {
  schema_version: 1;
  run_id: string;
  mode: LiquidationHealth["mode"];
  anchor_at_ms: number;
  windows: LiquidationDataWindowSummary[];
  ranking_24h: LiquidationDataSymbolRanking[];
  truncated: boolean;
}

const SOURCE_FILE_NAMES: Record<LiquidationDataSource, string> = {
  "bybit-linear": "bybit-linear.ndjson",
  "binance-usdm": "binance-usdm.ndjson",
  "okx-swap": "okx-swap.ndjson",
};
const WINDOW_MS = {
  "5m": 5 * 60_000,
  "1h": 60 * 60_000,
  "24h": 24 * 60 * 60_000,
} as const;
const SYMBOL_PATTERN = /^[A-Z0-9]{2,24}$/;
const RUN_ID_PATTERN = /^liquid20-\d{8}T\d{6}Z-\d+$/;
const MAX_QUERY_LIMIT = 200;
const MAX_IDENTIFIER_LENGTH = 256;
const MAX_LINE_BYTES = 128 * 1024;

interface CursorPayload {
  occurred_at_ms: number;
  source: LiquidationDataSource;
  source_event_id: string;
}

interface EventSnapshot {
  events: LiquidationDataEvent[];
  rejected: number;
  truncated: boolean;
}

export interface LiquidationLiveReadModelV3Options {
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

function integer(value: unknown, field: string): number {
  const parsed = typeof value === "string" && /^\d+$/.test(value) ? Number(value) : value;
  if (typeof parsed !== "number" || !Number.isSafeInteger(parsed) || parsed < 0) {
    throw new Error(`${field} must be a non-negative safe integer`);
  }
  return parsed;
}

function boundedString(value: unknown, field: string): string {
  if (typeof value !== "string") throw new Error(`${field} must be a string`);
  const parsed = value.trim();
  if (!parsed || parsed.length > MAX_IDENTIFIER_LENGTH) {
    throw new Error(`${field} must be non-empty and bounded`);
  }
  return parsed;
}

function positiveDecimal(value: unknown, field: string): string {
  if (typeof value !== "string" && typeof value !== "number") {
    throw new Error(`${field} must be decimal-compatible`);
  }
  const parsed = normalizeDecimal(String(value));
  if (parsed === "0" || parsed.startsWith("-")) {
    throw new Error(`${field} must be greater than zero`);
  }
  return parsed;
}

function parseEvent(value: unknown, expectedSource: LiquidationDataSource): LiquidationDataEvent {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("liquidation event must be an object");
  }
  const payload = value as Record<string, unknown>;
  if (integer(payload.schema_version, "schema_version") !== 1) {
    throw new Error("schema_version must be 1");
  }
  if (boundedString(payload.source, "source") !== expectedSource) {
    throw new Error("source does not match the fixed source file");
  }
  const symbol = boundedString(payload.symbol, "symbol").toUpperCase();
  if (!SYMBOL_PATTERN.test(symbol)) throw new Error("symbol has an invalid format");
  const side = boundedString(
    payload.liquidated_position_side,
    "liquidated_position_side",
  ) as LiquidatedPositionSide;
  if (side !== "long" && side !== "short") {
    throw new Error("liquidated_position_side must be long or short");
  }
  const occurredAtMs = integer(payload.occurred_at_ms, "occurred_at_ms");
  const receivedAtMs = integer(payload.received_at_ms, "received_at_ms");
  if (occurredAtMs < 1 || receivedAtMs < occurredAtMs) {
    throw new Error("event timestamps are invalid");
  }
  return {
    schema_version: 1,
    source: expectedSource,
    source_event_id: boundedString(payload.source_event_id, "source_event_id"),
    symbol,
    liquidated_position_side: side,
    occurred_at_ms: occurredAtMs,
    received_at_ms: receivedAtMs,
    ingest_latency_ms: receivedAtMs - occurredAtMs,
    price: positiveDecimal(payload.price, "price"),
    quantity: positiveDecimal(payload.quantity, "quantity"),
    notional_usd: positiveDecimal(payload.notional_usd, "notional_usd"),
  };
}

function compareEvents(left: LiquidationDataEvent, right: LiquidationDataEvent): number {
  return (
    right.occurred_at_ms - left.occurred_at_ms ||
    left.source.localeCompare(right.source) ||
    left.source_event_id.localeCompare(right.source_event_id)
  );
}

function encodeCursor(event: LiquidationDataEvent): string {
  const payload: CursorPayload = {
    occurred_at_ms: event.occurred_at_ms,
    source: event.source,
    source_event_id: event.source_event_id,
  };
  return Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
}

function decodeCursor(value: string): CursorPayload {
  try {
    const payload = JSON.parse(Buffer.from(value, "base64url").toString("utf8")) as Record<
      string,
      unknown
    >;
    const source = payload.source;
    const sourceEventId = payload.source_event_id;
    const occurredAtMs = integer(payload.occurred_at_ms, "occurred_at_ms");
    if (
      !LIQUIDATION_DATA_SOURCES.includes(source as LiquidationDataSource) ||
      typeof sourceEventId !== "string" ||
      !sourceEventId ||
      sourceEventId.length > MAX_IDENTIFIER_LENGTH
    ) {
      throw new Error("cursor fields are invalid");
    }
    return {
      occurred_at_ms: occurredAtMs,
      source: source as LiquidationDataSource,
      source_event_id: sourceEventId,
    };
  } catch {
    throw new LiquidationQueryError("cursor is invalid");
  }
}

function compareEventToCursor(event: LiquidationDataEvent, cursor: CursorPayload): number {
  return (
    cursor.occurred_at_ms - event.occurred_at_ms ||
    event.source.localeCompare(cursor.source) ||
    event.source_event_id.localeCompare(cursor.source_event_id)
  );
}

function validateQuery(query: LiquidationDataQuery): Required<
  Pick<LiquidationDataQuery, "source" | "limit">
> &
  Omit<LiquidationDataQuery, "source" | "limit"> {
  const source = query.source ?? "all";
  if (source !== "all" && !LIQUIDATION_DATA_SOURCES.includes(source)) {
    throw new LiquidationQueryError("source is invalid");
  }
  const symbol = query.symbol?.trim().toUpperCase();
  if (symbol && !SYMBOL_PATTERN.test(symbol)) throw new LiquidationQueryError("symbol is invalid");
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
  const limit = query.limit ?? 50;
  if (!Number.isSafeInteger(limit) || limit < 1 || limit > MAX_QUERY_LIMIT) {
    throw new LiquidationQueryError(`limit must be between 1 and ${MAX_QUERY_LIMIT}`);
  }
  if (query.cursor !== undefined) decodeCursor(query.cursor);
  return { ...query, source, symbol, limit };
}

function filterEvents(events: LiquidationDataEvent[], query: LiquidationDataQuery) {
  const validated = validateQuery(query);
  const cursor = validated.cursor ? decodeCursor(validated.cursor) : null;
  return {
    validated,
    events: events.filter((event) => {
      if (validated.source !== "all" && event.source !== validated.source) return false;
      if (validated.symbol && event.symbol !== validated.symbol) return false;
      if (validated.side && event.liquidated_position_side !== validated.side) return false;
      if (validated.since !== undefined && event.occurred_at_ms < validated.since) return false;
      if (validated.until !== undefined && event.occurred_at_ms > validated.until) return false;
      return !cursor || compareEventToCursor(event, cursor) > 0;
    }),
  };
}

function emptySourceBuckets(): Record<LiquidationDataSource, SourceBucket> {
  return {
    "bybit-linear": { event_count: 0, notional_usd: "0" },
    "binance-usdm": { event_count: 0, notional_usd: "0" },
    "okx-swap": { event_count: 0, notional_usd: "0" },
  };
}

function aggregateWindow(
  events: LiquidationDataEvent[],
  window: keyof typeof WINDOW_MS,
  anchorAtMs: number,
): LiquidationDataWindowSummary {
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
    const bucket = bySource[event.source];
    bucket.event_count += 1;
    bucket.notional_usd = addDecimalStrings(bucket.notional_usd, event.notional_usd);
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

function rankSymbols(events: LiquidationDataEvent[], anchorAtMs: number) {
  const sinceMs = Math.max(0, anchorAtMs - WINDOW_MS["24h"]);
  const rankings = new Map<string, LiquidationDataSymbolRanking>();
  for (const event of events) {
    if (event.occurred_at_ms < sinceMs || event.occurred_at_ms > anchorAtMs) continue;
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
    const bucket = ranking.by_source[event.source];
    bucket.event_count += 1;
    bucket.notional_usd = addDecimalStrings(bucket.notional_usd, event.notional_usd);
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

export class LiquidationLiveReadModelV3 {
  private readonly dataRoot: string;
  private readonly maxEvents: number;
  private readonly now: () => number;
  private readonly base: LiquidationLiveReadModel;

  constructor(options: LiquidationLiveReadModelV3Options) {
    this.dataRoot = resolve(options.dataRoot);
    this.maxEvents = options.maxEvents ?? 250_000;
    this.now = options.now ?? Date.now;
    if (!Number.isSafeInteger(this.maxEvents) || this.maxEvents < 1) {
      throw new LiquidationDataUnavailableError("maxEvents must be a positive safe integer");
    }
    this.base = new LiquidationLiveReadModel(options);
  }

  async health(): Promise<LiquidationHealth> {
    const health = await this.base.health();
    const sourceSemantics: Record<LiquidationHealthSource, string> = {
      "bybit-linear":
        health.source_semantics["bybit-linear"] ??
        "All liquidation events published by Bybit linear allLiquidation.",
      "binance-usdm":
        health.source_semantics["binance-usdm"] ??
        "Latest Binance USD-M forceOrder event per symbol in each approximately 1000 ms window.",
      "okx-swap":
        "Public OKX SWAP liquidation-orders events normalized with verified public ctVal metadata.",
    };
    return { ...health, source_semantics: sourceSemantics };
  }

  async list(query: LiquidationDataQuery = {}): Promise<LiquidationDataPage> {
    const health = await this.health();
    const snapshot = await this.readEvents(health);
    const { validated, events } = filterEvents(snapshot.events, query);
    const pageEvents = events.slice(0, validated.limit);
    return {
      schema_version: 1,
      run_id: health.run_id,
      mode: health.mode,
      events: pageEvents,
      next_cursor:
        events.length > validated.limit && pageEvents.length > 0
          ? encodeCursor(pageEvents[pageEvents.length - 1])
          : null,
      truncated: snapshot.truncated,
      rejected_records: snapshot.rejected,
    };
  }

  async summary(
    query: Omit<LiquidationDataQuery, "limit" | "cursor"> = {},
  ): Promise<LiquidationDataSummary> {
    const health = await this.health();
    const snapshot = await this.readEvents(health);
    const { events } = filterEvents(snapshot.events, { ...query, limit: MAX_QUERY_LIMIT });
    const anchorAtMs =
      health.mode === "historical"
        ? (snapshot.events[0]?.occurred_at_ms ?? health.last_event_at_ms ?? this.now())
        : this.now();
    return {
      schema_version: 1,
      run_id: health.run_id,
      mode: health.mode,
      anchor_at_ms: anchorAtMs,
      windows: (["5m", "1h", "24h"] as const).map((window) =>
        aggregateWindow(events, window, anchorAtMs),
      ),
      ranking_24h: rankSymbols(events, anchorAtMs),
      truncated: snapshot.truncated,
    };
  }

  private async runRoot(health: LiquidationHealth): Promise<string> {
    if (!RUN_ID_PATTERN.test(health.run_id)) {
      throw new LiquidationDataUnavailableError("Liquid20 run_id is invalid");
    }
    if (health.mode !== "historical") {
      const live = fixedChild(this.dataRoot, "live", "runs", health.run_id);
      if (!(await regularDirectory(live))) {
        throw new LiquidationDataUnavailableError("live Liquid20 run is unavailable");
      }
      return live;
    }
    const nested = fixedChild(this.dataRoot, "runs", health.run_id);
    if (await regularDirectory(nested)) return nested;
    const legacy = fixedChild(this.dataRoot, health.run_id);
    if (await regularDirectory(legacy)) return legacy;
    throw new LiquidationDataUnavailableError("historical Liquid20 run is unavailable");
  }

  private async readEvents(health: LiquidationHealth): Promise<EventSnapshot> {
    const runRoot = await this.runRoot(health);
    const events = new Map<string, LiquidationDataEvent>();
    let rejected = 0;
    for (const source of LIQUIDATION_DATA_SOURCES) {
      const path = fixedChild(runRoot, SOURCE_FILE_NAMES[source]);
      if (!(await regularFile(path))) continue;
      const lines = createInterface({ input: createReadStream(path), crlfDelay: Infinity });
      for await (const line of lines) {
        if (!line.trim()) continue;
        if (Buffer.byteLength(line, "utf8") > MAX_LINE_BYTES) {
          rejected += 1;
          continue;
        }
        try {
          const event = parseEvent(JSON.parse(line), source);
          const key = `${event.source}:${event.source_event_id}`;
          const previous = events.get(key);
          if (previous && JSON.stringify(previous) !== JSON.stringify(event)) {
            rejected += 1;
            continue;
          }
          events.set(key, event);
        } catch {
          rejected += 1;
        }
      }
    }
    const sorted = [...events.values()].sort(compareEvents);
    return {
      events: sorted.slice(0, this.maxEvents),
      rejected,
      truncated: sorted.length > this.maxEvents,
    };
  }
}
