import { lstat, readdir, readFile, stat } from "node:fs/promises";
import { resolve, sep } from "node:path";

import {
  type MarketEvidenceAuthorityBoundary,
  type MarketEvidenceInstrument,
  type MarketEvidenceInstrumentPage,
  type MarketEvidenceInstrumentQuery,
  type MarketEvidenceQualityStatus,
  type MarketEvidenceRun,
  type MarketEvidenceRunPage,
  type MarketEvidenceSource,
  type MarketEvidenceSourceStatus,
  type MarketEvidenceStatus,
  type MarketEvidenceSummary,
  MARKET_EVIDENCE_SOURCES,
} from "./contracts";
import {
  MarketEvidenceIntegrityError,
  parseVerifiedNdjson,
  type VerifiedMarketEvidencePackage,
  verifyMarketEvidencePackage,
} from "./integrity";

const RUN_ID_PATTERN = /^wickhunter-production-market-evidence-\d{8}-v\d+-r\d+$/;
const SYMBOL_PATTERN = /^[A-Z0-9]{2,24}$/;
const ACTIVE_POINTER_NAME = "active-wickhunter-production-market-evidence-v1.json";
const PACKAGE_DIR_NAME = "immutable-package";
const MAX_METADATA_BYTES = 8 * 1024 * 1024;
const MAX_RUNS = 50;
const MAX_PAGE_SIZE = 100;

const AUTHORITY: MarketEvidenceAuthorityBoundary = {
  execution_enabled: false,
  orders_submitted: 0,
  trading_credentials_present: false,
  model_execution_authorized: false,
  replay_authorized: false,
  performance_research_authorized: false,
  live_capital_authorized: false,
};

interface RunSnapshot {
  run: MarketEvidenceRun;
  updatedAtMs: number;
  manifest: Record<string, unknown> | null;
  state: Record<string, unknown> | null;
  qualityRows: Record<string, unknown>[];
  instrumentRows: Record<string, unknown>[];
  sourceRows: Record<string, unknown>[];
}

export interface MarketEvidenceReadModelOptions {
  dataRoot: string;
  staleAfterMs?: number;
  now?: () => number;
}

export interface LiquidationSourceOverlay {
  source: MarketEvidenceSource;
  connected: boolean;
  lastEventAtMs: number | null;
  reconnectCount: number;
  errors: string[];
  recordsWritten: number;
}

export class MarketEvidenceDataUnavailableError extends Error {}
export class MarketEvidenceQueryError extends Error {}

