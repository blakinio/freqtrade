import { lstat, readFile } from "node:fs/promises";
import { resolve } from "node:path";

import {
  type WickHunterBotMode,
  type WickHunterDriftState,
  type WickHunterObservabilityView,
  type WickHunterPortalObservabilitySnapshot,
  type WickHunterRuntimeDecisionSummary,
  type WickHunterRuntimeHealth,
  type WickHunterRuntimeSourceStatus,
  type WickHunterShadowStatus,
  type WickHunterSimulatedPosition,
  type WickHunterSourceHealth,
  type WickHunterTradeDirection,
  WICKHUNTER_OBSERVABILITY_SCHEMA_VERSION,
} from "./contracts";

const MAX_SNAPSHOT_BYTES = 2 * 1024 * 1024;
const DEFAULT_STALE_AFTER_MS = 60_000;
const MAX_FUTURE_SKEW_MS = 5_000;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;
const GIT_SHA_PATTERN = /^[0-9a-f]{40}$/;
const DECIMAL_PATTERN = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;
const SYMBOL_PATTERN = /^[A-Z0-9][A-Z0-9:_-]{1,47}$/;

const BOT_MODES = new Set<WickHunterBotMode>(["research", "shadow", "paper"]);
const RUNTIME_HEALTH = new Set<WickHunterRuntimeHealth>([
  "healthy",
  "degraded",
  "fail_closed",
]);
const SOURCE_HEALTH = new Set<WickHunterSourceHealth>([
  "healthy",
  "degraded",
  "failed",
  "unknown",
]);
const DRIFT_STATES = new Set<WickHunterDriftState>(["healthy", "drifted", "unknown"]);
const SHADOW_STATUSES = new Set<WickHunterShadowStatus>([
  "simulated_allowed",
  "ignored",
  "rejected_by_risk",
]);
const SIDES = new Set<WickHunterTradeDirection>(["long", "short"]);

export class WickHunterObservabilityUnavailableError extends Error {}
export class WickHunterObservabilityIntegrityError extends Error {}

export interface WickHunterObservabilityReaderOptions {
  snapshotPath?: string;
  staleAfterMs?: number;
  now?: () => number;
  fixtureMode?: boolean;
}

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new WickHunterObservabilityIntegrityError(`${field} must be an object`);
  }
  return value as Record<string, unknown>;
}

function text(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new WickHunterObservabilityIntegrityError(`${field} must be a non-empty string`);
  }
  return value;
}

function nullableText(value: unknown, field: string): string | null {
  return value === null ? null : text(value, field);
}

function booleanValue(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") {
    throw new WickHunterObservabilityIntegrityError(`${field} must be a boolean`);
  }
  return value;
}

function safeInteger(value: unknown, field: string, minimum = 0): number {
  if (!Number.isSafeInteger(value) || (value as number) < minimum) {
    throw new WickHunterObservabilityIntegrityError(
      `${field} must be a safe integer >= ${minimum}`,
    );
  }
  return value as number;
}

function nullableSafeInteger(value: unknown, field: string, minimum = 0): number | null {
  return value === null ? null : safeInteger(value, field, minimum);
}

function decimal(value: unknown, field: string, positive = false): string {
  const parsed = text(value, field);
  if (!DECIMAL_PATTERN.test(parsed)) {
    throw new WickHunterObservabilityIntegrityError(`${field} must be a decimal string`);
  }
  const numeric = Number(parsed);
  if (!Number.isFinite(numeric) || (positive && numeric <= 0)) {
    throw new WickHunterObservabilityIntegrityError(`${field} has an invalid decimal value`);
  }
  return parsed;
}

function sha256(value: unknown, field: string): string {
  const parsed = text(value, field);
  if (!SHA256_PATTERN.test(parsed)) {
    throw new WickHunterObservabilityIntegrityError(`${field} must be a lowercase SHA-256`);
  }
  return parsed;
}

function nullableSha256(value: unknown, field: string): string | null {
  return value === null ? null : sha256(value, field);
}

function nullableGitSha(value: unknown, field: string): string | null {
  if (value === null) return null;
  const parsed = text(value, field);
  if (!GIT_SHA_PATTERN.test(parsed)) {
    throw new WickHunterObservabilityIntegrityError(`${field} must be a lowercase Git SHA`);
  }
  return parsed;
}

