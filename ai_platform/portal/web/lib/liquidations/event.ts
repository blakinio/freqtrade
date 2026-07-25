import { normalizeDecimal } from "./decimal";
import type {
  LiquidatedPositionSide,
  LiquidationSource,
  PortalLiquidationEvent,
} from "./contracts";

const SYMBOL_PATTERN = /^[A-Z0-9]{2,24}$/;
const MAX_IDENTIFIER_LENGTH = 256;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function integer(value: unknown, field: string): number {
  const parsed = typeof value === "string" && /^\d+$/.test(value) ? Number(value) : value;
  if (typeof parsed !== "number" || !Number.isSafeInteger(parsed)) {
    throw new Error(`${field} must be a safe integer`);
  }
  return parsed;
}

function nonEmptyString(value: unknown, field: string): string {
  if (typeof value !== "string") {
    throw new Error(`${field} must be a string`);
  }
  const parsed = value.trim();
  if (!parsed || parsed.length > MAX_IDENTIFIER_LENGTH) {
    throw new Error(`${field} must be non-empty and bounded`);
  }
  return parsed;
}

function decimal(value: unknown, field: string): string {
  if (typeof value !== "string" && typeof value !== "number") {
    throw new Error(`${field} must be decimal-compatible`);
  }
  const parsed = normalizeDecimal(String(value));
  if (parsed === "0") {
    throw new Error(`${field} must be greater than zero`);
  }
  return parsed;
}

export function parsePortalLiquidationEvent(
  value: unknown,
  expectedSource: LiquidationSource,
): PortalLiquidationEvent {
  if (!isRecord(value)) {
    throw new Error("liquidation event must be an object");
  }
  const schemaVersion = integer(value.schema_version, "schema_version");
  if (schemaVersion !== 1) {
    throw new Error("schema_version must be 1");
  }
  const source = nonEmptyString(value.source, "source");
  if (source !== expectedSource) {
    throw new Error("source does not match the fixed source file");
  }
  const sourceEventId = nonEmptyString(value.source_event_id, "source_event_id");
  const symbol = nonEmptyString(value.symbol, "symbol").toUpperCase();
  if (!SYMBOL_PATTERN.test(symbol)) {
    throw new Error("symbol has an invalid format");
  }
  const side = nonEmptyString(
    value.liquidated_position_side,
    "liquidated_position_side",
  ) as LiquidatedPositionSide;
  if (side !== "long" && side !== "short") {
    throw new Error("liquidated_position_side must be long or short");
  }
  const occurredAtMs = integer(value.occurred_at_ms, "occurred_at_ms");
  const receivedAtMs = integer(value.received_at_ms, "received_at_ms");
  if (occurredAtMs <= 0 || receivedAtMs < occurredAtMs) {
    throw new Error("event timestamps are invalid");
  }
  return {
    schema_version: 1,
    source: expectedSource,
    source_event_id: sourceEventId,
    symbol,
    liquidated_position_side: side,
    occurred_at_ms: occurredAtMs,
    received_at_ms: receivedAtMs,
    ingest_latency_ms: receivedAtMs - occurredAtMs,
    price: decimal(value.price, "price"),
    quantity: decimal(value.quantity, "quantity"),
    notional_usd: decimal(value.notional_usd, "notional_usd"),
  };
}
