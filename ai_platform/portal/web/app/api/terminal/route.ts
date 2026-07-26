import { NextRequest, NextResponse } from "next/server";

import type { TerminalIntentRequest, TerminalIntentResult } from "@/lib/contracts";
import {
  forwardControlPlaneMutation,
  identityErrorResponse,
  requireBrowserMutation,
} from "@/lib/identity";
import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
  submitTerminalIntent,
} from "@/lib/portal-api";

function errorResponse(error: unknown) {
  const identityResponse = identityErrorResponse(error);
  if (identityResponse) return identityResponse;
  if (error instanceof PortalApiResponseError) {
    return NextResponse.json({ detail: error.message }, { status: error.status });
  }
  if (error instanceof PortalApiConfigurationError) {
    return NextResponse.json({ detail: "Portal API is not configured" }, { status: 503 });
  }
  return NextResponse.json({ detail: "Portal API request failed" }, { status: 502 });
}

function isTerminalIntentRequest(value: unknown): value is TerminalIntentRequest {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const keys = Object.keys(value);
  if (keys.some((key) => !["bot_id", "pair", "side", "amount"].includes(key))) {
    return false;
  }
  const request = value as Partial<TerminalIntentRequest>;
  return (
    typeof request.bot_id === "string" &&
    request.bot_id.trim().length > 0 &&
    typeof request.pair === "string" &&
    request.pair.trim().length > 0 &&
    (request.side === "BUY" || request.side === "SELL") &&
    typeof request.amount === "string" &&
    Number.isFinite(Number(request.amount)) &&
    Number(request.amount) > 0
  );
}

export async function POST(request: NextRequest) {
  try {
    requireBrowserMutation(request);
    const payload: unknown = await request.json();
    if (!isTerminalIntentRequest(payload)) {
      return NextResponse.json(
        { detail: "Request must contain only bot_id, pair, side and positive amount" },
        { status: 422 },
      );
    }
    const result =
      dataMode() === "fixture"
        ? await submitTerminalIntent(payload, request.headers.get("cookie"))
        : await forwardControlPlaneMutation<TerminalIntentResult>(
            request,
            "/v1/terminal/intents",
            "POST",
            payload,
          );
    return NextResponse.json(result);
  } catch (error) {
    return errorResponse(error);
  }
}
