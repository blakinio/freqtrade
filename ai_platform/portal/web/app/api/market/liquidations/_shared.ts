import { resolve } from "node:path";

import { NextResponse } from "next/server";

import {
  LIQUIDATION_SOURCES,
  LiquidationDataUnavailableError,
  LiquidationQueryError,
  LiquidationReadModel,
  type LiquidatedPositionSide,
  type LiquidationQuery,
  type LiquidationSource,
} from "@/lib/liquidations";

let singleton: LiquidationReadModel | null = null;
let singletonRoot: string | null = null;

function configuredDataRoot(): string {
  const configured = process.env.PORTAL_LIQUIDATIONS_DATA_ROOT?.trim();
  if (configured) {
    return resolve(configured);
  }
  if (process.env.PORTAL_WEB_DATA_MODE === "fixture") {
    return resolve(process.cwd(), "fixtures/liquidations");
  }
  throw new LiquidationDataUnavailableError(
    "PORTAL_LIQUIDATIONS_DATA_ROOT is required outside fixture mode",
  );
}

export function liquidationReadModel(): LiquidationReadModel {
  const dataRoot = configuredDataRoot();
  if (!singleton || singletonRoot !== dataRoot) {
    singleton = new LiquidationReadModel({ dataRoot });
    singletonRoot = dataRoot;
  }
  return singleton;
}

function integerParameter(value: string | null, name: string): number | undefined {
  if (value === null || value === "") {
    return undefined;
  }
  if (!/^\d+$/.test(value)) {
    throw new LiquidationQueryError(`${name} must be a non-negative integer`);
  }
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) {
    throw new LiquidationQueryError(`${name} must be a safe integer`);
  }
  return parsed;
}

export function liquidationQuery(searchParams: URLSearchParams): LiquidationQuery {
  const sourceValue = searchParams.get("source") ?? undefined;
  const source = sourceValue as LiquidationSource | "all" | undefined;
  if (source && source !== "all" && !LIQUIDATION_SOURCES.includes(source)) {
    throw new LiquidationQueryError("source is invalid");
  }
  const sideValue = searchParams.get("side") ?? undefined;
  if (sideValue && sideValue !== "long" && sideValue !== "short") {
    throw new LiquidationQueryError("side is invalid");
  }
  return {
    source,
    symbol: searchParams.get("symbol") ?? undefined,
    side: sideValue as LiquidatedPositionSide | undefined,
    since: integerParameter(searchParams.get("since"), "since"),
    until: integerParameter(searchParams.get("until"), "until"),
    limit: integerParameter(searchParams.get("limit"), "limit"),
    cursor: searchParams.get("cursor") ?? undefined,
  };
}

export function safeLiquidationError(error: unknown): NextResponse {
  if (error instanceof LiquidationQueryError) {
    return NextResponse.json({ detail: error.message }, { status: 422 });
  }
  if (error instanceof LiquidationDataUnavailableError) {
    return NextResponse.json(
      { detail: "Liquid20 data is currently unavailable" },
      { status: 503 },
    );
  }
  console.error("Liquid20 BFF request failed", error);
  return NextResponse.json({ detail: "Liquid20 read-model request failed" }, { status: 500 });
}
