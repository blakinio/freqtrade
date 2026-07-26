import "server-only";

import type {
  AuditEvent,
  BotDesiredState,
  BotInstance,
  BotSpec,
  PerformanceSummary,
  RiskDecisionRecord,
} from "./contracts";
import {
  dataMode,
  getBot,
  listAuditEvents,
  listBots,
  listPerformance,
  listRiskEvents,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "./portal-api";
import type {
  ProfileSecurityView,
  RuntimeLogRecord,
  RuntimeObservabilitySourceStatus,
} from "./product-contracts";
import {
  getProfileSecurity,
  getRuntimeObservabilityAvailability,
  searchRuntimeLogs,
} from "./product-api";
import {
  aggregateFreshness,
  runtimeEvidence,
  type RuntimeEvidenceOrder,
  type RuntimeEvidencePosition,
  type RuntimeEvidenceSnapshot,
  type RuntimeEvidenceTrade,
  type RuntimeReadFreshness,
  type RuntimeSourceStatus,
} from "./runtime-evidence";
import { listValuations, type ValuationSnapshot, type ValuationState } from "./valuation";

export type BotRiskState = "NORMAL" | "ATTENTION" | "UNKNOWN" | "UNAVAILABLE";
export type BotRuntimeHealth = "HEALTHY" | "ATTENTION" | "DEGRADED" | "UNKNOWN" | "UNAVAILABLE";
export type BotEvidenceState =
  | RuntimeReadFreshness
  | ValuationState
  | "CURRENT"
  | "DENIED"
  | "UNAVAILABLE";

export interface BotMutationPermissions {
  revise: boolean;
  start: boolean;
  pause: boolean;
  stop: boolean;
  audit_read: boolean;
}

export interface BotFleetRecord {
  bot: BotInstance;
  open_position_count: number;
  position_state: BotEvidenceState;
  realized_net_pnl: string | null;
  unrealized_pnl: string | null;
  valuation_state: BotEvidenceState;
  risk_state: BotRiskState;
  runtime_health: BotRuntimeHealth;
  last_activity_at: string | null;
}

export interface BotOperationsDetail {
  bot: BotInstance;
  positions: RuntimeEvidencePosition[];
  orders: RuntimeEvidenceOrder[];
  trades: RuntimeEvidenceTrade[];
  source_statuses: RuntimeSourceStatus[];
  performance: PerformanceSummary | null;
  valuations: ValuationSnapshot[];
  risk_events: RiskDecisionRecord[];
  audit_events: AuditEvent[];
  runtime_logs: RuntimeLogRecord[];
  observability: RuntimeObservabilitySourceStatus | null;
  permissions: BotMutationPermissions;
  section_states: {
    runtime_evidence: BotEvidenceState;
    performance: BotEvidenceState;
    valuation: BotEvidenceState;
    risk: BotEvidenceState;
    audit: BotEvidenceState;
    runtime_logs: BotEvidenceState;
  };
}

interface OptionalResult<T> {
  value: T | null;
  state: "CURRENT" | "UNAVAILABLE";
}

async function optional<T>(promise: Promise<T>): Promise<OptionalResult<T>> {
  try {
    return { value: await promise, state: "CURRENT" };
  } catch {
    return { value: null, state: "UNAVAILABLE" };
  }
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

async function controlPlaneMutation<T>(path: string, body: unknown, cookieHeader?: string | null) {
  const response = await fetch(`${controlPlaneUrl()}${path}`, {
    method: "POST",
    cache: "no-store",
    headers: {
      accept: "application/json",
      "content-type": "application/json",
      ...(cookieHeader ? { cookie: cookieHeader } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new PortalApiResponseError(
      `Portal API request failed with status ${response.status}`,
      response.status,
    );
  }
  return (await response.json()) as T;
}

function permissionSet(profile: ProfileSecurityView | null): Set<string> {
  const permissions = new Set(profile?.permissions ?? []);
  if (dataMode() === "fixture") {
    for (const permission of [
      "bot.read",
      "bot.create",
      "bot.start",
      "bot.pause",
      "bot.stop",
      "audit.read",
    ]) {
      permissions.add(permission);
    }
  }
  return permissions;
}

function mutationPermissions(profile: ProfileSecurityView | null): BotMutationPermissions {
  const permissions = permissionSet(profile);
  return {
    revise: permissions.has("bot.create"),
    start: permissions.has("bot.start"),
    pause: permissions.has("bot.pause"),
    stop: permissions.has("bot.stop"),
    audit_read: permissions.has("audit.read"),
  };
}

function exactDecimalSum(values: string[]): string | null {
  if (values.length === 0) return null;
  const parsed = values.map((value) => {
    const match = value.trim().match(/^(-?)(\d+)(?:\.(\d+))?$/);
    if (!match) return null;
    return { negative: match[1] === "-", integer: match[2], fraction: match[3] ?? "" };
  });
  if (parsed.some((value) => value === null)) return null;
  const decimals = parsed as Array<{ negative: boolean; integer: string; fraction: string }>;
  const scale = Math.max(...decimals.map((value) => value.fraction.length));
  let total = 0n;
  for (const value of decimals) {
    const magnitude = BigInt(`${value.integer}${value.fraction.padEnd(scale, "0")}`);
    total += value.negative ? -magnitude : magnitude;
  }
  const negative = total < 0n;
  const absolute = negative ? -total : total;
  const digits = absolute.toString().padStart(scale + 1, "0");
  const integer = scale === 0 ? digits : digits.slice(0, -scale);
  const fraction = scale === 0 ? "" : digits.slice(-scale).replace(/0+$/, "");
  return `${negative ? "-" : ""}${integer}${fraction ? `.${fraction}` : ""}`;
}

function latestTimestamp(values: Array<string | null | undefined>): string | null {
  const valid = values
    .filter((value): value is string => typeof value === "string" && Number.isFinite(Date.parse(value)))
    .sort((left, right) => Date.parse(right) - Date.parse(left));
  return valid[0] ?? null;
}

function botRuntimeStatuses(snapshot: RuntimeEvidenceSnapshot | null, bot: BotInstance) {
  return (snapshot?.source_statuses ?? []).filter(
    (status) => status.tenant_id === bot.tenant_id && status.bot_id === bot.bot_id,
  );
}

function runtimeHealth(bot: BotInstance, statuses: RuntimeSourceStatus[]): BotRuntimeHealth {
  if (bot.observed_state === "ERROR") return "DEGRADED";
  if (statuses.length === 0) return "UNKNOWN";
  if (statuses.some((status) => status.freshness === "SOURCE_UNAVAILABLE")) return "UNAVAILABLE";
  if (
    statuses.some(
      (status) =>
        status.freshness === "STALE" ||
        status.freshness === "PARTIAL" ||
        status.reconciliation_status !== "SYNCED",
    )
  ) {
    return "ATTENTION";
  }
  return "HEALTHY";
}

function valuationState(values: ValuationSnapshot[], hasOpenPositions: boolean): BotEvidenceState {
  if (values.length === 0) return hasOpenPositions ? "UNAVAILABLE" : "CURRENT";
  if (values.some((value) => value.state === "SOURCE_UNAVAILABLE")) return "SOURCE_UNAVAILABLE";
  if (values.some((value) => value.state === "STALE")) return "STALE";
  if (values.some((value) => value.state === "UNPRICED")) return "UNPRICED";
  return "CURRENT";
}

function riskEventsForBot(
  bot: BotInstance,
  riskEvents: RiskDecisionRecord[],
  auditEvents: AuditEvent[],
): RiskDecisionRecord[] {
  const correlations = new Set(
    auditEvents
      .filter(
        (event) =>
          event.tenant_id === bot.tenant_id &&
          event.resource_type === "bot" &&
          event.resource_id === bot.bot_id,
      )
      .map((event) => event.correlation_id),
  );
  return riskEvents.filter(
    (event) => event.tenant_id === bot.tenant_id && correlations.has(event.context.correlation_id),
  );
}

function riskState(events: RiskDecisionRecord[], sourceAvailable: boolean): BotRiskState {
  if (!sourceAvailable) return "UNAVAILABLE";
  if (events.some((event) => event.decision === "REJECTED")) return "ATTENTION";
  if (events.length > 0) return "NORMAL";
  return "UNKNOWN";
}

function eventsForBot(bot: BotInstance, auditEvents: AuditEvent[]) {
  return auditEvents.filter(
    (event) =>
      event.tenant_id === bot.tenant_id &&
      event.resource_type === "bot" &&
      event.resource_id === bot.bot_id,
  );
}

export async function listBotFleetOperations(
  cookieHeader?: string | null,
): Promise<BotFleetRecord[]> {
  const bots = await listBots(cookieHeader);
  const [runtimeResult, performanceResult, valuationResult, riskResult, auditResult] =
    await Promise.all([
      optional(runtimeEvidence(cookieHeader)),
      optional(listPerformance(cookieHeader)),
      optional(listValuations(cookieHeader)),
      optional(listRiskEvents(cookieHeader)),
      optional(listAuditEvents(cookieHeader)),
    ]);

  return bots.map((bot) => {
    const positions = (runtimeResult.value?.positions ?? []).filter(
      (position) => position.tenant_id === bot.tenant_id && position.bot_id === bot.bot_id,
    );
    const currentPositions = positions.filter(
      (position) => position.freshness === "CURRENT" && position.reconciliation_status === "SYNCED",
    );
    const statuses = botRuntimeStatuses(runtimeResult.value, bot);
    const performance = (performanceResult.value ?? []).find(
      (entry) => entry.tenant_id === bot.tenant_id && entry.bot_id === bot.bot_id,
    );
    const valuations = (valuationResult.value ?? []).filter(
      (entry) => entry.tenant_id === bot.tenant_id && entry.bot_id === bot.bot_id,
    );
    const currentValuations = valuations.filter(
      (entry) => entry.state === "CURRENT" && entry.unrealized_pnl !== null,
    );
    const audits = eventsForBot(bot, auditResult.value ?? []);
    const risks = riskEventsForBot(bot, riskResult.value ?? [], audits);
    const orders = (runtimeResult.value?.orders ?? []).filter(
      (entry) => entry.tenant_id === bot.tenant_id && entry.bot_id === bot.bot_id,
    );
    const trades = (runtimeResult.value?.trades ?? []).filter(
      (entry) => entry.tenant_id === bot.tenant_id && entry.bot_id === bot.bot_id,
    );

    return {
      bot,
      open_position_count: currentPositions.length,
      position_state:
        runtimeResult.state === "UNAVAILABLE"
          ? "UNAVAILABLE"
          : aggregateFreshness(statuses.filter((status) => status.kind === "OPEN_POSITIONS")),
      realized_net_pnl: performance?.net_pnl ?? null,
      unrealized_pnl: exactDecimalSum(
        currentValuations.map((entry) => entry.unrealized_pnl as string),
      ),
      valuation_state:
        valuationResult.state === "UNAVAILABLE"
          ? "UNAVAILABLE"
          : valuationState(valuations, positions.length > 0),
      risk_state: riskState(risks, riskResult.state === "CURRENT" && auditResult.state === "CURRENT"),
      runtime_health:
        runtimeResult.state === "UNAVAILABLE" ? "UNAVAILABLE" : runtimeHealth(bot, statuses),
      last_activity_at: latestTimestamp([
        ...audits.map((event) => event.occurred_at),
        ...positions.map((entry) => entry.observed_at ?? entry.opened_at),
        ...orders.map((entry) => entry.observed_at ?? entry.created_at),
        ...trades.map((entry) => entry.observed_at ?? entry.closed_at ?? entry.opened_at),
      ]),
    };
  });
}

export async function getBotOperationsDetail(
  botId: string,
  cookieHeader?: string | null,
): Promise<BotOperationsDetail | null> {
  const bot = await getBot(botId, cookieHeader);
  if (!bot) return null;

  const [runtimeResult, performanceResult, valuationResult, riskResult, auditResult, profileResult, observabilityResult] =
    await Promise.all([
      optional(runtimeEvidence(cookieHeader)),
      optional(listPerformance(cookieHeader)),
      optional(listValuations(cookieHeader)),
      optional(listRiskEvents(cookieHeader)),
      optional(listAuditEvents(cookieHeader)),
      optional(getProfileSecurity(cookieHeader)),
      optional(getRuntimeObservabilityAvailability(cookieHeader)),
    ]);

  const permissions = mutationPermissions(profileResult.value);
  const positions = (runtimeResult.value?.positions ?? []).filter(
    (entry) => entry.tenant_id === bot.tenant_id && entry.bot_id === bot.bot_id,
  );
  const orders = (runtimeResult.value?.orders ?? []).filter(
    (entry) => entry.tenant_id === bot.tenant_id && entry.bot_id === bot.bot_id,
  );
  const trades = (runtimeResult.value?.trades ?? []).filter(
    (entry) => entry.tenant_id === bot.tenant_id && entry.bot_id === bot.bot_id,
  );
  const sourceStatuses = botRuntimeStatuses(runtimeResult.value, bot);
  const performance = (performanceResult.value ?? []).find(
    (entry) => entry.tenant_id === bot.tenant_id && entry.bot_id === bot.bot_id,
  ) ?? null;
  const valuations = (valuationResult.value ?? []).filter(
    (entry) => entry.tenant_id === bot.tenant_id && entry.bot_id === bot.bot_id,
  );
  const auditEvents = eventsForBot(bot, auditResult.value ?? []);
  const riskEvents = riskEventsForBot(bot, riskResult.value ?? [], auditEvents);

  let runtimeLogs: RuntimeLogRecord[] = [];
  let runtimeLogsState: BotEvidenceState = "UNAVAILABLE";
  const observability = observabilityResult.value;
  if (!permissions.audit_read) {
    runtimeLogsState = "DENIED";
  } else if (observabilityResult.state === "UNAVAILABLE") {
    runtimeLogsState = "UNAVAILABLE";
  } else if (observability?.availability !== "AVAILABLE") {
    runtimeLogsState = "SOURCE_UNAVAILABLE";
  } else {
    const end = new Date();
    const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
    const logsResult = await optional(
      searchRuntimeLogs(
        {
          start_at: start.toISOString(),
          end_at: end.toISOString(),
          bot_id: bot.bot_id,
          limit: 50,
        },
        cookieHeader,
      ),
    );
    if (logsResult.value) {
      runtimeLogs = logsResult.value.records.filter(
        (record) => record.tenant_id === bot.tenant_id && record.bot_id === bot.bot_id,
      );
      runtimeLogsState = logsResult.value.source_status.availability === "AVAILABLE"
        ? "CURRENT"
        : "SOURCE_UNAVAILABLE";
    }
  }

  return {
    bot,
    positions,
    orders,
    trades,
    source_statuses: sourceStatuses,
    performance,
    valuations,
    risk_events: riskEvents,
    audit_events: permissions.audit_read ? auditEvents : [],
    runtime_logs: runtimeLogs,
    observability,
    permissions,
    section_states: {
      runtime_evidence:
        runtimeResult.state === "UNAVAILABLE" ? "UNAVAILABLE" : aggregateFreshness(sourceStatuses),
      performance: performanceResult.state === "UNAVAILABLE" ? "UNAVAILABLE" : "CURRENT",
      valuation:
        valuationResult.state === "UNAVAILABLE"
          ? "UNAVAILABLE"
          : valuationState(valuations, positions.length > 0),
      risk: riskResult.state === "UNAVAILABLE" ? "UNAVAILABLE" : "CURRENT",
      audit: !permissions.audit_read
        ? "DENIED"
        : auditResult.state === "UNAVAILABLE"
          ? "UNAVAILABLE"
          : "CURRENT",
      runtime_logs: runtimeLogsState,
    },
  };
}

export function sameBotSpec(left: BotSpec, right: BotSpec): boolean {
  return (
    left.tenant_id === right.tenant_id &&
    left.strategy_version === right.strategy_version &&
    left.model_version === right.model_version &&
    left.risk_policy_version === right.risk_policy_version &&
    left.exchange_connection_ref === right.exchange_connection_ref &&
    left.pair_universe.length === right.pair_universe.length &&
    left.pair_universe.every((pair, index) => pair === right.pair_universe[index]) &&
    left.timeframe === right.timeframe &&
    left.capital_allocation === right.capital_allocation &&
    left.capital_currency === right.capital_currency &&
    left.runtime_version === right.runtime_version &&
    left.config_revision === right.config_revision &&
    left.environment === right.environment &&
    left.execution_mode === right.execution_mode
  );
}

export async function reviseBot(
  botId: string,
  spec: BotSpec,
  cookieHeader?: string | null,
): Promise<BotInstance> {
  if (dataMode() === "fixture") {
    const current = await getBot(botId, cookieHeader);
    if (!current) throw new PortalApiResponseError("Portal API request failed with status 404", 404);
    return { ...current, spec: structuredClone(spec) };
  }
  return controlPlaneMutation<BotInstance>(
    `/v1/bots/${encodeURIComponent(botId)}/revisions`,
    { spec },
    cookieHeader,
  );
}

export async function setBotDesiredState(
  botId: string,
  desiredState: Exclude<BotDesiredState, "CREATED">,
  cookieHeader?: string | null,
): Promise<BotInstance> {
  if (dataMode() === "fixture") {
    const current = await getBot(botId, cookieHeader);
    if (!current) throw new PortalApiResponseError("Portal API request failed with status 404", 404);
    return { ...current, desired_state: desiredState };
  }
  return controlPlaneMutation<BotInstance>(
    `/v1/bots/${encodeURIComponent(botId)}/desired-state`,
    { desired_state: desiredState },
    cookieHeader,
  );
}
