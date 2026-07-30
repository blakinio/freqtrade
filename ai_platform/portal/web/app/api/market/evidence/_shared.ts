import { resolve } from "node:path";

import { NextResponse } from "next/server";

import {
  MarketEvidenceDataUnavailableError,
  MarketEvidenceQueryError,
  MarketEvidenceReadModel,
  MARKET_EVIDENCE_SOURCES,
  type MarketEvidenceInstrumentQuery,
  type MarketEvidenceQualityStatus,
  type MarketEvidenceSource,
} from "@/lib/market-evidence";

let singleton: MarketEvidenceReadModel | null = null;
let singletonKey: string | null = null;

function configuredDataRoot(): string {
  const configured = process.env.PORTAL_MARKET_EVIDENCE_DATA_ROOT?.trim();
  if (configured) return resolve(configured);
  if (process.env.PORTAL_WEB_DATA_MODE === "fixture") {
    return resolve(process.cwd(), "fixtures/market-evidence");
  }
  throw new MarketEvidenceDataUnavailableError(
    "PORTAL_MARKET_EVIDENCE_DATA_ROOT is required outside fixture mode",
  );
}

function configuredThreshold(name: string, fallback: number): number {
  const raw = process.env[name]?.trim();
  if (!raw) return fallback;
  if (!/^\d+$/u.test(raw)) {
    throw new MarketEvidenceDataUnavailableError(`${name} must be a positive integer`);
  }
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < 1) {
    throw new MarketEvidenceDataUnavailableError(`${name} must be a positive safe integer`);
  }
  return value;
}

export function marketEvidenceReadModel(): MarketEvidenceReadModel {
  const dataRoot = configuredDataRoot();
  const staleAfterMs = configuredThreshold("PORTAL_MARKET_EVIDENCE_STALE_MS", 15 * 60_000);
  const key = `${dataRoot}:${staleAfterMs}`;
  if (!singleton || singletonKey !== key) {
    singleton = new MarketEvidenceReadModel({ dataRoot, staleAfterMs });
    singletonKey = key;
  }
  return singleton;
}

function integerParameter(value: string | null, name: string): number | undefined {
  if (value === null || value === "") return undefined;
  if (!/^\d+$/u.test(value)) {
    throw new MarketEvidenceQueryError(`${name} must be a non-negative integer`);
  }
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) {
    throw new MarketEvidenceQueryError(`${name} must be a safe integer`);
  }
  return parsed;
}

function booleanParameter(value: string | null, name: string): boolean | undefined {
  if (value === null || value === "") return undefined;
  if (value === "true") return true;
  if (value === "false") return false;
  throw new MarketEvidenceQueryError(`${name} must be true or false`);
}

function sourceParameter(value: string | null): MarketEvidenceSource | "all" | undefined {
  if (value === null || value === "") return undefined;
  if (value === "all" || MARKET_EVIDENCE_SOURCES.includes(value as MarketEvidenceSource)) {
    return value as MarketEvidenceSource | "all";
  }
  throw new MarketEvidenceQueryError("source is invalid");
}

function qualityParameter(value: string | null): MarketEvidenceQualityStatus | undefined {
  if (value === null || value === "") return undefined;
  if (["healthy", "degraded", "stale", "unavailable"].includes(value)) {
    return value as MarketEvidenceQualityStatus;
  }
  throw new MarketEvidenceQueryError("quality is invalid");
}

function sortParameter(value: string | null): MarketEvidenceInstrumentQuery["sort"] {
  if (value === null || value === "") return undefined;
  if (["symbol", "source", "spread", "volume", "freshness"].includes(value)) {
    return value as MarketEvidenceInstrumentQuery["sort"];
  }
  throw new MarketEvidenceQueryError("sort is invalid");
}

function directionParameter(value: string | null): "asc" | "desc" | undefined {
  if (value === null || value === "") return undefined;
  if (value === "asc" || value === "desc") return value;
  throw new MarketEvidenceQueryError("direction is invalid");
}

export function marketEvidenceInstrumentQuery(
  searchParams: URLSearchParams,
): MarketEvidenceInstrumentQuery {
  return {
    source: sourceParameter(searchParams.get("source")),
    symbol: searchParams.get("symbol") ?? undefined,
    market: searchParams.get("market") ?? undefined,
    active: booleanParameter(searchParams.get("active"), "active"),
    included: booleanParameter(searchParams.get("included"), "included"),
    quality: qualityParameter(searchParams.get("quality")),
    sort: sortParameter(searchParams.get("sort")),
    direction: directionParameter(searchParams.get("direction")),
    page: integerParameter(searchParams.get("page"), "page"),
    page_size: integerParameter(searchParams.get("page_size"), "page_size"),
  };
}

export function marketEvidencePagination(searchParams: URLSearchParams): {
  page: number;
  pageSize: number;
} {
  return {
    page: integerParameter(searchParams.get("page"), "page") ?? 1,
    pageSize: integerParameter(searchParams.get("page_size"), "page_size") ?? 20,
  };
}

export function safeMarketEvidenceError(error: unknown): NextResponse {
  if (error instanceof MarketEvidenceQueryError) {
    return NextResponse.json(
      { detail: error.message, code: "MARKET_EVIDENCE_QUERY_INVALID" },
      { status: 422, headers: { "cache-control": "no-store" } },
    );
  }
  if (error instanceof MarketEvidenceDataUnavailableError) {
    return NextResponse.json(
      {
        detail: "WickHunter market evidence is currently unavailable",
        code: "MARKET_EVIDENCE_UNAVAILABLE",
      },
      { status: 503, headers: { "cache-control": "no-store" } },
    );
  }
  console.error("Market evidence BFF request failed", error);
  return NextResponse.json(
    { detail: "Market evidence read-model request failed", code: "MARKET_EVIDENCE_READ_FAILED" },
    { status: 500, headers: { "cache-control": "no-store" } },
  );
}
