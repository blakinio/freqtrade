import { NextRequest, NextResponse } from "next/server";

import type { CreateGridBotConfigRequest } from "@/lib/product-contracts";
import { createGridBotConfig, listGridBotConfigs } from "@/lib/product-api";
import { PortalApiConfigurationError, PortalApiResponseError } from "@/lib/portal-api";

function errorResponse(error: unknown) {
  if (error instanceof PortalApiResponseError) {
    return NextResponse.json({ detail: error.message }, { status: error.status });
  }
  if (error instanceof PortalApiConfigurationError) {
    return NextResponse.json({ detail: "Portal API is not configured" }, { status: 503 });
  }
  return NextResponse.json({ detail: "Portal API request failed" }, { status: 502 });
}

function validRequest(value: unknown): value is CreateGridBotConfigRequest {
  if (typeof value !== "object" || value === null) return false;
  const request = value as Partial<CreateGridBotConfigRequest>;
  const lower = Number(request.lower_price);
  const upper = Number(request.upper_price);
  const allocation = Number(request.quote_allocation);
  return (
    typeof request.bot_id === "string" && request.bot_id.trim().length > 0 &&
    typeof request.pair === "string" && request.pair.trim().length > 0 &&
    typeof request.lower_price === "string" && Number.isFinite(lower) && lower > 0 &&
    typeof request.upper_price === "string" && Number.isFinite(upper) && upper > lower &&
    Number.isInteger(request.levels) && Number(request.levels) >= 2 && Number(request.levels) <= 200 &&
    typeof request.quote_allocation === "string" && Number.isFinite(allocation) && allocation > 0
  );
}

export async function GET(request: NextRequest) {
  try {
    return NextResponse.json(await listGridBotConfigs(request.headers.get("cookie")));
  } catch (error) {
    return errorResponse(error);
  }
}

export async function POST(request: NextRequest) {
  try {
    const payload: unknown = await request.json();
    if (!validRequest(payload)) {
      return NextResponse.json({ detail: "Invalid dry-run grid configuration" }, { status: 422 });
    }
    return NextResponse.json(
      await createGridBotConfig(payload, request.headers.get("cookie")),
      { status: 201 },
    );
  } catch (error) {
    return errorResponse(error);
  }
}
