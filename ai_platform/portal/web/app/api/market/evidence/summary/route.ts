import { NextResponse } from "next/server";

import { marketEvidenceReadModel, safeMarketEvidenceError } from "../_shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(): Promise<NextResponse> {
  try {
    return NextResponse.json(await marketEvidenceReadModel().summary(), {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return safeMarketEvidenceError(error);
  }
}
