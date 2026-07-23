import { NextRequest, NextResponse } from "next/server";

import type { NotificationPreference } from "@/lib/product-contracts";
import {
  getNotificationPreferences,
  updateNotificationPreferences,
} from "@/lib/product-api";
import { PortalApiConfigurationError, PortalApiResponseError } from "@/lib/portal-api";

function errorResponse(error: unknown) {
  if (error instanceof PortalApiResponseError) {
    return NextResponse.json({ detail: error.message }, { status: error.status });
  }
  if (error instanceof PortalApiConfigurationError) {
    return NextResponse.json({ detail: "Portal API is not configured" }, { status: 503 });
  }
  return NextResponse.json({ detail: "Portal API request failed" }, { status: 502 });
}

type PreferenceUpdate = Omit<NotificationPreference, "tenant_id" | "actor_id" | "updated_at">;

function validRequest(value: unknown): value is PreferenceUpdate {
  if (typeof value !== "object" || value === null) return false;
  const request = value as Partial<PreferenceUpdate>;
  return (
    typeof request.in_app_enabled === "boolean" &&
    typeof request.signal_events === "boolean" &&
    typeof request.risk_events === "boolean" &&
    typeof request.execution_events === "boolean"
  );
}

export async function GET(request: NextRequest) {
  try {
    return NextResponse.json(await getNotificationPreferences(request.headers.get("cookie")));
  } catch (error) {
    return errorResponse(error);
  }
}

export async function PUT(request: NextRequest) {
  try {
    const payload: unknown = await request.json();
    if (!validRequest(payload)) {
      return NextResponse.json({ detail: "Invalid notification preference request" }, { status: 422 });
    }
    return NextResponse.json(
      await updateNotificationPreferences(payload, request.headers.get("cookie")),
    );
  } catch (error) {
    return errorResponse(error);
  }
}
