import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import {
  authorizeLiquidationRequest,
  liquidationQuery,
  liquidationReadModel,
  safeLiquidationError,
} from "./_shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    await authorizeLiquidationRequest(request);
    const result = await liquidationReadModel().list(
      liquidationQuery(request.nextUrl.searchParams),
    );
    return NextResponse.json(result, {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return safeLiquidationError(error);
  }
}
