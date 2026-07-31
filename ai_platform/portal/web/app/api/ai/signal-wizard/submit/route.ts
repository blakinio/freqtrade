import { NextRequest, NextResponse } from "next/server";

import { identityErrorResponse, requireBrowserMutation } from "@/lib/identity";
import {
  SignalWizardApiError,
  submitSignalWizard,
} from "@/lib/signal-wizard-api";
import {
  isSignalWizardSubmitRequest,
  type SignalWizardFixtureView,
} from "@/lib/signal-wizard-contracts";

const fixtureViews = new Set<SignalWizardFixtureView>([
  "default",
  "empty",
  "stale",
  "failure",
  "leakage",
  "conflict",
]);

export async function POST(request: NextRequest) {
  try {
    requireBrowserMutation(request);
    const payload: unknown = await request.json();
    if (!isSignalWizardSubmitRequest(payload)) {
      return NextResponse.json(
        {
          detail:
            "Submit requires a persisted preview hash, strategy identity, expected strategy version, experiment name and idempotency key",
          reason_code: "SIGNAL_WIZARD_SUBMIT_REQUEST_INVALID",
        },
        { status: 422, headers: noStoreHeaders() },
      );
    }
    const result = await submitSignalWizard(request, payload, fixtureView(request));
    return NextResponse.json(result, {
      status: result.accepted ? 201 : 409,
      headers: noStoreHeaders(),
    });
  } catch (error) {
    return errorResponse(error);
  }
}

function fixtureView(request: NextRequest): SignalWizardFixtureView {
  const value = request.nextUrl.searchParams.get("view") ?? "default";
  return fixtureViews.has(value as SignalWizardFixtureView)
    ? (value as SignalWizardFixtureView)
    : "default";
}

function errorResponse(error: unknown): NextResponse {
  const identityResponse = identityErrorResponse(error);
  if (identityResponse) return identityResponse;
  if (error instanceof SignalWizardApiError) {
    return NextResponse.json(
      {
        detail: error.message,
        ...(error.reasonCode ? { reason_code: error.reasonCode } : {}),
      },
      { status: error.status, headers: noStoreHeaders() },
    );
  }
  return NextResponse.json(
    {
      detail: "Signal Wizard experiment submission failed closed",
      reason_code: "SIGNAL_WIZARD_REQUEST_FAILED",
    },
    { status: 502, headers: noStoreHeaders() },
  );
}

function noStoreHeaders(): HeadersInit {
  return { "cache-control": "no-store" };
}
