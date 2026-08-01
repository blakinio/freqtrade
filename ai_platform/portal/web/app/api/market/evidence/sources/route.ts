import { type NextRequest, NextResponse } from "next/server";

import type { LiquidationHealthSource, LiquidationSourceHealth } from "@/lib/liquidations";
import type { LiquidationSourceOverlay, MarketEvidenceSource } from "@/lib/market-evidence";

import { liquidationReadModel } from "../../liquidations/_shared";
import {
  marketEvidenceReadModel,
  requireMarketEvidenceAuthorization,
  safeMarketEvidenceError,
} from "../_shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function overlay(
  source: LiquidationHealthSource,
  health: LiquidationSourceHealth | undefined,
): LiquidationSourceOverlay {
  return {
    source: source as MarketEvidenceSource,
    connected: health?.connected ?? (health?.events ?? 0) > 0,
    lastEventAtMs: health?.last_event_received_at_ms ?? health?.last_event_at_ms ?? null,
    reconnectCount: health?.reconnect_count ?? 0,
    errors: health?.latest_error ? [health.latest_error] : [],
    recordsWritten: health?.events ?? 0,
  };
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    await requireMarketEvidenceAuthorization(request);
    const overlays: LiquidationSourceOverlay[] = [];
    try {
      const health = await liquidationReadModel().health();
      for (const source of ["binance-usdm", "bybit-linear", "okx-swap"] as const) {
        overlays.push(overlay(source, health.sources[source]));
      }
    } catch (error) {
      void error;
    }
    return NextResponse.json(await marketEvidenceReadModel().sources(overlays), {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return safeMarketEvidenceError(error);
  }
}
