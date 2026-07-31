import { NextRequest, NextResponse } from "next/server";

import {
  identityErrorResponse,
  requireBrowserMutation,
} from "@/lib/identity";
import {
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "@/lib/portal-api";
import { submitSignalWizard } from "@/lib/signal-wizard-api";
import type { SignalWizardSubmitCommand } from "@/lib/signal-wizard-contracts";

function isSubmitCommand(value: unknown): value is SignalWizardSubmitCommand {
  if (typeof value !== "object" || value === null) return false;
  const command = value as Partial<SignalWizardSubmitCommand>;
  return (
    command.contract_version === "v2" &&
    typeof command.idempotency_key === "string" &&
    command.idempotency_key.trim().length > 0 &&
    typeof command.preview_hash === "string" &&
    /^[0-9a-f]{64}$/.test(command.preview_hash) &&
    typeof command.experiment_name === "string" &&
    command.experiment_name.trim().length > 0 &&
    typeof command.expected_strategy_version === "string" &&
    command.expected_strategy_version.trim().length > 0 &&
    command.capability?.capability === "experiment.submit"
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
    { detail: "Signal Wizard submission failed closed" },
    { status: 502, headers: { "cache-control": "no-store" } },
  );
}

export async function POST(request: NextRequest) {
  try {
    requireBrowserMutation(request);
    const payload: unknown = await request.json();
    if (!isSubmitCommand(payload)) {
      return NextResponse.json(
        { detail: "Signal Wizard submit command is incomplete or invalid" },
        { status: 422, headers: { "cache-control": "no-store" } },
      );
    }
    const result = await submitSignalWizard(request, payload);
    return NextResponse.json(result, {
      status: result.accepted ? 201 : 409,
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return errorResponse(error);
  }
}
