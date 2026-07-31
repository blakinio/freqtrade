import { createHash } from "node:crypto";
import type { NextRequest } from "next/server";

import {
  FIXTURE_STATE_COOKIE_NAME,
  fixtureIdentityMode,
  forwardedIdentityHeaders,
  forwardControlPlaneMutation,
} from "@/lib/identity";
import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "@/lib/portal-api";
import type {
  JsonValue,
  SignalWizardFeature,
  SignalWizardFeatureCatalog,
  SignalWizardPreviewCommand,
  SignalWizardPreviewResult,
  SignalWizardSubmitCommand,
  SignalWizardSubmitResult,
} from "@/lib/signal-wizard-contracts";

function controlPlaneUrl(): string {
  const value = process.env.PORTAL_CONTROL_PLANE_URL;
  if (!value) throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL is required");
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL must use HTTP or HTTPS");
  }
  return url.toString().replace(/\/$/, "");
}

async function responsePayload(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { detail: `Signal Wizard backend returned non-JSON status ${response.status}` };
  }
}

function detail(payload: unknown, fallback: string): string {
  if (typeof payload !== "object" || payload === null) return fallback;
  const raw = (payload as { detail?: unknown }).detail;
  if (typeof raw === "string") return raw;
  if (typeof raw === "object" && raw !== null) {
    const message = (raw as { message?: unknown }).message;
    if (typeof message === "string") return message;
  }
  return fallback;
}

function cookieValue(header: string | null | undefined, name: string): string | null {
  if (!header) return null;
  for (const item of header.split(";")) {
    const [rawName, ...rest] = item.trim().split("=");
    if (rawName === name) return decodeURIComponent(rest.join("="));
  }
  return null;
}

function enforceFixtureRead(cookieHeader?: string | null): void {
  if (!fixtureIdentityMode()) return;
  const state = cookieValue(cookieHeader, FIXTURE_STATE_COOKIE_NAME) ?? "authenticated";
  if (state === "anonymous" || state === "expired" || state === "revoked") {
    throw new PortalApiResponseError("Portal session is missing or no longer valid", 401);
  }
  if (state === "cross_tenant") {
    throw new PortalApiResponseError(
      "Authenticated membership does not authorize this tenant",
      403,
    );
  }
}

const fixtureFeatures: SignalWizardFeature[] = [
  {
    feature_id: "atr.v1",
    status: "active",
    approved_for_ai: true,
    research_only: true,
    roles: ["volatility"],
    inputs: ["high", "low", "close"],
    dependencies: [],
    required_sources: ["candles"],
    parameters: [
      { name: "period", kinds: ["integer"], default: 14, minimum: 2, maximum: 200, choices: [] },
    ],
    constraints: ["closed bars only"],
    warmup: "period + 1 bars",
    timestamp_policy: "closed_bar",
    normalization_policy: "raw",
    license_origin: "clean-room",
    definition_sha256: "a".repeat(64),
    execution_authority: false,
  },
  {
    feature_id: "rsi.v1",
    status: "active",
    approved_for_ai: true,
    research_only: true,
    roles: ["momentum"],
    inputs: ["close"],
    dependencies: [],
    required_sources: ["candles"],
    parameters: [
      { name: "period", kinds: ["integer"], default: 14, minimum: 2, maximum: 200, choices: [] },
    ],
    constraints: ["closed bars only"],
    warmup: "period + 1 bars",
    timestamp_policy: "closed_bar",
    normalization_policy: "bounded_0_100",
    license_origin: "clean-room",
    definition_sha256: "b".repeat(64),
    execution_authority: false,
  },
  {
    feature_id: "macd.v1",
    status: "active",
    approved_for_ai: true,
    research_only: true,
    roles: ["trend", "momentum"],
    inputs: ["close"],
    dependencies: [],
    required_sources: ["candles"],
    parameters: [
      { name: "fast_period", kinds: ["integer"], default: 12, minimum: 2, maximum: 100, choices: [] },
      { name: "slow_period", kinds: ["integer"], default: 26, minimum: 3, maximum: 300, choices: [] },
      { name: "signal_period", kinds: ["integer"], default: 9, minimum: 2, maximum: 100, choices: [] },
    ],
    constraints: ["fast_period must be lower than slow_period", "closed bars only"],
    warmup: "slow_period + signal_period bars",
    timestamp_policy: "closed_bar",
    normalization_policy: "raw",
    license_origin: "clean-room",
    definition_sha256: "c".repeat(64),
    execution_authority: false,
  },
];