function recordOrNull(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function stringOrNull(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function numberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function integerOrNull(value: unknown): number | null {
  const parsed = numberOrNull(value);
  return parsed !== null && Number.isSafeInteger(parsed) ? parsed : null;
}

function nonNegativeInteger(value: unknown, fallback = 0): number {
  const parsed = integerOrNull(value);
  return parsed !== null && parsed >= 0 ? parsed : fallback;
}

function booleanOrFalse(value: unknown): boolean {
  return value === true;
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string").slice(0, 50)
    : [];
}

function fixedChild(root: string, ...segments: string[]): string {
  const resolvedRoot = resolve(root);
  const candidate = resolve(resolvedRoot, ...segments);
  if (candidate !== resolvedRoot && !candidate.startsWith(`${resolvedRoot}${sep}`)) {
    throw new MarketEvidenceDataUnavailableError("resolved path escaped the market evidence root");
  }
  return candidate;
}

async function regularDirectory(path: string): Promise<boolean> {
  try {
    const entry = await lstat(path);
    return entry.isDirectory() && !entry.isSymbolicLink();
  } catch {
    return false;
  }
}

async function regularFile(path: string): Promise<boolean> {
  try {
    const entry = await lstat(path);
    return entry.isFile() && !entry.isSymbolicLink();
  } catch {
    return false;
  }
}

async function readJsonObject(path: string, field: string): Promise<Record<string, unknown> | null> {
  if (!(await regularFile(path))) return null;
  const metadata = await stat(path);
  if (metadata.size > MAX_METADATA_BYTES) {
    throw new MarketEvidenceDataUnavailableError(`${field} exceeded the bounded size limit`);
  }
  try {
    const parsed: unknown = JSON.parse(await readFile(path, "utf8"));
    const record = recordOrNull(parsed);
    if (!record) throw new Error("not an object");
    return record;
  } catch (error) {
    void error;
    throw new MarketEvidenceDataUnavailableError(`${field} is invalid JSON`);
  }
}

function sourceDisplayName(source: MarketEvidenceSource): string {
  if (source === "binance-usdm") return "Binance USD-M";
  if (source === "bybit-linear") return "Bybit Linear";
  return "OKX Swap";
}

function validateInstrumentQuery(query: MarketEvidenceInstrumentQuery): Required<
  Pick<MarketEvidenceInstrumentQuery, "source" | "sort" | "direction" | "page" | "page_size">
> &
  Omit<MarketEvidenceInstrumentQuery, "source" | "sort" | "direction" | "page" | "page_size"> {
  const source = query.source ?? "all";
  if (source !== "all" && !MARKET_EVIDENCE_SOURCES.includes(source)) {
    throw new MarketEvidenceQueryError("source is invalid");
  }
  const symbol = query.symbol?.trim().toUpperCase();
  if (symbol && !SYMBOL_PATTERN.test(symbol)) {
    throw new MarketEvidenceQueryError("symbol is invalid");
  }
  const sort = query.sort ?? "symbol";
  if (!["symbol", "source", "spread", "volume", "freshness"].includes(sort)) {
    throw new MarketEvidenceQueryError("sort is invalid");
  }
  const direction = query.direction ?? "asc";
  if (direction !== "asc" && direction !== "desc") {
    throw new MarketEvidenceQueryError("direction is invalid");
  }
  const page = query.page ?? 1;
  const pageSize = query.page_size ?? 25;
  if (!Number.isSafeInteger(page) || page < 1) {
    throw new MarketEvidenceQueryError("page must be a positive integer");
  }
  if (!Number.isSafeInteger(pageSize) || pageSize < 1 || pageSize > MAX_PAGE_SIZE) {
    throw new MarketEvidenceQueryError(`page_size must be between 1 and ${MAX_PAGE_SIZE}`);
  }
  return { ...query, source, symbol, sort, direction, page, page_size: pageSize };
}

function numeric(value: string | null): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : Number.NEGATIVE_INFINITY;
}

function compareNullable(left: number | null, right: number | null): number {
  if (left === null && right === null) return 0;
  if (left === null) return 1;
  if (right === null) return -1;
  return left - right;
}

export class MarketEvidenceReadModel {
  private readonly dataRoot: string;
  private readonly staleAfterMs: number;
  private readonly now: () => number;

  constructor(options: MarketEvidenceReadModelOptions) {
    this.dataRoot = resolve(options.dataRoot);
    this.staleAfterMs = options.staleAfterMs ?? 15 * 60_000;
    this.now = options.now ?? Date.now;
  }

  async summary(): Promise<MarketEvidenceSummary> {
    const snapshots = await this.snapshots();
    const activeRunId = await this.activeRunId();
    const latest = snapshots.find((snapshot) => snapshot.run.state === "completed") ?? null;
    if (!activeRunId && !latest) {
      return {
        schema_version: 1,
        status: "UNAVAILABLE",
        updated_at_ms: this.now(),
        active_run_id: null,
        latest_immutable_run_id: null,
        capture_start_ms: null,
        capture_end_ms: null,
        pre_roll_ms: null,
        completeness: 0,
        instrument_count: 0,
        completed_candle_count: 0,
        market_quality_observation_count: 0,
        gap_count: 0,
        gap_duration_ms: 0,
        wh01: {
          ready: false,
          market_evidence_ready: false,
          blocker_code: "MARKET_EVIDENCE_UNAVAILABLE",
          blocker_detail: "No active or verified immutable market-evidence run is available.",
        },
        identities: {
          request_sha256: null,
          policy_sha256: null,
          code_sha: null,
          manifest_sha256: null,
        },
        authority: AUTHORITY,
      };
    }
    if (!latest) {
      const active = snapshots.find((snapshot) => snapshot.run.run_id === activeRunId) ?? null;
      return {
        schema_version: 1,
        status: active && this.now() - active.updatedAtMs > this.staleAfterMs ? "STALE" : "LIVE",
        updated_at_ms: active?.updatedAtMs ?? this.now(),
        active_run_id: activeRunId,
        latest_immutable_run_id: null,
        capture_start_ms: active?.run.capture_start_ms ?? null,
        capture_end_ms: active?.run.capture_end_ms ?? null,
        pre_roll_ms: active?.run.pre_roll_ms ?? null,
        completeness: active?.run.completeness ?? 0,
        instrument_count: active?.run.instrument_count ?? 0,
        completed_candle_count: 0,
        market_quality_observation_count: active?.run.market_quality_observation_count ?? 0,
        gap_count: active?.run.gap_count ?? 0,
        gap_duration_ms: active?.run.gap_duration_ms ?? 0,
        wh01: {
          ready: false,
          market_evidence_ready: false,
          blocker_code: "IMMUTABLE_PACKAGE_PENDING",
          blocker_detail: "The active capture has not produced a verified immutable package.",
        },
        identities: {
          request_sha256: active?.run.request_sha256 ?? null,
          policy_sha256: active?.run.policy_sha256 ?? null,
          code_sha: active?.run.code_sha ?? null,
          manifest_sha256: null,
        },
        authority: AUTHORITY,
      };
    }
    const wh01 = recordOrNull(latest.manifest?.wh01);
    const marketReady = wh01?.market_evidence_ready === true;
    const ready = wh01?.ready === true;
    const blockerCode = stringOrNull(wh01?.blocker_code);
    const blockerDetail = stringOrNull(wh01?.blocker_detail);
    const stale = this.now() - latest.updatedAtMs > this.staleAfterMs && latest.run.state !== "completed";
    let status: MarketEvidenceStatus = ready ? "LIVE" : "BLOCKED";
    if (stale) status = "STALE";
    else if (latest.run.gap_count > 0 || latest.run.verification_result !== "accepted") {
      status = "DEGRADED";
    }
    return {
      schema_version: 1,
      status,
      updated_at_ms: latest.updatedAtMs,
      active_run_id: activeRunId,
      latest_immutable_run_id: latest.run.run_id,
      capture_start_ms: latest.run.capture_start_ms,
      capture_end_ms: latest.run.capture_end_ms,
      pre_roll_ms: latest.run.pre_roll_ms,
      completeness: latest.run.completeness,
      instrument_count: latest.run.instrument_count,
      completed_candle_count: latest.run.completed_candle_count,
      market_quality_observation_count: latest.run.market_quality_observation_count,
      gap_count: latest.run.gap_count,
      gap_duration_ms: latest.run.gap_duration_ms,
      wh01: {
        ready,
        market_evidence_ready: marketReady,
        blocker_code: ready ? null : blockerCode ?? "WH01_NOT_READY",
        blocker_detail: ready ? null : blockerDetail ?? "WH-01 input requirements are incomplete.",
      },
      identities: {
        request_sha256: latest.run.request_sha256,
        policy_sha256: latest.run.policy_sha256,
        code_sha: latest.run.code_sha,
        manifest_sha256: latest.run.manifest_sha256,
      },
      authority: AUTHORITY,
    };
  }

  async sources(overlays: LiquidationSourceOverlay[] = []): Promise<MarketEvidenceSourceStatus[]> {
    const snapshots = await this.snapshots();
    const latest = snapshots.find((snapshot) => snapshot.run.state === "completed") ?? null;
    const latestRows = new Map<MarketEvidenceSource, Record<string, unknown>>();
    for (const row of latest?.sourceRows ?? []) {
      const source = row.source;
      if (!MARKET_EVIDENCE_SOURCES.includes(source as MarketEvidenceSource)) continue;
      const typed = source as MarketEvidenceSource;
      const previous = latestRows.get(typed);
      if (!previous || nonNegativeInteger(row.available_at_ms) > nonNegativeInteger(previous.available_at_ms)) {
        latestRows.set(typed, row);
      }
    }
    const overlayBySource = new Map(overlays.map((overlay) => [overlay.source, overlay]));
    return MARKET_EVIDENCE_SOURCES.map((source) => {
      const row = latestRows.get(source);
      const overlay = overlayBySource.get(source);
      const evidenceAvailable = source !== "okx-swap" && Boolean(latest && row);
      const connected = overlay?.connected ?? booleanOrFalse(row?.connected);
      const healthy = evidenceAvailable ? booleanOrFalse(row?.healthy) : connected;
      return {
        source,
        display_name: sourceDisplayName(source),
        connected,
        healthy,
        last_event_at_ms: overlay?.lastEventAtMs ?? integerOrNull(row?.last_event_at_ms),
        last_ticker_at_ms: integerOrNull(row?.last_ticker_at_ms),
        last_completed_candle_at_ms: integerOrNull(row?.last_completed_candle_at_ms),
        freshness_ms: integerOrNull(row?.freshness_ms),
        active_symbols: nonNegativeInteger(row?.active_symbols),
        errors: [...(overlay?.errors ?? []), ...stringArray(row?.errors)].slice(0, 20),
        reconnect_count: overlay?.reconnectCount ?? nonNegativeInteger(row?.reconnect_count),
        gaps: nonNegativeInteger(row?.gaps),
        records_written: overlay?.recordsWritten ?? nonNegativeInteger(row?.records_written),
        required_scope:
          source === "okx-swap"
            ? "liquidation feed only; candle, quality and instrument evidence are not configured"
            : stringOrNull(row?.required_scope) ??
              "ticker, spread, rolling quote volume, completed 5m candles and instrument history",
        liquidation_feed: overlay ? (overlay.connected ? "available" : "unavailable") : "unknown",
        candle_evidence: evidenceAvailable ? "available" : "unavailable",
        market_quality_evidence: evidenceAvailable ? "available" : "unavailable",
        instrument_history: evidenceAvailable ? "available" : "unavailable",
        wickhunter_available: evidenceAvailable && booleanOrFalse(row?.wickhunter_available),
        exclusion_reason:
          source === "okx-swap"
            ? "OKX_CANDLE_EVIDENCE_NOT_CONFIGURED"
            : stringOrNull(row?.exclusion_reason),
      };
    });
  }

  async instruments(query: MarketEvidenceInstrumentQuery = {}): Promise<MarketEvidenceInstrumentPage> {
    const validated = validateInstrumentQuery(query);
    const snapshots = await this.snapshots();
    const latest = snapshots.find((snapshot) => snapshot.run.state === "completed") ?? null;
    if (!latest) {
      return { schema_version: 1, items: [], page: validated.page, page_size: validated.page_size, total: 0, total_pages: 0 };
    }
    const qualities = new Map<string, Record<string, unknown>>();
    for (const row of latest.qualityRows) {
      const source = stringOrNull(row.source);
      const symbol = stringOrNull(row.canonical_symbol) ?? stringOrNull(row.symbol);
      if (!source || !symbol) continue;
      const key = `${source}:${symbol}`;
      const previous = qualities.get(key);
      if (!previous || nonNegativeInteger(row.available_at_ms) > nonNegativeInteger(previous.available_at_ms)) {
        qualities.set(key, row);
      }
    }
    const instruments = new Map<string, Record<string, unknown>>();
    for (const row of latest.instrumentRows) {
      const source = stringOrNull(row.source);
      const symbol = stringOrNull(row.canonical_symbol);
      if (!source || !symbol) continue;
      const key = `${source}:${symbol}`;
      const previous = instruments.get(key);
      if (!previous || nonNegativeInteger(row.captured_at_ms) > nonNegativeInteger(previous.captured_at_ms)) {
        instruments.set(key, row);
      }
    }
    const captureEnd = latest.run.capture_end_ms ?? latest.updatedAtMs;
    let items: MarketEvidenceInstrument[] = [...instruments.entries()].flatMap(([key, instrument]) => {
      const quality = qualities.get(key);
      const source = stringOrNull(instrument.source);
      const symbol = stringOrNull(instrument.canonical_symbol);
      if ((source !== "binance-usdm" && source !== "bybit-linear") || !symbol) return [];
      const capturedAt = integerOrNull(instrument.captured_at_ms);
      const active = booleanOrFalse(instrument.active);
      const qualityAvailable = Boolean(quality);
      const included = active && qualityAvailable && latest.run.gap_count === 0;
      const freshness = capturedAt === null ? null : Math.max(0, captureEnd - capturedAt);
      const qualityStatus: MarketEvidenceQualityStatus = !qualityAvailable
        ? "unavailable"
        : latest.run.gap_count > 0
          ? "degraded"
          : "healthy";
      return [
        {
          source,
          symbol,
          native_symbol: stringOrNull(instrument.native_symbol) ?? symbol,
          market: stringOrNull(instrument.market) ?? "unknown",
          active,
          included,
          latest_price: stringOrNull(quality?.last_price),
          spread_bps: stringOrNull(quality?.spread_bps),
          quote_volume_24h:
            stringOrNull(quality?.quote_volume_24h) ?? stringOrNull(quality?.quote_volume_24h_usd),
          last_completed_candle_at_ms:
            latest.run.capture_end_ms === null ? null : latest.run.capture_end_ms - 300_000,
          history_depth_rows: 432,
          freshness_ms: freshness,
          reason_codes: included ? ["eligible"] : active ? ["market_quality_unavailable"] : ["instrument_inactive"],
          quality_status: qualityStatus,
        },
      ];
    });
    items = items.filter((item) => {
      if (validated.source !== "all" && item.source !== validated.source) return false;
      if (validated.symbol && !item.symbol.includes(validated.symbol)) return false;
      if (validated.market && item.market !== validated.market) return false;
      if (validated.active !== undefined && item.active !== validated.active) return false;
      if (validated.included !== undefined && item.included !== validated.included) return false;
      if (validated.quality && item.quality_status !== validated.quality) return false;
      return true;
    });
    items.sort((left, right) => {
      let compared = 0;
      if (validated.sort === "source") compared = left.source.localeCompare(right.source);
      else if (validated.sort === "spread") compared = numeric(left.spread_bps) - numeric(right.spread_bps);
      else if (validated.sort === "volume") compared = numeric(left.quote_volume_24h) - numeric(right.quote_volume_24h);
      else if (validated.sort === "freshness") compared = compareNullable(left.freshness_ms, right.freshness_ms);
      else compared = left.symbol.localeCompare(right.symbol) || left.source.localeCompare(right.source);
      return validated.direction === "desc" ? -compared : compared;
    });
    const total = items.length;
    const totalPages = total === 0 ? 0 : Math.ceil(total / validated.page_size);
    const offset = (validated.page - 1) * validated.page_size;
    return {
      schema_version: 1,
      items: items.slice(offset, offset + validated.page_size),
      page: validated.page,
      page_size: validated.page_size,
      total,
      total_pages: totalPages,
    };
  }

  async runs(page = 1, pageSize = 20): Promise<MarketEvidenceRunPage> {
    if (!Number.isSafeInteger(page) || page < 1) {
      throw new MarketEvidenceQueryError("page must be a positive integer");
    }
    if (!Number.isSafeInteger(pageSize) || pageSize < 1 || pageSize > MAX_PAGE_SIZE) {
      throw new MarketEvidenceQueryError(`page_size must be between 1 and ${MAX_PAGE_SIZE}`);
    }
    const items = (await this.snapshots()).map((snapshot) => snapshot.run);
    const total = items.length;
    const totalPages = total === 0 ? 0 : Math.ceil(total / pageSize);
    const offset = (page - 1) * pageSize;
    return {
      schema_version: 1,
      items: items.slice(offset, offset + pageSize),
      page,
      page_size: pageSize,
      total,
      total_pages: totalPages,
    };
  }

  private async activeRunId(): Promise<string | null> {
    const pointer = await readJsonObject(fixedChild(this.dataRoot, ACTIVE_POINTER_NAME), "active pointer");
    if (!pointer) return null;
    const runId = stringOrNull(pointer.run_id);
    if (!runId || !RUN_ID_PATTERN.test(runId)) {
      throw new MarketEvidenceDataUnavailableError("active run identity is invalid");
    }
    return runId;
  }

  private async snapshots(): Promise<RunSnapshot[]> {
    if (!(await regularDirectory(this.dataRoot))) {
      throw new MarketEvidenceDataUnavailableError("market evidence data root is unavailable");
    }
    const nested = fixedChild(this.dataRoot, "runs");
    const runsRoot = (await regularDirectory(nested)) ? nested : this.dataRoot;
    const entries = await readdir(runsRoot, { withFileTypes: true });
    const runIds = entries
      .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink() && RUN_ID_PATTERN.test(entry.name))
      .map((entry) => entry.name)
      .sort()
      .reverse()
      .slice(0, MAX_RUNS);
    const snapshots: RunSnapshot[] = [];
    for (const runId of runIds) {
      const snapshot = await this.loadRun(runsRoot, runId);
      if (snapshot) snapshots.push(snapshot);
    }
    return snapshots.sort((left, right) => right.updatedAtMs - left.updatedAtMs || right.run.run_id.localeCompare(left.run.run_id));
  }

  private async loadRun(runsRoot: string, runId: string): Promise<RunSnapshot | null> {
    const runRoot = fixedChild(runsRoot, runId);
    if (!(await regularDirectory(runRoot))) {
      throw new MarketEvidenceDataUnavailableError("market evidence run is not a regular directory");
    }
    const packageRoot = fixedChild(runRoot, PACKAGE_DIR_NAME);
    if (await regularDirectory(packageRoot)) {
      try {
        const verified = await verifyMarketEvidencePackage({
          dataRoot: this.dataRoot,
          packageRoot,
          runId,
        });
        if (verified.version !== 1) return null;
        return this.loadCompletedRun(runId, verified);
      } catch (error) {
        if (error instanceof MarketEvidenceIntegrityError) {
          throw new MarketEvidenceDataUnavailableError(
            "immutable market evidence package failed integrity verification",
          );
        }
        throw error;
      }
    }
    return this.loadActiveRun(runId, runRoot);
  }

  private async loadCompletedRun(
    runId: string,
    verified: VerifiedMarketEvidencePackage,
  ): Promise<RunSnapshot> {
    const { manifest, state, verification, packageRoot } = verified;
    const recordCounts = recordOrNull(manifest.record_counts);
    const capture = recordOrNull(manifest.capture);
    const wh01 = recordOrNull(manifest.wh01);
    const sourceCoverage = stringArray(manifest.sources);
    const gaps = Array.isArray(manifest.gaps) ? manifest.gaps : [];
    const updatedAtMs = nonNegativeInteger(capture?.decision_end_ms, Math.floor((await stat(packageRoot)).mtimeMs));
    const reasonCodes = wh01?.ready === true ? ["eligible"] : [stringOrNull(wh01?.blocker_code) ?? "WH01_NOT_READY"];
    const run: MarketEvidenceRun = {
      run_id: runId,
      state: "completed",
      capture_start_ms: integerOrNull(capture?.pre_roll_start_ms),
      capture_end_ms: integerOrNull(capture?.decision_end_ms),
      pre_roll_ms: integerOrNull(capture?.pre_roll_ms),
      completeness: gaps.length === 0 && verification.outcome === "accepted" ? 1 : 0,
      source_coverage: sourceCoverage,
      instrument_count: Array.isArray(manifest.instruments) ? manifest.instruments.length : 0,
      completed_candle_count: nonNegativeInteger(recordCounts?.completed_candles),
      market_quality_observation_count: nonNegativeInteger(recordCounts?.market_quality_observations),
      gap_count: gaps.length,
      gap_duration_ms: gaps.reduce(
        (total, gap) => total + nonNegativeInteger(recordOrNull(gap)?.duration_ms),
        0,
      ),
      verification_result: verification.outcome === "accepted" ? "accepted" : "rejected",
      manifest_sha256: stringOrNull(manifest.manifest_sha256),
      request_sha256: stringOrNull(manifest.request_sha256),
      policy_sha256: stringOrNull(manifest.policy_sha256),
      code_sha: stringOrNull(manifest.collector_commit),
      wh01_eligible: wh01?.ready === true,
      reason_codes: reasonCodes,
    };
    return {
      run,
      updatedAtMs,
      manifest,
      state,
      qualityRows: parseVerifiedNdjson(
        verified,
        "market-quality-observations.ndjson",
        "market quality observations",
      ),
      instrumentRows: parseVerifiedNdjson(
        verified,
        "instrument-snapshots.ndjson",
        "instrument snapshots",
      ),
      sourceRows: parseVerifiedNdjson(
        verified,
        "source-snapshots.ndjson",
        "source snapshots",
      ),
    };
  }

  private async loadActiveRun(runId: string, runRoot: string): Promise<RunSnapshot> {
    const state = await readJsonObject(fixedChild(runRoot, "incremental-state.json"), "incremental state");
    const request = await readJsonObject(fixedChild(runRoot, "run-request.json"), "run request");
    if (!state || !request || state.run_id !== runId || request.run_id !== runId) {
      throw new MarketEvidenceDataUnavailableError("active market evidence metadata is incomplete");
    }
    const nextSample = nonNegativeInteger(state.next_sample_index);
    const expectedSamples = 144;
    const status = stringOrNull(state.status);
    const runState = status === "failed" ? "failed" : "active";
    const updatedAtMs = Math.floor((await stat(runRoot)).mtimeMs);
    const run: MarketEvidenceRun = {
      run_id: runId,
      state: runState,
      capture_start_ms: integerOrNull(request.pre_roll_start_ms),
      capture_end_ms: integerOrNull(request.decision_end_ms),
      pre_roll_ms:
        integerOrNull(request.decision_start_ms) !== null && integerOrNull(request.pre_roll_start_ms) !== null
          ? Number(request.decision_start_ms) - Number(request.pre_roll_start_ms)
          : null,
      completeness: Math.min(1, nextSample / expectedSamples),
      source_coverage: stringArray(request.sources),
      instrument_count: Array.isArray(request.symbols) ? request.symbols.length : 0,
      completed_candle_count: 0,
      market_quality_observation_count: nextSample * 40,
      gap_count: nonNegativeInteger(state.sample_failures),
      gap_duration_ms: nonNegativeInteger(state.sample_failures) * 300_000,
      verification_result: runState === "failed" ? "rejected" : "pending",
      manifest_sha256: stringOrNull(state.manifest_sha256),
      request_sha256: null,
      policy_sha256: null,
      code_sha: stringOrNull(state.collector_commit),
      wh01_eligible: false,
      reason_codes: [runState === "failed" ? "CAPTURE_FAILED" : "IMMUTABLE_PACKAGE_PENDING"],
    };
    return {
      run,
      updatedAtMs,
      manifest: null,
      state,
      qualityRows: [],
      instrumentRows: [],
      sourceRows: [],
    };
  }
}
