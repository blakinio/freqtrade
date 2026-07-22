import { NextRequest, NextResponse } from "next/server";

import type { CreateBotRequest } from "@/lib/contracts";
import {
  createBot,
  listBots,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "@/lib/portal-api";

function errorResponse(error: unknown) {
  if (error instanceof PortalApiResponseError) {
    return NextResponse.json({ detail: error.message }, { status: error.status });
  }
  if (error instanceof PortalApiConfigurationError) {
    return NextResponse.json({ detail: "Portal API is not configured" }, { status: 503 });
  }
  return NextResponse.json({ detail: "Portal API request failed" }, { status: 502 });
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isCreateBotRequest(value: unknown): value is CreateBotRequest {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const request = value as Partial<CreateBotRequest>;
  const spec = request.spec;
  return (
    isNonEmptyString(request.bot_id) &&
    isNonEmptyString(request.name) &&
    typeof spec === "object" &&
    spec !== null &&
    isNonEmptyString(spec.tenant_id) &&
    isNonEmptyString(spec.strategy_version) &&
    isNonEmptyString(spec.model_version) &&
    isNonEmptyString(spec.risk_policy_version) &&
    isNonEmptyString(spec.exchange_connection_ref) &&
    Array.isArray(spec.pair_universe) &&
    spec.pair_universe.length > 0 &&
    spec.pair_universe.every(isNonEmptyString) &&
    new Set(spec.pair_universe).size === spec.pair_universe.length &&
    isNonEmptyString(spec.timeframe) &&
    isNonEmptyString(spec.capital_allocation) &&
    Number.isFinite(Number(spec.capital_allocation)) &&
    Number(spec.capital_allocation) > 0 &&
    isNonEmptyString(spec.capital_currency) &&
    isNonEmptyString(spec.runtime_version) &&
    Number.isInteger(spec.config_revision) &&
    Number(spec.config_revision) > 0 &&
    (spec.environment === "research" ||
      spec.environment === "test" ||
      spec.environment === "staging" ||
      spec.environment === "production") &&
    spec.execution_mode === "dry_run"
  );
}

export async function GET(request: NextRequest) {
  try {
    return NextResponse.json(await listBots(request.headers.get("cookie")));
  } catch (error) {
    return errorResponse(error);
  }
}

export async function POST(request: NextRequest) {
  try {
    const payload: unknown = await request.json();
    if (!isCreateBotRequest(payload)) {
      return NextResponse.json(
        { detail: "Request must match the canonical P2 dry-run bot contract" },
        { status: 422 },
      );
    }
    const bot = await createBot(payload, request.headers.get("cookie"));
    return NextResponse.json(bot, { status: 201 });
  } catch (error) {
    return errorResponse(error);
  }
}
