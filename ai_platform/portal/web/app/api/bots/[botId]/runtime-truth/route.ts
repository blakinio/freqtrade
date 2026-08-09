import { NextRequest, NextResponse } from "next/server";

import {
  getBotRuntimeTruth,
} from "@/lib/runtime-generation";
import {
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "@/lib/portal-api";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ botId: string }> },
) {
  try {
    const { botId } = await context.params;
    const truth = await getBotRuntimeTruth(botId, request.headers.get("cookie"));
    if (!truth) {
      return NextResponse.json({ detail: "Runtime generation truth is unavailable" }, { status: 404 });
    }
    return NextResponse.json(truth, { headers: { "cache-control": "no-store" } });
  } catch (error) {
    if (error instanceof PortalApiResponseError) {
      return NextResponse.json({ detail: error.message }, { status: error.status });
    }
    if (error instanceof PortalApiConfigurationError) {
      return NextResponse.json({ detail: "Portal API is not configured" }, { status: 503 });
    }
    return NextResponse.json({ detail: "Portal API request failed" }, { status: 502 });
  }
}
