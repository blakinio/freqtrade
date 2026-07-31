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

async function forwardPreview(
  request: NextRequest,
  csrfToken: string,
  command: SignalWizardPreviewCommand,
) {
  const cookieHeader = request.headers.get("cookie");
  if (!cookieHeader) {
    return NextResponse.json(
      { detail: "Portal session is missing", code: "SESSION_MISSING" },
      { status: 401, headers: { "cache-control": "no-store" } },
    );
  }
  const response = await fetch(`${controlPlaneUrl()}/v1/signal-wizard/preview`, {
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
    { detail: "Signal Wizard preview failed closed" },
    { status: 502, headers: { "cache-control": "no-store" } },
  );
}

export async function POST(request: NextRequest) {
  try {
    const csrfToken = requireBrowserMutation(request);
    const payload: unknown = await request.json();
    if (!isPreviewCommand(payload)) {
      return NextResponse.json(
        { detail: "Signal Wizard preview command is incomplete or invalid" },
        { status: 422, headers: { "cache-control": "no-store" } },
      );
    }
    if (dataMode() !== "fixture") {
      return forwardPreview(request, csrfToken, payload);
    }
    return NextResponse.json(await previewSignalWizard(request, payload), {
      status: 200,
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return errorResponse(error);
  }
}