function enumValue<T extends string>(value: unknown, field: string, allowed: Set<T>): T {
  const parsed = text(value, field) as T;
  if (!allowed.has(parsed)) {
    throw new WickHunterObservabilityIntegrityError(`${field} has an unsupported value`);
  }
  return parsed;
}

function stringArray(value: unknown, field: string): string[] {
  if (!Array.isArray(value)) {
    throw new WickHunterObservabilityIntegrityError(`${field} must be an array`);
  }
  const parsed = value.map((item, index) => text(item, `${field}[${index}]`));
  if (parsed.length !== new Set(parsed).size) {
    throw new WickHunterObservabilityIntegrityError(`${field} must contain unique values`);
  }
  return parsed;
}

function sortedStringArray(value: unknown, field: string): string[] {
  const parsed = stringArray(value, field);
  if (parsed.join("\0") !== [...parsed].sort().join("\0")) {
    throw new WickHunterObservabilityIntegrityError(`${field} must be sorted`);
  }
  return parsed;
}

function validateSource(value: unknown, index: number): WickHunterRuntimeSourceStatus {
  const source = record(value, `source_freshness[${index}]`);
  const lastReceived = nullableSafeInteger(
    source.last_received_at_ms,
    `source_freshness[${index}].last_received_at_ms`,
    1,
  );
  const age = nullableSafeInteger(source.age_ms, `source_freshness[${index}].age_ms`);
  const fresh = booleanValue(source.fresh, `source_freshness[${index}].fresh`);
  if (lastReceived === null && (age !== null || fresh)) {
    throw new WickHunterObservabilityIntegrityError(
      `source_freshness[${index}] cannot be fresh without received data`,
    );
  }
  return {
    source: text(source.source, `source_freshness[${index}].source`),
    health: enumValue(
      source.health,
      `source_freshness[${index}].health`,
      SOURCE_HEALTH,
    ),
    observed_at_ms: safeInteger(
      source.observed_at_ms,
      `source_freshness[${index}].observed_at_ms`,
      1,
    ),
    last_received_at_ms: lastReceived,
    age_ms: age,
    fresh,
  };
}

function validateDecision(value: unknown, index: number): WickHunterRuntimeDecisionSummary {
  const decision = record(value, `decisions[${index}]`);
  const side = decision.side === null ? null : enumValue(decision.side, `decisions[${index}].side`, SIDES);
  return {
    shadow_decision_id: sha256(
      decision.shadow_decision_id,
      `decisions[${index}].shadow_decision_id`,
    ),
    status: enumValue(decision.status, `decisions[${index}].status`, SHADOW_STATUSES),
    symbol: text(decision.symbol, `decisions[${index}].symbol`),
    side,
    candidate_id: nullableSha256(decision.candidate_id, `decisions[${index}].candidate_id`),
    score_id: nullableSha256(decision.score_id, `decisions[${index}].score_id`),
    risk_decision_id: nullableSha256(
      decision.risk_decision_id,
      `decisions[${index}].risk_decision_id`,
    ),
    reason_codes: sortedStringArray(decision.reason_codes, `decisions[${index}].reason_codes`),
    observed_at_ms: safeInteger(
      decision.observed_at_ms,
      `decisions[${index}].observed_at_ms`,
      1,
    ),
  };
}

function validatePosition(value: unknown, index: number): WickHunterSimulatedPosition {
  const position = record(value, `positions[${index}]`);
  return {
    position_id: sha256(position.position_id, `positions[${index}].position_id`),
    trade_intent_id: sha256(position.trade_intent_id, `positions[${index}].trade_intent_id`),
    symbol: text(position.symbol, `positions[${index}].symbol`),
    side: enumValue(position.side, `positions[${index}].side`, SIDES),
    opened_at_ms: safeInteger(position.opened_at_ms, `positions[${index}].opened_at_ms`, 1),
    entry_price: decimal(position.entry_price, `positions[${index}].entry_price`, true),
    mark_price: decimal(position.mark_price, `positions[${index}].mark_price`, true),
    quantity: decimal(position.quantity, `positions[${index}].quantity`, true),
    take_profit_price: decimal(
      position.take_profit_price,
      `positions[${index}].take_profit_price`,
      true,
    ),
    stop_loss_price: decimal(
      position.stop_loss_price,
      `positions[${index}].stop_loss_price`,
      true,
    ),
    model_version: nullableText(position.model_version, `positions[${index}].model_version`),
    model_hash: nullableSha256(position.model_hash, `positions[${index}].model_hash`),
    parameter_version: text(
      position.parameter_version,
      `positions[${index}].parameter_version`,
    ),
    parameter_hash: sha256(position.parameter_hash, `positions[${index}].parameter_hash`),
  };
}

