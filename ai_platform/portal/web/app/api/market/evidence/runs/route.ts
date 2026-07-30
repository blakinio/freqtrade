import { type NextRequest, NextResponse } from "next/server";

import {
  marketEvidencePagination,
  marketEvidenceReadModel,
  safeMarketEvidenceError,
} from "../_shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const { page, pageSize } = marketEvidencePagination(request.nextUrl.searchParams);
    return NextResponse.json(await marketEvidenceReadModel().runs(page, pageSize), {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return safeMarketEvidenceError(error);
  }
}
