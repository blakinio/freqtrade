import { NextRequest, NextResponse } from "next/server";

import { reviseBot, sameBotSpec } from "@/lib/bot-operations";
import type { BotInstance, BotSpec } from "@/lib/contracts";
import {
  forwardControlPlaneMutation,
  identityErrorResponse,
  requireBrowserMutation,
} from "@/lib/identity";
import {
  dataMode,
  getBot,
  PortalApiConfigurationError,
  PortalApiResponseError,
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

function nonEmpty(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isBotSpec(value: unknown): value is BotSpec {
  if (typeof value !== "object" || value === null) return false;
  const spec = value as Partial<BotSpec>;
  return (
    nonEmpty(spec.tenant_id) &&
    nonEmpty(spec.strategy_version) &&
    nonEmpty(spec.model_version) &&
    nonEmpty(spec.risk_policy_version) &&
    nonEmpty(spec.exchange_connection_ref) &&
    Array.isArray(spec.pair_universe) &&
    spec.pair_universe.length > 0 &&
    spec.pair_universe.every(nonEmpty) &&
    new Set(spec.pair_universe).size === spec.pair_universe.length &&
    nonEmpty(spec.timeframe) &&
    nonEmpty(spec.capital_allocation) &&
    Number.isFinite(Number(spec.capital_allocation)) &&
    Number(spec.capital_allocation) > 0 &&
    nonEmpty(spec.capital_currency) &&
    nonEmpty(spec.runtime_version) &&
    Number.isInteger(spec.config_revision) &&
    Number(spec.config_revision) > 0 &&
    (spec.environment === "research" ||
      spec.environment === "test" ||
      spec.environment === "staging" ||
      spec.environment === "production") &&
    (spec.execution_mode === "simulated" || spec.execution_mode === "dry_run")
  );
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ botId: string }> },
) {
  try {
    requireBrowserMutation(request);
    const { botId } = await context.params;
    const payload: unknown = await request.json();
    const spec =
      typeof payload === "object" && payload !== null
        ? (payload as { spec?: unknown }).spec
        : undefined;
    if (!isBotSpec(spec)) {
      return NextResponse.json(
        { detail: "Request must contain a complete canonical immutable bot spec" },
        { status: 422 },
      );
    }

    const cookieHeader = request.headers.get("cookie");
    const current = await getBot(botId, cookieHeader);
    if (!current) {
      return NextResponse.json({ detail: "Bot not found" }, { status: 404 });
    }
    if (spec.tenant_id !== current.tenant_id) {
      return NextResponse.json({ detail: "Tenant scope mismatch" }, { status: 403 });
    }
    if (
      spec.environment !== current.spec.environment ||
      spec.execution_mode !== current.spec.execution_mode
    ) {
      return NextResponse.json(
        { detail: "Revision cannot change the bot environment or execution mode" },
        { status: 422 },
      );
    }
    if (spec.config_revision === current.spec.config_revision && sameBotSpec(spec, current.spec)) {
      return NextResponse.json(current, { headers: { "x-idempotent-replay": "true" } });
    }
    if (spec.config_revision !== current.spec.config_revision + 1) {
      return NextResponse.json(
        {
          detail: `Stale revision. Expected immutable revision ${current.spec.config_revision + 1}`,
        },
        { status: 409 },
      );
    }

    const updated =
      dataMode() === "fixture"
        ? await reviseBot(botId, spec, cookieHeader)
        : await forwardControlPlaneMutation<BotInstance>(
            request,
            `/v1/bots/${encodeURIComponent(botId)}/revisions`,
            "POST",
            { spec },
          );
    return NextResponse.json(updated, { headers: { "x-idempotent-replay": "false" } });
  } catch (error) {
    return errorResponse(error);
  }
}
