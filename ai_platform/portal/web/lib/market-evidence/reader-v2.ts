import { lstat, readdir } from "node:fs/promises";
import { resolve, sep } from "node:path";

import {
  type MarketEvidenceInstrument,
  type MarketEvidenceInstrumentPage,
  type MarketEvidenceInstrumentQuery,
  type MarketEvidenceQualityStatus,
  type MarketEvidenceRunPage,
  type MarketEvidenceSource,
  type MarketEvidenceSourceStatus,
  type MarketEvidenceSummary,
  MARKET_EVIDENCE_SOURCES,
} from "./contracts";
import {
  MarketEvidenceIntegrityError,
  parseVerifiedNdjson,
  type VerifiedMarketEvidencePackage,
  verifyMarketEvidencePackage,
} from "./integrity";
import {
  type LiquidationSourceOverlay,
  MarketEvidenceDataUnavailableError,
  MarketEvidenceQueryError,
  MarketEvidenceReadModel as LegacyMarketEvidenceReadModel,
  type MarketEvidenceReadModelOptions,
} from "./reader";

export {
  type LiquidationSourceOverlay,
  MarketEvidenceDataUnavailableError,
  MarketEvidenceQueryError,
  type MarketEvidenceReadModelOptions,
} from "./reader";

const RUN_ID_PATTERN = /^wickhunter-production-market-evidence-\d{8}-v\d+-r\d+$/;
const MAX_PAGE_SIZE = 100;

interface VerifiedV2Package {
  runId: string;
  packageRoot: string;
  captureEndMs: number;
  gapCount: number;
  manifest: Record<string, unknown>;
  qualityRows: Record<string, unknown>[];
  instrumentRows: Record<string, unknown>[];
  sourceRows: Record<string, unknown>[];
}

