import { NextRequest, NextResponse } from "next/server";

import type { BotDesiredState } from "@/lib/contracts";
import { setBotDesiredState } from "@/lib/bot-operations";
import {
  getBot,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "@/lib/portal-api";

type LifecycleState = Exclude<BotDesiredState, "CREATED">;

function errorResponse(error: unknown) {
  if (error instanceof PortalApiResponseError) {
    return NextResponse.json({ detail: error.message }, { status: error.status });
  }
  if (error instanceof PortalApiConfigurationError) {
    return NextResponse.json({ detail: "Portal API is not configured" }, { status: 503 });
  }
  return NextResponse.json({ detail: "Portal API request failed" }, { status: 502 });
}

function isLifecycleState(value: unknown): value is LifecycleState {
  return value === "RUNNING" || value === "PAUSED" || value === "STOPPED";
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ botId: string }> },
) {
  try {
    const { botId } = await context.params;
    const payload: unknown = await request.json();
    const desiredState =
      typeof payload === "object" && payload !== null
        ? (payload as { desired_state?: unknown }).desired_state
        : undefined;
    const expectedCurrentState =
      typeof payload === "object" && payload !== null
        ? (payload as { expected_current_state?: unknown }).expected_current_state
        : undefined;
    if (!isLifecycleState(desiredState) || typeof expectedCurrentState !== "string") {
      return NextResponse.json(
        { detail: "Request requires desired_state and expected_current_state" },
        { status: 422 },
      );
    }

    const cookieHeader = request.headers.get("cookie");
    const current = await getBot(botId, cookieHeader);
    if (!current) {
      return NextResponse.json({ detail: "Bot not found" }, { status: 404 });
    }
    if (current.desired_state === desiredState) {
      return NextResponse.json(current, { headers: { "x-idempotent-replay": "true" } });
    }
    if (current.desired_state !== expectedCurrentState) {
      return NextResponse.json(
        {
          detail: `Bot lifecycle state changed. Current desired state is ${current.desired_state}`,
        },
        { status: 409 },
      );
    }

    const updated = await setBotDesiredState(botId, desiredState, cookieHeader);
    return NextResponse.json(updated, { headers: { "x-idempotent-replay": "false" } });
  } catch (error) {
    return errorResponse(error);
  }
}
