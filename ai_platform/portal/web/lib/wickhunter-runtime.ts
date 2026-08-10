import "server-only";

export type WickHunterManagedMode = "research" | "shadow" | "paper" | "live_blocked";
export type WickHunterHealth = "HEALTHY" | "DEGRADED" | "STALE";

export interface WickHunterLatestDecision {
  final_decision: string;
  status: string;
  symbol: string;
  calibrated_confidence: string | null;
  no_trade_confidence: string;
  observed_at_ms: number;
  record_sha256: string;
}

export interface WickHunterRuntimeEvidence {
  evidence_source: "synology_read_only_runtime_files";
  candidate_identity: "H900";
  run_id: string;
  mode: WickHunterManagedMode;
  health: WickHunterHealth;
  source_checked_at: string;
  source_runtime_generation: number;
  package_id: string;
  package_manifest_sha256: string;
  model_version: string;
  model_hash: string;
  model_artifact_sha256: string;
  parameter_version: string;
  parameter_hash: string;
  dataset_hash: string;
  operator_commit: string;
  no_trade_confidence: string;
  outcome_horizon_ms: number;
  decision_count: number;
  no_trade_count: number;
  latest_decision: WickHunterLatestDecision | null;
  paper_active: boolean;
  paper_activation_authorized: boolean;
  live_status: "BLOCKED";
  trading_credentials_present: boolean;
  order_adapter_present: boolean;
  execution_enabled: boolean;
  orders_submitted: number;
  live_capital_authorized: boolean;
  health_sha256: string;
  telemetry_sha256: string;
  identity_sha256: string;
}

export interface WickHunterPortalRuntimeView {
  bot_id: string;
  bot_name: string;
  managed_mode: WickHunterManagedMode;
  desired_runtime_generation_id: string | null;
  observed_runtime_generation_id: string | null;
  generations_synced: boolean;
  runtime_instance_id: string | null;
  adoption_provenance: "EXTERNAL_RUNTIME_ADOPTED";
  runtime: WickHunterRuntimeEvidence;
}

export type WickHunterRuntimeResult =
  | { state: "AVAILABLE"; view: WickHunterPortalRuntimeView }
  | { state: "UNAVAILABLE" }
  | { state: "NOT_WICKHUNTER" };

function controlPlaneUrl(): string {
  const value = process.env.PORTAL_CONTROL_PLANE_URL;
  if (!value) throw new Error("PORTAL_CONTROL_PLANE_URL is required in API mode");
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("PORTAL_CONTROL_PLANE_URL must use http or https");
  }
  return url.toString().replace(/\/$/, "");
}

export async function getWickHunterRuntime(
  botId: string,
  cookieHeader?: string | null,
): Promise<WickHunterRuntimeResult> {
  if (process.env.PORTAL_WEB_DATA_MODE === "fixture") return { state: "NOT_WICKHUNTER" };
  const response = await fetch(
    `${controlPlaneUrl()}/v1/bots/${encodeURIComponent(botId)}/wickhunter-runtime-evidence`,
    {
      cache: "no-store",
      headers: {
        accept: "application/json",
        ...(cookieHeader ? { cookie: cookieHeader } : {}),
      },
    },
  );
  if (response.status === 404) return { state: "NOT_WICKHUNTER" };
  if (response.status === 503) return { state: "UNAVAILABLE" };
  if (!response.ok) throw new Error(`WickHunter runtime API failed with status ${response.status}`);
  return { state: "AVAILABLE", view: (await response.json()) as WickHunterPortalRuntimeView };
}
