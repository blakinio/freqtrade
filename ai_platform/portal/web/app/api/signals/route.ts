import { NextRequest, NextResponse } from "next/server";

import type { SubmitSignalRequest } from "@/lib/product-contracts";
import { listSignals, submitSignal } from "@/lib/product-api";
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

function validRequest(value: unknown): value is SubmitSignalRequest {
  if (typeof value !== "object" || value === null) return false;
  const request = value as Partial<SubmitSignalRequest>;
  return (
    typeof request.bot_id === "string" && request.bot_id.trim().length > 0 &&
    typeof request.pair === "string" && request.pair.trim().length > 0 &&
    (request.side === "BUY" || request.side === "SELL") &&
    typeof request.timeframe === "string" && request.timeframe.trim().length > 0 &&
    typeof request.confidence === "string" &&
    Number.isFinite(Number(request.confidence)) &&
    Number(request.confidence) >= 0 &&
    Number(request.confidence) <= 1 &&
    typeof request.rationale === "string" && request.rationale.trim().length > 0
  );
}

export async function GET(request: NextRequest) {
  try {
    return NextResponse.json(await listSignals(request.headers.get("cookie")));
  } catch (error) {
    return errorResponse(error);
  }
}

export async function POST(request: NextRequest) {
  try {
    const payload: unknown = await request.json();
    if (!validRequest(payload)) {
      return NextResponse.json({ detail: "Invalid advisory signal request" }, { status: 422 });
    }
    return NextResponse.json(await submitSignal(payload, request.headers.get("cookie")), { status: 201 });
  } catch (error) {
    return errorResponse(error);
  }
}
