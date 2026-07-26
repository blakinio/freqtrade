import "server-only";

import { dataMode, PortalApiConfigurationError, PortalApiResponseError } from "./portal-api";

export type ValuationState = "CURRENT" | "STALE" | "SOURCE_UNAVAILABLE" | "UNPRICED";

export interface ValuationSnapshot {
  valuation_id: string;
  tenant_id: string;
  bot_id: string;
  position_id: string;
  source_position_id: string | null;
  source_runtime_id: string;
  pair: string;
  side: "BUY" | "SELL";
  amount: string;
  state: ValuationState;
  valuation_currency: string | null;
  entry_rate: string | null;
  mark_rate: string | null;
  cost_basis: string | null;
  market_value: string | null;
  unrealized_pnl: string | null;
  source_price_id: string | null;
  source_observed_at: string | null;
  observed_at: string;
  method_version: "mark-to-entry-v1";
  reason_code: string | null;
}

function controlPlaneUrl(): string {
  const value = process.env.PORTAL_CONTROL_PLANE_URL;
  if (!value) {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL is required in API mode");
  }
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL must use http or https");
  }
  return url.toString().replace(/\/$/, "");
}

function fixtureValuations(): ValuationSnapshot[] {
  return [
    {
      valuation_id: "valuation:fixture-eth",
      tenant_id: "tenant-demo",
      bot_id: "bot-eth-dryrun-02",
      position_id: "fixture-position-1",
      source_position_id: "fixture-position-1",
      source_runtime_id: "runtime-eth-02",
      pair: "ETH/USDT",
      side: "BUY",
      amount: "0.10",
      state: "CURRENT",
      valuation_currency: "USDT",
      entry_rate: "3000",
      mark_rate: "3100",
      cost_basis: "300",
      market_value: "310",
      unrealized_pnl: "10",
      source_price_id: "fixture:runtime-eth-02:ETH-USDT",
      source_observed_at: "2026-07-24T18:00:00Z",
      observed_at: "2026-07-24T18:00:00Z",
      method_version: "mark-to-entry-v1",
      reason_code: null,
    },
  ];
}

export async function listValuations(cookieHeader?: string | null): Promise<ValuationSnapshot[]> {
  if (dataMode() === "fixture") {
    return fixtureValuations();
  }
  const response = await fetch(`${controlPlaneUrl()}/v1/valuations`, {
    cache: "no-store",
    headers: {
      accept: "application/json",
      ...(cookieHeader ? { cookie: cookieHeader } : {}),
    },
  });
  if (!response.ok) {
    throw new PortalApiResponseError(
      `Portal API request failed with status ${response.status}`,
      response.status,
    );
  }
  return (await response.json()) as ValuationSnapshot[];
}
