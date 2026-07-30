import { type NextRequest, NextResponse } from "next/server";

import {
  marketEvidenceInstrumentQuery,
  marketEvidenceReadModel,
  safeMarketEvidenceError,
} from "../_shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const query = marketEvidenceInstrumentQuery(request.nextUrl.searchParams);
    return NextResponse.json(await marketEvidenceReadModel().instruments(query), {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return safeMarketEvidenceError(error);
  }
}