export async function listSignalWizardFeatures(
  cookieHeader?: string | null,
): Promise<SignalWizardFeatureCatalog> {
  if (dataMode() === "fixture") {
    enforceFixtureRead(cookieHeader);
    return {
      registry_version: "fixture-registry-v1",
      snapshot_sha256: "f".repeat(64),
      features: fixtureFeatures,
      stale: false,
      reason_codes: ["APPROVED_FEATURES_ONLY", "FIXTURE_EVIDENCE"],
    };
  }
  const response = await fetch(
    `${controlPlaneUrl()}/v1/feature-registry/features?approved_for_ai=true`,
    {
      cache: "no-store",
      redirect: "manual",
      headers: {
        accept: "application/json",
        ...(forwardedIdentityHeaders(cookieHeader) ?? {}),
      },
    },
  );
  const payload = await responsePayload(response);
  if (!response.ok) {
    throw new PortalApiResponseError(
      detail(payload, `Feature Registry request failed with status ${response.status}`),
      response.status,
    );
  }
  return {
    registry_version: "canonical-feature-registry",
    snapshot_sha256: "",
    features: payload as SignalWizardFeature[],
    stale: false,
    reason_codes: ["APPROVED_FEATURES_ONLY", "CANONICAL_CONTROL_PLANE"],
  };
}

export async function previewSignalWizard(
  request: NextRequest,
  command: SignalWizardPreviewCommand,
): Promise<SignalWizardPreviewResult> {
  if (dataMode() !== "fixture") {
    return forwardControlPlaneMutation<SignalWizardPreviewResult>(
      request,
      "/v1/signal-wizard/preview",
      "POST",
      command,
    );
  }
  const enabled = command.feature_selections.filter((item) => item.enabled);
  if (enabled.length === 0) {
    throw new PortalApiResponseError("At least one approved feature is required", 422);
  }
  const allowed = new Set(fixtureFeatures.map((feature) => feature.feature_id));
  const invalid = enabled.find((item) => !allowed.has(item.feature_id));
  if (invalid) {
    throw new PortalApiResponseError(`Feature is not approved for AI use: ${invalid.feature_id}`, 422);
  }
  const digest = createHash("sha256")
    .update(JSON.stringify(command))
    .digest("hex");
  const version = command.base_strategy_version ?? `${command.strategy_id}:wizard:${digest.slice(0, 12)}`;
  const strategyDefinition: Record<string, JsonValue> = {
    schema_version: "2.0.0",
    strategy_id: command.strategy_id,
    version,
    features: enabled.map((selection) => ({
      id: selection.feature_id,
      timeframe: selection.timeframe,
      params: selection.parameters,
      confirmation: "closed_bar",
    })),
    condition_ast: command.condition_ast,
    parameter_constraints: command.parameter_constraints.map((constraint) => ({
      contract_version: constraint.contract_version,
      parameter: constraint.parameter,
      minimum: constraint.minimum,
      maximum: constraint.maximum,
      allowed_values: constraint.allowed_values,
      reason_code: constraint.reason_code,
    })),
    authority: "research_only",
    execution: {
      mode: command.context.execution_mode,
      use_closed_bars_only: true,
      execution_authority: false,
    },
    risk: { live_capital_authority: false },
  };
  return {
    contract_version: "v2",
    context: command.context,
    idempotency_key: command.idempotency_key,
    strategy_definition: strategyDefinition,
    leakage_warnings:
      command.strategy_id === "leakage-warning-candidate"
        ? [
            {
              contract_version: "v2",
              reason_code: "FEATURE_TIMESTAMP_POLICY_REQUIRES_REVIEW",
              field_path: "feature_selections[0].feature_id",
              message: "Fixture demonstrates a blocking repaint/leakage warning.",
              blocking: true,
            },
          ]
        : [],
    reason_codes: [
      "SIGNAL_WIZARD_PREVIEW_VALIDATED",
      "RESEARCH_ONLY",
      "FIXTURE_EVIDENCE",
      ...(command.strategy_id === "leakage-warning-candidate"
        ? ["LEAKAGE_WARNING_PRESENT"]
        : []),
    ],
    preview_hash: createHash("sha256").update(JSON.stringify(strategyDefinition)).digest("hex"),
    execution_authority: false,
    promotion_authority: false,
  };
}

export async function submitSignalWizard(
  request: NextRequest,
  command: SignalWizardSubmitCommand,
): Promise<SignalWizardSubmitResult> {
  if (dataMode() !== "fixture") {
    return forwardControlPlaneMutation<SignalWizardSubmitResult>(
      request,
      "/v1/signal-wizard/submit",
      "POST",
      command,
    );
  }
  if (!command.experiment_name.trim()) {
    throw new PortalApiResponseError("Experiment name is required", 422);
  }
  if (command.experiment_name.trim().toLowerCase() === "conflict") {
    throw new PortalApiResponseError("Preview version changed before submission", 409);
  }
  return {
    contract_version: "v2",
    context: command.context,
    idempotency_key: command.idempotency_key,
    experiment_id: createHash("sha256")
      .update(`${command.context.tenant_id}:${command.idempotency_key}:${command.preview_hash}`)
      .digest("hex")
      .slice(0, 32),
    accepted: true,
    reason_codes: ["SIGNAL_WIZARD_CANDIDATE_PERSISTED", "RESEARCH_ONLY", "FIXTURE_EVIDENCE"],
    execution_authority: false,
    promotion_authority: false,
  };
}
