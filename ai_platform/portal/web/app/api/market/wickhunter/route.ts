import { type NextRequest, NextResponse } from "next/server";

import {
  WickHunterObservabilityIntegrityError,
  WickHunterObservabilityUnavailableError,
  readWickHunterObservability,
} from "@/lib/wickhunter-observability";

import {
  requireMarketEvidenceAuthorization,
  safeMarketEvidenceError,
} from "../evidence/_shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    await requireMarketEvidenceAuthorization(request);
    return NextResponse.json(await readWickHunterObservability(), {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    if (error instanceof WickHunterObservabilityUnavailableError) {
      return NextResponse.json(
        { code: "WICKHUNTER_OBSERVABILITY_UNAVAILABLE", error: error.message },
        { status: 503, headers: { "cache-control": "no-store" } },
      );
    }
    if (error instanceof WickHunterObservabilityIntegrityError) {
      console.error("Rejected unsafe WickHunter observability snapshot", error);
      return NextResponse.json(
        {
          code: "WICKHUNTER_OBSERVABILITY_INTEGRITY_ERROR",
          error: "WickHunter observability snapshot failed validation",
        },
        { status: 503, headers: { "cache-control": "no-store" } },
      );
    }
    return safeMarketEvidenceError(error);
  }
}
