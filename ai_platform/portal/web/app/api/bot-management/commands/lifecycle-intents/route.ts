import { NextRequest, NextResponse } from "next/server";

import type {
  LifecycleAction,
  LifecycleIntentRequest,
  LifecycleIntentResult,
} from "@/lib/bot-command-contracts";
import {
  forwardControlPlaneMutation,
  identityErrorResponse,
  requireBrowserMutation,
} from "@/lib/identity";
import { dataMode } from "@/lib/portal-api";

const actions = new Set<LifecycleAction>([
  "START",
  "PAUSE_NEW_ENTRIES",
  "RESUME",
  "STOP_KEEP_POSITIONS",
  "STOP_AFTER_EXIT",
  "RESTART_RUNTIME",
  "RETIRE",
]);
const allowedKeys = new Set([
  "bot_id",
  "action",
  "expected_config_revision",
  "expected_runtime_generation_id",
  "idempotency_key",
]);

function validRequest(value: unknown): value is LifecycleIntentRequest {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  if (Object.keys(value).some((key) => !allowedKeys.has(key))) return false;
  const request = value as Partial<LifecycleIntentRequest>;
  return (
    typeof request.bot_id === "string" &&
    request.bot_id.trim().length > 0 &&
    typeof request.action === "string" &&
    actions.has(request.action as LifecycleAction) &&
    Number.isInteger(request.expected_config_revision) &&
    Number(request.expected_config_revision) > 0 &&
    typeof request.expected_runtime_generation_id === "string" &&
    request.expected_runtime_generation_id.trim().length > 0 &&
    typeof request.idempotency_key === "string" &&
    request.idempotency_key.trim().length > 0
  );
}

function fixtureResult(request: LifecycleIntentRequest): LifecycleIntentResult {
  return {
    command_id: `fixture-command:${request.idempotency_key}`,
    bot_id: request.bot_id,
    action: request.action,
    status: "ACCEPTED",
    reason_codes: [],
    command_persisted: true,
    execution_submission_performed: false,
  };
}

export async function POST(request: NextRequest) {
  try {
    requireBrowserMutation(request);
    const payload: unknown = await request.json();
    if (!validRequest(payload)) {
      return NextResponse.json(
        { detail: "Invalid lifecycle command intent request" },
        { status: 422, headers: { "cache-control": "no-store" } },
      );
    }

    const result =
      dataMode() === "fixture"
        ? fixtureResult(payload)
        : await forwardControlPlaneMutation<LifecycleIntentResult>(
            request,
            "/v1/bot-management/commands/lifecycle-intents",
            "POST",
            payload,
          );
    return NextResponse.json(result, {
      status: result.status === "ACCEPTED" ? 202 : 200,
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    const identityResponse = identityErrorResponse(error);
    if (identityResponse) return identityResponse;
    return NextResponse.json(
      { detail: "Lifecycle command intent failed closed" },
      { status: 502, headers: { "cache-control": "no-store" } },
    );
  }
}