function recordOrNull(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function stringOrNull(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function integerOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isSafeInteger(value) ? value : null;
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

function validatedQuery(query: MarketEvidenceInstrumentQuery): Required<
  Pick<MarketEvidenceInstrumentQuery, "source" | "sort" | "direction" | "page" | "page_size">
> &
  Omit<MarketEvidenceInstrumentQuery, "source" | "sort" | "direction" | "page" | "page_size"> {
  const source = query.source ?? "all";
  if (source !== "all" && !MARKET_EVIDENCE_SOURCES.includes(source)) {
    throw new MarketEvidenceQueryError("source is invalid");
  }
  const symbol = query.symbol?.trim().toUpperCase();
  if (symbol && !/^[A-Z0-9]{2,24}$/u.test(symbol)) {
    throw new MarketEvidenceQueryError("symbol is invalid");
  }
  const sort = query.sort ?? "symbol";
  const direction = query.direction ?? "asc";
  const page = query.page ?? 1;
  const pageSize = query.page_size ?? 25;
  if (!["symbol", "source", "spread", "volume", "freshness"].includes(sort)) {
    throw new MarketEvidenceQueryError("sort is invalid");
  }
  if (direction !== "asc" && direction !== "desc") {
    throw new MarketEvidenceQueryError("direction is invalid");
  }
  if (!Number.isSafeInteger(page) || page < 1) {
    throw new MarketEvidenceQueryError("page must be a positive integer");
  }
  if (!Number.isSafeInteger(pageSize) || pageSize < 1 || pageSize > MAX_PAGE_SIZE) {
    throw new MarketEvidenceQueryError(`page_size must be between 1 and ${MAX_PAGE_SIZE}`);
  }
  return { ...query, source, symbol, sort, direction, page, page_size: pageSize };
}

export class MarketEvidenceReadModel {
  private readonly legacy: LegacyMarketEvidenceReadModel;
  private readonly dataRoot: string;

  constructor(options: MarketEvidenceReadModelOptions) {
    this.legacy = new LegacyMarketEvidenceReadModel(options);
    this.dataRoot = resolve(options.dataRoot);
  }

  async summary(): Promise<MarketEvidenceSummary> {
    return this.legacy.summary();
  }

  async runs(page = 1, pageSize = 20): Promise<MarketEvidenceRunPage> {
    return this.legacy.runs(page, pageSize);
  }

  async sources(overlays: LiquidationSourceOverlay[] = []): Promise<MarketEvidenceSourceStatus[]> {
    const legacy = await this.legacy.sources(overlays);
    const latest = await this.latestV2Package();
    if (!latest) return legacy;
    const latestRows = new Map<MarketEvidenceSource, Record<string, unknown>>();
    for (const row of latest.sourceRows) {
      const source = stringOrNull(row.source);
      if (!source || !MARKET_EVIDENCE_SOURCES.includes(source as MarketEvidenceSource)) continue;
      const typed = source as MarketEvidenceSource;
      const previous = latestRows.get(typed);
      if (!previous || nonNegativeInteger(row.available_at_ms) > nonNegativeInteger(previous.available_at_ms)) {
        latestRows.set(typed, row);
      }
    }
    return legacy.map((item) => {
      if (item.source !== "okx-swap") return item;
      const row = latestRows.get("okx-swap");
      if (!row) return item;
      const connected = booleanOrFalse(row.connected) || item.connected;
      const healthy = booleanOrFalse(row.healthy) && latest.gapCount === 0;
      return {
        ...item,
        connected,
        healthy,
        last_ticker_at_ms: integerOrNull(row.last_ticker_at_ms),
        last_completed_candle_at_ms: integerOrNull(row.last_completed_candle_at_ms),
        freshness_ms: integerOrNull(row.freshness_ms),
        active_symbols: nonNegativeInteger(row.active_symbols),
        errors: [...item.errors, ...stringArray(row.errors)].slice(0, 20),
        reconnect_count: Math.max(item.reconnect_count, nonNegativeInteger(row.reconnect_count)),
        gaps: nonNegativeInteger(row.gaps),
        records_written: Math.max(item.records_written, nonNegativeInteger(row.records_written)),
        required_scope:
          stringOrNull(row.required_scope) ??
          "ticker, spread, rolling quote volume, completed 5m candles and instrument history",
        candle_evidence: "available",
        market_quality_evidence: "available",
        instrument_history: "available",
        wickhunter_available: healthy && booleanOrFalse(row.wickhunter_available),
        exclusion_reason: healthy ? null : stringOrNull(row.exclusion_reason) ?? "OKX_EVIDENCE_DEGRADED",
      };
    });
  }

  async instruments(query: MarketEvidenceInstrumentQuery = {}): Promise<MarketEvidenceInstrumentPage> {
    const validated = validatedQuery(query);
    const legacyPage = await this.legacy.instruments({
      source: "all",
      page: 1,
      page_size: 100,
    });
    const latest = await this.latestV2Package();
    let items: MarketEvidenceInstrument[] = [...legacyPage.items];
    if (latest) items.push(...this.okxInstruments(latest));
    const deduplicated = new Map<string, MarketEvidenceInstrument>();
    for (const item of items) deduplicated.set(`${item.source}:${item.symbol}`, item);
    items = [...deduplicated.values()].filter((item) => {
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
      else if (validated.sort === "volume") {
        compared = numeric(left.quote_volume_24h) - numeric(right.quote_volume_24h);
      } else if (validated.sort === "freshness") {
        compared = compareNullable(left.freshness_ms, right.freshness_ms);
      } else {
        compared = left.symbol.localeCompare(right.symbol) || left.source.localeCompare(right.source);
      }
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

  private okxInstruments(latest: VerifiedV2Package): MarketEvidenceInstrument[] {
    const qualityBySymbol = new Map<string, Record<string, unknown>>();
    for (const row of latest.qualityRows) {
      if (row.source !== "okx-swap") continue;
      const symbol = stringOrNull(row.canonical_symbol) ?? stringOrNull(row.symbol);
      if (!symbol) continue;
      const previous = qualityBySymbol.get(symbol);
      if (!previous || nonNegativeInteger(row.available_at_ms) > nonNegativeInteger(previous.available_at_ms)) {
        qualityBySymbol.set(symbol, row);
      }
    }
    const instrumentBySymbol = new Map<string, Record<string, unknown>>();
    for (const row of latest.instrumentRows) {
      if (row.source !== "okx-swap") continue;
      const symbol = stringOrNull(row.canonical_symbol);
      if (!symbol) continue;
      const previous = instrumentBySymbol.get(symbol);
      const available = nonNegativeInteger(row.available_at_ms, nonNegativeInteger(row.captured_at_ms));
      const previousAvailable = previous
        ? nonNegativeInteger(previous.available_at_ms, nonNegativeInteger(previous.captured_at_ms))
        : -1;
      if (!previous || available > previousAvailable) instrumentBySymbol.set(symbol, row);
    }
    return [...instrumentBySymbol.entries()].map(([symbol, instrument]) => {
      const quality = qualityBySymbol.get(symbol);
      const active = booleanOrFalse(instrument.active);
      const qualityAvailable = Boolean(quality);
      const included = active && qualityAvailable && latest.gapCount === 0;
      const capturedAt = integerOrNull(instrument.available_at_ms) ?? integerOrNull(instrument.captured_at_ms);
      const freshness = capturedAt === null ? null : Math.max(0, latest.captureEndMs - capturedAt);
      const qualityStatus: MarketEvidenceQualityStatus = !qualityAvailable
        ? "unavailable"
        : latest.gapCount > 0
          ? "degraded"
          : "healthy";
      return {
        source: "okx-swap",
        symbol,
        native_symbol: stringOrNull(instrument.native_symbol) ?? symbol,
        market: stringOrNull(instrument.market) ?? "USDT-margined perpetual swap",
        active,
        included,
        latest_price: stringOrNull(quality?.last_price),
        spread_bps: stringOrNull(quality?.spread_bps),
        quote_volume_24h:
          stringOrNull(quality?.quote_volume_24h) ?? stringOrNull(quality?.quote_volume_24h_usd),
        last_completed_candle_at_ms: latest.captureEndMs - 300_000,
        history_depth_rows: 432,
        freshness_ms: freshness,
        reason_codes: included
          ? ["eligible"]
          : active
            ? ["market_quality_unavailable"]
            : ["instrument_inactive"],
        quality_status: qualityStatus,
      };
    });
  }

  private async latestV2Package(): Promise<VerifiedV2Package | null> {
    if (!(await regularDirectory(this.dataRoot))) {
      throw new MarketEvidenceDataUnavailableError("market evidence data root is unavailable");
    }
    const nested = fixedChild(this.dataRoot, "runs");
    const runsRoot = (await regularDirectory(nested)) ? nested : this.dataRoot;
    const entries = await readdir(runsRoot, { withFileTypes: true });
    const candidates: VerifiedV2Package[] = [];
    for (const entry of entries) {
      if (!entry.isDirectory() || entry.isSymbolicLink() || !RUN_ID_PATTERN.test(entry.name)) continue;
      const packageRoot = fixedChild(runsRoot, entry.name, "immutable-package");
      if (!(await regularDirectory(packageRoot))) continue;
      let verified: VerifiedMarketEvidencePackage;
      try {
        verified = await verifyMarketEvidencePackage({
          dataRoot: this.dataRoot,
          packageRoot,
          runId: entry.name,
        });
      } catch (error) {
        if (error instanceof MarketEvidenceIntegrityError) {
          throw new MarketEvidenceDataUnavailableError(
            "immutable v2 market evidence package failed integrity verification",
          );
        }
        throw error;
      }
      if (verified.version !== 2) continue;
      const { manifest } = verified;
      const capture = recordOrNull(manifest.capture);
      const recordCounts = recordOrNull(manifest.record_counts);
      const captureEndMs = nonNegativeInteger(capture?.decision_end_ms);
      if (captureEndMs <= 0) continue;
      candidates.push({
        runId: entry.name,
        packageRoot,
        captureEndMs,
        gapCount: Array.isArray(manifest.gaps)
          ? manifest.gaps.length
          : nonNegativeInteger(recordCounts?.gap_count),
        manifest,
        qualityRows: parseVerifiedNdjson(
          verified,
          "market-quality-observations.ndjson",
          "v2 market quality",
        ),
        instrumentRows: parseVerifiedNdjson(
          verified,
          "instrument-snapshots.ndjson",
          "v2 instrument history",
        ),
        sourceRows: parseVerifiedNdjson(
          verified,
          "source-snapshots.ndjson",
          "v2 source snapshots",
        ),
      });
    }
    candidates.sort(
      (left, right) => right.captureEndMs - left.captureEndMs || right.runId.localeCompare(left.runId),
    );
    return candidates[0] ?? null;
  }
}
