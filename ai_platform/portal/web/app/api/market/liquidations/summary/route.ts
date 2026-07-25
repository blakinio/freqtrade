import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import {
  liquidationQuery,
  liquidationReadModel,
  safeLiquidationError,
} from "../_shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const { source, symbol, side, since, until } = liquidationQuery(
      request.nextUrl.searchParams,
    );
    const result = await liquidationReadModel().summary({
      source,
      symbol,
      side,
      since,
      until,
    });
    return NextResponse.json(result, {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return safeLiquidationError(error);
  }
}
