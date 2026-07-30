import { NextRequest, NextResponse } from "next/server";

import {
  identityErrorResponse,
  requireBrowserMutation,
} from "@/lib/identity";
import {
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "@/lib/portal-api";
import { submitStrategyRollback } from "@/lib/strategy-catalog-api";
import type { StrategyRollbackRequest } from "@/lib/strategy-catalog-contracts";

function errorResponse(error: unknown) {
  const identityResponse = identityErrorResponse(error);
  if (identityResponse) return identityResponse;
  if (error instanceof PortalApiResponseError) {
    return NextResponse.json(
      { detail: error.message },
      { status: error.status, headers: { "cache-control": "no-store" } },
    );
  }
  if (error instanceof PortalApiConfigurationError) {
    return NextResponse.json(
      { detail: "Strategy Catalog backend is not configured" },
      { status: 503, headers: { "cache-control": "no-store" } },
    );
  }
  return NextResponse.json(
    { detail: "Strategy rollback request failed closed" },
    { status: 502, headers: { "cache-control": "no-store" } },
  );
}

function isRollbackRequest(value: unknown): value is StrategyRollbackRequest {
  if (typeof value !== "object" || value === null) return false;
  const request = value as Partial<StrategyRollbackRequest>;
  return (
    typeof request.to_strategy_version === "string" &&
    request.to_strategy_version.trim().length > 0 &&
    typeof request.reason === "string" &&
    request.reason.trim().length >= 8 &&
    typeof request.idempotency_key === "string" &&
    request.idempotency_key.trim().length > 0
  );
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ strategyVersion: string }> },
) {
  try {
    requireBrowserMutation(request);
    const payload: unknown = await request.json();
    if (!isRollbackRequest(payload)) {
      return NextResponse.json(
        {
          detail:
            "Rollback requires a target version, an evidence reason of at least eight characters and an idempotency key",
        },
        { status: 422, headers: { "cache-control": "no-store" } },
      );
    }
    const { strategyVersion } = await context.params;
    if (strategyVersion === payload.to_strategy_version) {
      return NextResponse.json(
        { detail: "Rollback target must differ from the source strategy version" },
        { status: 422, headers: { "cache-control": "no-store" } },
      );
    }
    const result = await submitStrategyRollback(request, strategyVersion, {
      to_strategy_version: payload.to_strategy_version.trim(),
      reason: payload.reason.trim(),
      idempotency_key: payload.idempotency_key.trim(),
    });
    return NextResponse.json(result, {
      status: result.accepted ? 202 : 409,
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return errorResponse(error);
  }
}
