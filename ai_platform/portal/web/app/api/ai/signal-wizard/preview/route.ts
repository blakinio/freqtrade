import { NextRequest, NextResponse } from "next/server";

import {
  identityErrorResponse,
  requireBrowserMutation,
} from "@/lib/identity";
import {
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "@/lib/portal-api";
import { previewSignalWizard } from "@/lib/signal-wizard-api";
import type { SignalWizardPreviewCommand } from "@/lib/signal-wizard-contracts";

function isPreviewCommand(value: unknown): value is SignalWizardPreviewCommand {
  if (typeof value !== "object" || value === null) return false;
  const command = value as Partial<SignalWizardPreviewCommand>;
  return (
    command.contract_version === "v2" &&
    typeof command.idempotency_key === "string" &&
    command.idempotency_key.trim().length > 0 &&
    typeof command.strategy_id === "string" &&
    command.strategy_id.trim().length > 0 &&
    Array.isArray(command.feature_selections) &&
    typeof command.condition_ast === "object" &&
    command.condition_ast !== null &&
    command.capability?.capability === "strategy.research"
  );
}

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
      { detail: "Signal Wizard backend is not configured" },
      { status: 503, headers: { "cache-control": "no-store" } },
    );
  }
  return NextResponse.json(
    { detail: "Signal Wizard preview failed closed" },
    { status: 502, headers: { "cache-control": "no-store" } },
  );
}

export async function POST(request: NextRequest) {
  try {
    requireBrowserMutation(request);
    const payload: unknown = await request.json();
    if (!isPreviewCommand(payload)) {
      return NextResponse.json(
        { detail: "Signal Wizard preview command is incomplete or invalid" },
        { status: 422, headers: { "cache-control": "no-store" } },
      );
    }
    return NextResponse.json(await previewSignalWizard(request, payload), {
      status: 200,
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return errorResponse(error);
  }
}
