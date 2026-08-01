import { type NextRequest, NextResponse } from "next/server";

import {
  marketEvidenceReadModel,
  requireMarketEvidenceAuthorization,
  safeMarketEvidenceError,
} from "../_shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    await requireMarketEvidenceAuthorization(request);
    return NextResponse.json(await marketEvidenceReadModel().summary(), {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return safeMarketEvidenceError(error);
  }
}
