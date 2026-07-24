import "server-only";

import type { OrderState, ReconciliationStatus, TradeSide, TradeHistoryEntry } from "./contracts";
import { dataMode, PortalApiConfigurationError, PortalApiResponseError } from "./portal-api";
import { listFixtureOrders, listFixturePositions, listFixtureTrades } from "./fixtures";

export type RuntimeReadFreshness = "CURRENT" | "STALE" | "PARTIAL" | "SOURCE_UNAVAILABLE";
export type RuntimeReadKind = "OPEN_POSITIONS" | "ORDERS" | "TRADES";
export type RuntimeTradeState = "OPEN" | "CLOSED" | "CANCELED";

interface RuntimeEvidenceFields {
  source_runtime_id: string;
  source_updated_at: string | null;
  observed_at: string | null;
  last_reconciled_at: string | null;
  freshness: RuntimeReadFreshness;
  reconciliation_status: ReconciliationStatus;
  reason_code: string | null;
}

export interface RuntimeEvidencePosition extends RuntimeEvidenceFields {
  tenant_id: string;
  bot_id: string;
  position_id: string;
  source_position_id: string | null;
  pair: string;
  side: TradeSide;
  amount: string;
  opened_at: string;
}

export interface RuntimeEvidenceOrder extends RuntimeEvidenceFields {
  tenant_id: string;
  bot_id: string;
  order_id: string;
  source_order_id: string | null;
  source_trade_id: string | null;
  execution_intent_id: string | null;
  pair: string;
  side: TradeSide;
  state: OrderState;
  amount: string;
  created_at: string;
}

export interface RuntimeEvidenceTrade extends RuntimeEvidenceFields {
  tenant_id: string;
  bot_id: string;
  trade_id: string;
  source_trade_id: string;
  pair: string;
  side: TradeSide;
  state: RuntimeTradeState;
  amount: string;
  opened_at: string;
  closed_at: string | null;
  realized_pnl: string | null;
  fees: string | null;
  exit_reason: string | null;
}

export interface RuntimeSourceStatus {
  tenant_id: string;
  bot_id: string;
  source_runtime_id: string;
  kind: RuntimeReadKind;
  source_observed_at: string | null;
  observed_at: string;
  last_reconciled_at: string;
  freshness: RuntimeReadFreshness;
  reconciliation_status: ReconciliationStatus;
  complete: boolean;
  record_count: number;
  reason_code: string | null;
}

export interface RuntimeEvidenceSnapshot {
  positions: RuntimeEvidencePosition[];
  orders: RuntimeEvidenceOrder[];
  trades: RuntimeEvidenceTrade[];
  source_statuses: RuntimeSourceStatus[];
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

function fixtureTrade(trade: TradeHistoryEntry): RuntimeEvidenceTrade {
  return {
    tenant_id: trade.tenant_id,
    bot_id: trade.bot_id,
    source_runtime_id: trade.source_runtime_id,
    trade_id: trade.trade_id,
    source_trade_id: trade.trade_id,
    pair: trade.pair,
    side: trade.side,
    state: "CLOSED",
    amount: trade.amount,
    opened_at: trade.opened_at,
    closed_at: trade.closed_at,
    realized_pnl: trade.realized_pnl,
    fees: trade.fees,
    exit_reason: trade.exit_reason,
    source_updated_at: trade.closed_at,
    observed_at: trade.closed_at,
    last_reconciled_at: trade.closed_at,
    freshness: "CURRENT",
    reconciliation_status: trade.reconciliation_status,
    reason_code: null,
  };
}

function fixtureSnapshot(): RuntimeEvidenceSnapshot {
  const positions: RuntimeEvidencePosition[] = listFixturePositions().map((position) => ({
    ...position,
    source_position_id: position.position_id,
    source_updated_at: position.opened_at,
    observed_at: position.opened_at,
    last_reconciled_at: position.opened_at,
    freshness: "CURRENT",
    reconciliation_status: "SYNCED",
    reason_code: null,
  }));
  const orders: RuntimeEvidenceOrder[] = listFixtureOrders().map((order) => ({
    ...order,
    source_order_id: order.order_id,
    source_trade_id: null,
    source_updated_at: order.created_at,
    observed_at: order.created_at,
    last_reconciled_at: order.created_at,
    freshness: "CURRENT",
    reconciliation_status: "SYNCED",
    reason_code: null,
  }));
  const trades = listFixtureTrades().map(fixtureTrade);
  const statusKeys = new Map<string, RuntimeSourceStatus>();
  for (const [kind, records] of [
    ["OPEN_POSITIONS", positions],
    ["ORDERS", orders],
    ["TRADES", trades],
  ] as const) {
    for (const record of records) {
      const key = `${record.tenant_id}\0${record.bot_id}\0${record.source_runtime_id}\0${kind}`;
      const observedAt = record.observed_at ?? record.source_updated_at ?? "2026-07-22T12:00:00Z";
      statusKeys.set(key, {
        tenant_id: record.tenant_id,
        bot_id: record.bot_id,
        source_runtime_id: record.source_runtime_id,
        kind,
        source_observed_at: observedAt,
        observed_at: observedAt,
        last_reconciled_at: observedAt,
        freshness: "CURRENT",
        reconciliation_status: "SYNCED",
        complete: true,
        record_count: records.filter(
          (candidate) =>
            candidate.tenant_id === record.tenant_id &&
            candidate.bot_id === record.bot_id &&
            candidate.source_runtime_id === record.source_runtime_id,
        ).length,
        reason_code: null,
      });
    }
  }
  return { positions, orders, trades, source_statuses: [...statusKeys.values()] };
}

export async function runtimeEvidence(
  cookieHeader?: string | null,
): Promise<RuntimeEvidenceSnapshot> {
  if (dataMode() === "fixture") {
    return fixtureSnapshot();
  }
  const response = await fetch(`${controlPlaneUrl()}/v1/runtime-evidence`, {
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
  return (await response.json()) as RuntimeEvidenceSnapshot;
}

export function sourceStatusFor(
  snapshot: RuntimeEvidenceSnapshot,
  kind: RuntimeReadKind,
): RuntimeSourceStatus[] {
  return snapshot.source_statuses.filter((status) => status.kind === kind);
}

export function aggregateFreshness(
  statuses: RuntimeSourceStatus[],
): RuntimeReadFreshness | "UNAVAILABLE" {
  if (statuses.length === 0) {
    return "UNAVAILABLE";
  }
  if (statuses.some((status) => status.freshness === "SOURCE_UNAVAILABLE")) {
    return "SOURCE_UNAVAILABLE";
  }
  if (statuses.some((status) => status.freshness === "PARTIAL")) {
    return "PARTIAL";
  }
  if (statuses.some((status) => status.freshness === "STALE")) {
    return "STALE";
  }
  return "CURRENT";
}
