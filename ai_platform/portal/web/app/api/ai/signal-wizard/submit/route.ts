import { NextRequest, NextResponse } from "next/server";

import {
  CSRF_HEADER_NAME,
  identityErrorResponse,
  requireBrowserMutation,
} from "@/lib/identity";
import {
  dataMode,
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

function controlPlaneUrl(): string {
  const value = process.env.PORTAL_CONTROL_PLANE_URL;
  if (!value) throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL is required");
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL must use HTTP or HTTPS");
  }
  return url.toString().replace(/\/$/, "");
}

async function upstreamPayload(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { detail: `Signal Wizard backend returned non-JSON status ${response.status}` };
  }
}

async function forwardSubmit(
  request: NextRequest,
  csrfToken: string,
  command: SignalWizardSubmitCommand,
) {
  const cookieHeader = request.headers.get("cookie");
  if (!cookieHeader) {
    return NextResponse.json(
      { detail: "Portal session is missing", code: "SESSION_MISSING" },
      { status: 401, headers: { "cache-control": "no-store" } },
    );
  }
  const response = await fetch(`${controlPlaneUrl()}/v1/signal-wizard/submit`, {
    method: "POST",
    cache: "no-store",
    redirect: "manual",
    headers: {
      accept: "application/json",
      cookie: cookieHeader,
      [CSRF_HEADER_NAME]: csrfToken,
      "content-type": "application/json",
    },
    body: JSON.stringify(command),
  });
  return NextResponse.json(await upstreamPayload(response), {
    status: response.status,
    headers: { "cache-control": "no-store" },
  });
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
    const csrfToken = requireBrowserMutation(request);
    const payload: unknown = await request.json();
    if (!isSubmitCommand(payload)) {
      return NextResponse.json(
        { detail: "Signal Wizard submit command is incomplete or invalid" },
        { status: 422, headers: { "cache-control": "no-store" } },
      );
    }
    if (dataMode() !== "fixture") {
      return forwardSubmit(request, csrfToken, payload);
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
