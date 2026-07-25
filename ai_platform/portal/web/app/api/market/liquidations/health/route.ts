import { NextResponse } from "next/server";

import { liquidationReadModel, safeLiquidationError } from "../_shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(): Promise<NextResponse> {
  try {
    return NextResponse.json(await liquidationReadModel().health(), {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return safeLiquidationError(error);
  }
}