function validateSnapshot(value: unknown): WickHunterPortalObservabilitySnapshot {
  const snapshot = record(value, "snapshot");
  if (snapshot.schema_version !== WICKHUNTER_OBSERVABILITY_SCHEMA_VERSION) {
    throw new WickHunterObservabilityIntegrityError("snapshot schema version mismatch");
  }
  if (
    snapshot.read_only !== true ||
    snapshot.trading_credentials_present !== false ||
    snapshot.order_adapter_present !== false ||
    snapshot.orders_submitted !== 0 ||
    snapshot.live_capital_authorized !== false
  ) {
    throw new WickHunterObservabilityIntegrityError(
      "snapshot contains forbidden execution authority",
    );
  }

  const universe = sortedStringArray(snapshot.dynamic_universe, "dynamic_universe");
  for (const [index, symbol] of universe.entries()) {
    if (!SYMBOL_PATTERN.test(symbol)) {
      throw new WickHunterObservabilityIntegrityError(
        `dynamic_universe[${index}] is not a canonical symbol`,
      );
    }
  }

  if (!Array.isArray(snapshot.source_freshness)) {
    throw new WickHunterObservabilityIntegrityError("source_freshness must be an array");
  }
  const sources = snapshot.source_freshness.map(validateSource);
  const sourceNames = sources.map((item) => item.source);
  if (sourceNames.join("\0") !== [...sourceNames].sort().join("\0")) {
    throw new WickHunterObservabilityIntegrityError("source_freshness must be sorted");
  }

  if (!Array.isArray(snapshot.decisions) || !Array.isArray(snapshot.positions)) {
    throw new WickHunterObservabilityIntegrityError("decisions and positions must be arrays");
  }
  const decisions = snapshot.decisions.map(validateDecision);
  const positions = snapshot.positions.map(validatePosition);

  const modelVersion = nullableText(snapshot.model_version, "model_version");
  const modelHash = nullableSha256(snapshot.model_hash, "model_hash");
  const parameterVersion = nullableText(snapshot.parameter_version, "parameter_version");
  const parameterHash = nullableSha256(snapshot.parameter_hash, "parameter_hash");
  if ((modelVersion === null) !== (modelHash === null)) {
    throw new WickHunterObservabilityIntegrityError("model identity is incomplete");
  }
  if ((parameterVersion === null) !== (parameterHash === null)) {
    throw new WickHunterObservabilityIntegrityError("parameter identity is incomplete");
  }

  return {
    schema_version: WICKHUNTER_OBSERVABILITY_SCHEMA_VERSION,
    snapshot_id: sha256(snapshot.snapshot_id, "snapshot_id"),
    bot_instance: text(snapshot.bot_instance, "bot_instance"),
    mode: enumValue(snapshot.mode, "mode", BOT_MODES),
    health: enumValue(snapshot.health, "health", RUNTIME_HEALTH),
    observed_at_ms: safeInteger(snapshot.observed_at_ms, "observed_at_ms", 1),
    universe_snapshot_hash: sha256(snapshot.universe_snapshot_hash, "universe_snapshot_hash"),
    dynamic_universe: universe,
    source_freshness: sources,
    model_version: modelVersion,
    model_hash: modelHash,
    parameter_version: parameterVersion,
    parameter_hash: parameterHash,
    dataset_hash: nullableSha256(snapshot.dataset_hash, "dataset_hash"),
    code_sha: nullableGitSha(snapshot.code_sha, "code_sha"),
    decisions,
    positions,
    cumulative_realized_pnl_quote: decimal(
      snapshot.cumulative_realized_pnl_quote,
      "cumulative_realized_pnl_quote",
    ),
    unrealized_pnl_quote: decimal(snapshot.unrealized_pnl_quote, "unrealized_pnl_quote"),
    simulated_equity_quote: decimal(
      snapshot.simulated_equity_quote,
      "simulated_equity_quote",
      true,
    ),
    drawdown_ratio: decimal(snapshot.drawdown_ratio, "drawdown_ratio"),
    retraining_state: text(snapshot.retraining_state, "retraining_state"),
    validation_state: text(snapshot.validation_state, "validation_state"),
    model_drift: enumValue(snapshot.model_drift, "model_drift", DRIFT_STATES),
    data_drift: enumValue(snapshot.data_drift, "data_drift", DRIFT_STATES),
    circuit_breaker_active: booleanValue(
      snapshot.circuit_breaker_active,
      "circuit_breaker_active",
    ),
    circuit_breaker_reasons: sortedStringArray(
      snapshot.circuit_breaker_reasons,
      "circuit_breaker_reasons",
    ),
    persistence_generation: safeInteger(
      snapshot.persistence_generation,
      "persistence_generation",
    ),
    runtime_state_sha256: sha256(snapshot.runtime_state_sha256, "runtime_state_sha256"),
    read_only: true,
    trading_credentials_present: false,
    order_adapter_present: false,
    orders_submitted: 0,
    live_capital_authorized: false,
  };
}

