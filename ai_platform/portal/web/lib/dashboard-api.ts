import { listFixtureBots } from "./fixtures";
import { dataMode, portalEnvironment, PortalApiConfigurationError, PortalApiResponseError } from "./portal-api";
import type {
  BotDesiredState,
  BotObservedState,
  ExecutionMode,
  PortalEnvironment,
} from "./contracts";

export type DashboardEvidenceSource =
  | "CONTROL_PLANE"
  | "RUNTIME"
  | "VALUATION"
  | "MODEL"
  | "RISK";

export type DashboardEvidenceState =
  | "CURRENT"
  | "ATTENTION"
  | "DEGRADED"
  | "STALE"
  | "PARTIAL"
  | "UNAVAILABLE"
  | "NOT_APPLICABLE";

export interface DashboardEvidenceStatus {
  source: DashboardEvidenceSource;
  state: DashboardEvidenceState;
  observed_at: string | null;
  reason_codes: string[];
}

export interface BotDashboardItem {
  bot_id: string;
  name: string;
  environment: PortalEnvironment;
  execution_mode: ExecutionMode;
  desired_state: BotDesiredState;
  observed_state: BotObservedState;
  config_revision: number;
  strategy_version: string;
  model_version: string;
  risk_policy_version: string;
  open_position_count: number;
  open_order_count: number;
  runtime_trade_count: number;
  realized_net_pnl: string | null;
  unrealized_pnl: string | null;
  evidence: {
    runtime: DashboardEvidenceStatus;
    valuation: DashboardEvidenceStatus;
    model: DashboardEvidenceStatus;
  };
  requires_attention: boolean;
  attention_reasons: string[];
}

export interface BotDashboardPage {
  schema_version: 1;
  generated_at: string;
  filters: {
    bot_ids: string[];
    environments: PortalEnvironment[];
    states: string[];
    occurred_from: string | null;
    occurred_to: string | null;
  };
  items: BotDashboardItem[];
  page_info: {
    requested_page_size: number;
    result_count: number;
    next_cursor: string | null;
    has_more: boolean;
  };
  totals: {
    matching_bot_count: number;
    active_bot_count: number;
    attention_bot_count: number;
    open_position_count: number;
    open_order_count: number;
    runtime_trade_count: number;
    risk_decision_count: number;
    realized_net_pnl: string | null;
    unrealized_pnl: string | null;
  };
  source_statuses: DashboardEvidenceStatus[];
}

const CSRF_COOKIE_NAME = "__Host-portal_csrf";
const CSRF_HEADER_NAME = "x-csrf-token";

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

function csrfHeader(cookieHeader?: string | null): Record<string, string> {
  if (!cookieHeader) {
    throw new PortalApiConfigurationError(
      "PORTAL_DASHBOARD_CSRF_MISSING: browser session cookies are required in API mode",
    );
  }
  const prefix = `${CSRF_COOKIE_NAME}=`;
  const encoded = cookieHeader
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(prefix))
    ?.slice(prefix.length);
  if (!encoded) {
    throw new PortalApiConfigurationError(
      "PORTAL_DASHBOARD_CSRF_MISSING: CSRF cookie is required in API mode",
    );
  }
  let token: string;
  try {
    token = decodeURIComponent(encoded);
  } catch {
    throw new PortalApiConfigurationError(
      "PORTAL_DASHBOARD_CSRF_INVALID: CSRF cookie is malformed",
    );
  }
  if (!token) {
    throw new PortalApiConfigurationError(
      "PORTAL_DASHBOARD_CSRF_MISSING: CSRF cookie is empty",
    );
  }
  return { [CSRF_HEADER_NAME]: token };
}

function fixtureEvidence(
  source: DashboardEvidenceSource,
  state: DashboardEvidenceState,
): DashboardEvidenceStatus {
  return {
    source,
    state,
    observed_at: "2026-07-28T18:00:00Z",
    reason_codes: ["DETERMINISTIC_FIXTURE_ONLY"],
  };
}

function fixtureDashboard(environment: PortalEnvironment): BotDashboardPage {
  const bots = listFixtureBots().filter((bot) => bot.spec.environment === environment);
  const items: BotDashboardItem[] = bots.map((bot) => ({
    bot_id: bot.bot_id,
    name: bot.name,
    environment: bot.spec.environment,
    execution_mode: bot.spec.execution_mode,
    desired_state: bot.desired_state,
    observed_state: bot.observed_state,
    config_revision: bot.spec.config_revision,
    strategy_version: bot.spec.strategy_version,
    model_version: bot.spec.model_version,
    risk_policy_version: bot.spec.risk_policy_version,
    open_position_count: 0,
    open_order_count: 0,
    runtime_trade_count: 0,
    realized_net_pnl: null,
    unrealized_pnl: null,
    evidence: {
      runtime: fixtureEvidence("RUNTIME", "PARTIAL"),
      valuation: fixtureEvidence("VALUATION", "NOT_APPLICABLE"),
      model: fixtureEvidence("MODEL", "PARTIAL"),
    },
    requires_attention: true,
    attention_reasons: ["DETERMINISTIC_FIXTURE_ONLY"],
  }));
  return {
    schema_version: 1,
    generated_at: "2026-07-28T18:00:00Z",
    filters: {
      bot_ids: [],
      environments: [environment],
      states: [],
      occurred_from: null,
      occurred_to: null,
    },
    items,
    page_info: {
      requested_page_size: 50,
      result_count: items.length,
      next_cursor: null,
      has_more: false,
    },
    totals: {
      matching_bot_count: items.length,
      active_bot_count: items.filter((item) => item.observed_state === "RUNNING").length,
      attention_bot_count: items.length,
      open_position_count: 0,
      open_order_count: 0,
      runtime_trade_count: 0,
      risk_decision_count: 0,
      realized_net_pnl: null,
      unrealized_pnl: null,
    },
    source_statuses: [
      fixtureEvidence("CONTROL_PLANE", "PARTIAL"),
      fixtureEvidence("MODEL", "PARTIAL"),
      fixtureEvidence("RISK", "UNAVAILABLE"),
      fixtureEvidence("RUNTIME", "PARTIAL"),
      fixtureEvidence("VALUATION", "NOT_APPLICABLE"),
    ],
  };
}

export async function dashboardSnapshot(cookieHeader?: string | null): Promise<BotDashboardPage> {
  const environment = portalEnvironment();
  if (dataMode() === "fixture") {
    return fixtureDashboard(environment);
  }
  const response = await fetch(`${controlPlaneUrl()}/v1/bot-management/dashboard/search`, {
    method: "POST",
    cache: "no-store",
    headers: {
      accept: "application/json",
      "content-type": "application/json",
      ...(cookieHeader ? { cookie: cookieHeader } : {}),
      ...csrfHeader(cookieHeader),
    },
    body: JSON.stringify({
      filters: {
        bot_ids: [],
        environments: [environment],
        states: [],
        occurred_from: null,
        occurred_to: null,
      },
      page: {
        page_size: 50,
        cursor: null,
        sort_field: "bot_id",
        sort_direction: "asc",
      },
    }),
  });
  if (!response.ok) {
    throw new PortalApiResponseError(
      `Portal dashboard request failed with status ${response.status}`,
      response.status,
    );
  }
  return (await response.json()) as BotDashboardPage;
}