function configuredSnapshotPath(options: WickHunterObservabilityReaderOptions): {
  path: string;
  fixtureMode: boolean;
} {
  const fixtureMode = options.fixtureMode ?? process.env.PORTAL_WEB_DATA_MODE === "fixture";
  if (options.snapshotPath) {
    return { path: resolve(options.snapshotPath), fixtureMode };
  }
  if (fixtureMode) {
    return {
      path: resolve(process.cwd(), "fixtures/wickhunter/portal-observability-snapshot.json"),
      fixtureMode: true,
    };
  }
  const configured = process.env.PORTAL_WICKHUNTER_SNAPSHOT_PATH?.trim();
  if (!configured) {
    throw new WickHunterObservabilityUnavailableError(
      "WickHunter observability snapshot path is not configured",
    );
  }
  return { path: resolve(configured), fixtureMode: false };
}

export async function readWickHunterObservability(
  options: WickHunterObservabilityReaderOptions = {},
): Promise<WickHunterObservabilityView> {
  const selected = configuredSnapshotPath(options);
  let metadata;
  try {
    metadata = await lstat(selected.path);
  } catch {
    throw new WickHunterObservabilityUnavailableError(
      "WickHunter observability snapshot is unavailable",
    );
  }
  if (metadata.isSymbolicLink() || !metadata.isFile()) {
    throw new WickHunterObservabilityIntegrityError(
      "WickHunter observability snapshot must be a regular file",
    );
  }
  if (metadata.size > MAX_SNAPSHOT_BYTES) {
    throw new WickHunterObservabilityIntegrityError(
      "WickHunter observability snapshot exceeds the size limit",
    );
  }

  let raw: unknown;
  try {
    raw = JSON.parse(await readFile(selected.path, "utf8")) as unknown;
  } catch {
    throw new WickHunterObservabilityIntegrityError(
      "WickHunter observability snapshot is not valid JSON",
    );
  }
  const snapshot = validateSnapshot(raw);
  const now = (options.now ?? Date.now)();
  if (!Number.isSafeInteger(now) || now <= 0) {
    throw new WickHunterObservabilityIntegrityError("reader clock is invalid");
  }
  if (!selected.fixtureMode && snapshot.observed_at_ms > now + MAX_FUTURE_SKEW_MS) {
    throw new WickHunterObservabilityIntegrityError("snapshot is observed in the future");
  }
  const age = selected.fixtureMode ? 0 : Math.max(0, now - snapshot.observed_at_ms);
  const staleAfterMs = options.staleAfterMs ?? DEFAULT_STALE_AFTER_MS;
  if (!Number.isSafeInteger(staleAfterMs) || staleAfterMs < 1) {
    throw new WickHunterObservabilityIntegrityError("staleAfterMs must be a positive integer");
  }
  return {
    snapshot,
    snapshot_age_ms: age,
    stale: age > staleAfterMs,
    source_path_kind: selected.fixtureMode ? "fixture" : "configured",
  };
}
