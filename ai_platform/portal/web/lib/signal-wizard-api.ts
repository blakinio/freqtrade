import "server-only";

import { createHash, randomUUID } from "node:crypto";
import type { NextRequest } from "next/server";

import {
  fixtureIdentityMode,
  fixtureIdentityState,
  fixtureSession,
  forwardedIdentityHeaders,
  identityBackendFetch,
  responsePayload,
  type PortalSessionView,
} from "./identity";
import { dataMode, portalEnvironment } from "./portal-api";
import type {
  CapabilityRequirement,
  ClosureRequestContext,
  FeatureParameterReadModel,
  FeatureRegistryFeature,
  FeatureRegistrySnapshot,
  JsonValue,
  SignalWizardBootstrap,
  SignalWizardFeatureSelection,
  SignalWizardFixtureView,
  SignalWizardLeakageWarning,
  SignalWizardParameterConstraint,
  SignalWizardPreviewCommand,
  SignalWizardPreviewRequest,
  SignalWizardPreviewResult,
  SignalWizardSubmitCommand,
  SignalWizardSubmitRequest,
  SignalWizardSubmitResult,
} from "./signal-wizard-contracts";
import { validateFeatureParameters } from "./signal-wizard-contracts";

const FIXTURE_GENERATED_AT = "2026-07-31T07:00:00Z";
const FIXTURE_REGISTRY_VERSION = "1.0.0";
const FIXTURE_MANIFEST_SHA = "a".repeat(64);
const FIXTURE_SNAPSHOT_SHA = "b".repeat(64);

export class SignalWizardApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly reasonCode?: string,
  ) {
    super(message);
  }
}

interface FixturePreviewRecord {
  requestDigest: string;
  result: SignalWizardPreviewResult;
}

interface FixtureSubmissionRecord {
  requestDigest: string;
  result: SignalWizardSubmitResult;
}

interface FixtureStore {
  previewByHash: Map<string, SignalWizardPreviewResult>;
  previewByIdempotency: Map<string, FixturePreviewRecord>;
  submissionByIdempotency: Map<string, FixtureSubmissionRecord>;
}

type SignalWizardGlobal = typeof globalThis & {
  __signalWizardFixtureStore?: FixtureStore;
};

export async function getSignalWizardBootstrap(
  request: NextRequest,
  fixtureView: SignalWizardFixtureView,
): Promise<SignalWizardBootstrap> {
  const session = await sessionForRequest(request);
  if (dataMode() === "fixture" && fixtureView === "failure") {
    throw new SignalWizardApiError(
      "Signal Wizard feature registry fixture is unavailable",
      503,
      "SIGNAL_WIZARD_REGISTRY_UNAVAILABLE",
    );
  }
  const snapshot = await registrySnapshot(request);
  assertNoExecutionAuthority(snapshot);
  const features = snapshot.features.filter((feature) => feature.approved_for_ai);
  return {
    contract_version: "v2",
    tenant_id: session.tenant_id,
    registry_version: snapshot.registry_version,
    snapshot_sha256: snapshot.snapshot_sha256,
    generated_at: dataMode() === "fixture" ? FIXTURE_GENERATED_AT : new Date().toISOString(),
    stale: dataMode() === "fixture" && fixtureView === "stale",
    reason_codes:
      dataMode() === "fixture" && fixtureView === "stale"
        ? ["FEATURE_REGISTRY_SNAPSHOT_STALE"]
        : [],
    features:
      dataMode() === "fixture" && fixtureView === "empty" ? [] : structuredClone(features),
    execution_authority: false,
  };
}

export async function previewSignalWizard(
  request: NextRequest,
  previewRequest: SignalWizardPreviewRequest,
  fixtureView: SignalWizardFixtureView,
): Promise<SignalWizardPreviewResult> {
  const session = await sessionForRequest(request);
  const snapshot = await registrySnapshot(request);
  validateRegistryIdentity(previewRequest, snapshot);
  validateSelectedFeatures(previewRequest.feature_selections, snapshot);
  validateConditionAst(previewRequest.condition_ast, previewRequest.feature_selections);
  validateRequestedConstraints(
    previewRequest.parameter_constraints,
    previewRequest.feature_selections,
  );
  const command = previewCommand(session, previewRequest);

  if (dataMode() === "fixture") {
    return fixturePreview(command, fixtureView);
  }
  return controlPlaneJson<SignalWizardPreviewResult>(
    request,
    "/v1/signal-wizard/preview",
    "POST",
    command,
  );
}

export async function submitSignalWizard(
  request: NextRequest,
  submitRequest: SignalWizardSubmitRequest,
  fixtureView: SignalWizardFixtureView,
): Promise<SignalWizardSubmitResult> {
  const session = await sessionForRequest(request);
  const command = submitCommand(session, submitRequest);
  if (dataMode() === "fixture") {
    return fixtureSubmit(command, fixtureView);
  }
  return controlPlaneJson<SignalWizardSubmitResult>(
    request,
    "/v1/signal-wizard/submit",
    "POST",
    command,
  );
}

function previewCommand(
  session: PortalSessionView,
  request: SignalWizardPreviewRequest,
): SignalWizardPreviewCommand {
  return {
    ...request,
    contract_version: "v2",
    context: commandContext(
      session,
      request.strategy_id,
      request.idempotency_key,
      request.registry_version,
      request.snapshot_sha256,
      "preview",
    ),
    requested_strategy_schema_version: "2.0.0",
    capability: capability(session, "strategy.research"),
  };
}

function submitCommand(
  session: PortalSessionView,
  request: SignalWizardSubmitRequest,
): SignalWizardSubmitCommand {
  return {
    ...request,
    contract_version: "v2",
    context: commandContext(
      session,
      request.strategy_id,
      request.idempotency_key,
      "persisted-preview",
      request.preview_hash,
      "submit",
    ),
    capability: capability(session, "experiment.submit"),
  };
}

function commandContext(
  session: PortalSessionView,
  strategyId: string,
  idempotencyKey: string,
  sourceVersion: string,
  sourceIdentity: string,
  operation: "preview" | "submit",
): ClosureRequestContext {
  const environment = portalEnvironment();
  if (environment === "production") {
    throw new SignalWizardApiError(
      "Signal Wizard commands are forbidden in the production environment",
      422,
      "SIGNAL_WIZARD_PRODUCTION_FORBIDDEN",
    );
  }
  return {
    contract_version: "v2",
    tenant_id: session.tenant_id,
    actor_id: session.principal_id,
    actor_type: "user",
    resource_type: "strategy",
    resource_id: strategyId,
    environment,
    execution_mode: "simulated",
    correlation: {
      contract_version: "v1",
      request_id: randomUUID(),
      correlation_id: randomUUID(),
      causation_id: null,
    },
    provenance: {
      contract_version: "v2",
      producer: "portal-signal-wizard-bff",
      artifact_id: `signal-wizard:${operation}:${idempotencyKey}`,
      created_at: session.created_at,
      source_refs: [`${sourceVersion}:${sourceIdentity}`],
      metadata: {
        boundary: "same_origin_portal_bff",
        evidence_scope: "research_command",
      },
    },
    authority: "research_only",
  };
}

function capability(
  session: PortalSessionView,
  value: "strategy.research" | "experiment.submit",
): CapabilityRequirement {
  return {
    contract_version: "v2",
    capability: value,
    authorization_decision_ref: `membership:${session.membership_id}:${value}`,
    enforced: true,
  };
}

async function sessionForRequest(request: NextRequest): Promise<PortalSessionView> {
  if (fixtureIdentityMode()) return fixtureSession(fixtureIdentityState(request));
  const response = await identityBackendFetch("/v1/identity/session", {
    headers: request.headers.get("cookie")
      ? { cookie: request.headers.get("cookie") as string }
      : undefined,
  });
  const payload = await responsePayload(response);
  if (!response.ok) throw errorFromPayload(payload, response.status, "PORTAL_SESSION_UNAVAILABLE");
  return payload as PortalSessionView;
}

async function registrySnapshot(request: NextRequest): Promise<FeatureRegistrySnapshot> {
  if (dataMode() === "fixture") return fixtureSnapshot();
  return controlPlaneJson<FeatureRegistrySnapshot>(
    request,
    "/v1/feature-registry/snapshot",
    "GET",
  );
}

async function controlPlaneJson<T>(
  request: NextRequest,
  path: string,
  method: "GET" | "POST",
  body?: unknown,
): Promise<T> {
  const cookieHeader = request.headers.get("cookie");
  const response = await identityBackendFetch(path, {
    method,
    headers: {
      ...forwardedIdentityHeaders(cookieHeader),
      ...(body === undefined ? {} : { "content-type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const payload = await responsePayload(response);
  if (!response.ok) throw errorFromPayload(payload, response.status, "SIGNAL_WIZARD_UPSTREAM_ERROR");
  return payload as T;
}

function errorFromPayload(
  payload: unknown,
  status: number,
  fallbackReason: string,
): SignalWizardApiError {
  if (isRecord(payload)) {
    const detail = payload.detail;
    if (typeof detail === "string") {
      return new SignalWizardApiError(detail, status, fallbackReason);
    }
    if (isRecord(detail)) {
      const reason = typeof detail.reason_code === "string" ? detail.reason_code : fallbackReason;
      const message =
        typeof detail.message === "string"
          ? detail.message
          : `Signal Wizard request failed with status ${status}`;
      return new SignalWizardApiError(message, status, reason);
    }
  }
  return new SignalWizardApiError(
    `Signal Wizard request failed with status ${status}`,
    status,
    fallbackReason,
  );
}

function validateRegistryIdentity(
  request: SignalWizardPreviewRequest,
  snapshot: FeatureRegistrySnapshot,
): void {
  if (
    request.registry_version !== snapshot.registry_version ||
    request.snapshot_sha256 !== snapshot.snapshot_sha256
  ) {
    throw new SignalWizardApiError(
      "The selected feature registry snapshot is stale; reload before preview",
      409,
      "FEATURE_REGISTRY_SNAPSHOT_CONFLICT",
    );
  }
}

function validateSelectedFeatures(
  selections: SignalWizardFeatureSelection[],
  snapshot: FeatureRegistrySnapshot,
): void {
  const enabled = selections.filter((selection) => selection.enabled);
  if (enabled.length === 0) {
    throw new SignalWizardApiError(
      "At least one approved feature must be enabled",
      422,
      "SIGNAL_WIZARD_NO_ENABLED_FEATURES",
    );
  }
  const definitions = new Map(snapshot.features.map((feature) => [feature.feature_id, feature]));
  const selectedIds = new Set(enabled.map((selection) => selection.feature_id));
  for (const selection of enabled) {
    const definition = definitions.get(selection.feature_id);
    if (!definition) {
      throw new SignalWizardApiError(
        `Unknown Feature Registry identity: ${selection.feature_id}`,
        422,
        "FEATURE_REGISTRY_UNKNOWN_FEATURE",
      );
    }
    if (!definition.approved_for_ai) {
      throw new SignalWizardApiError(
        `Feature is not approved for AI use: ${selection.feature_id}`,
        422,
        "FEATURE_NOT_APPROVED_FOR_AI",
      );
    }
    for (const dependency of definition.dependencies) {
      if (!selectedIds.has(dependency)) {
        throw new SignalWizardApiError(
          `Explicitly select required dependency: ${dependency}`,
          422,
          "FEATURE_DEPENDENCY_MISSING",
        );
      }
    }
    const issues = validateFeatureParameters(definition, selection.parameters);
    if (issues.length > 0) {
      throw new SignalWizardApiError(issues[0].message, 422, issues[0].reason_code);
    }
  }
}

function validateConditionAst(
  conditionAst: Record<string, JsonValue>,
  selections: SignalWizardFeatureSelection[],
): void {
  const selected = new Set(
    selections.filter((selection) => selection.enabled).map((selection) => selection.feature_id),
  );
  const referenced = new Set<string>();
  collectConditionFeatures(conditionAst, referenced);
  if (referenced.size === 0) {
    throw new SignalWizardApiError(
      "The typed condition AST must reference at least one selected feature",
      422,
      "CONDITION_GROUP_EMPTY",
    );
  }
  for (const featureId of referenced) {
    if (!selected.has(featureId)) {
      throw new SignalWizardApiError(
        `Condition references an undeclared feature: ${featureId}`,
        422,
        "FEATURE_NOT_DECLARED",
      );
    }
  }
}

function collectConditionFeatures(value: JsonValue, result: Set<string>): void {
  if (Array.isArray(value)) {
    for (const child of value) collectConditionFeatures(child, result);
    return;
  }
  if (!isRecord(value)) return;
  if (typeof value.feature === "string") result.add(value.feature);
  for (const child of Object.values(value)) collectConditionFeatures(child as JsonValue, result);
}

function validateRequestedConstraints(
  constraints: SignalWizardParameterConstraint[],
  selections: SignalWizardFeatureSelection[],
): void {
  const values = new Map<string, JsonValue[]>();
  for (const selection of selections.filter((item) => item.enabled)) {
    for (const [name, value] of Object.entries(selection.parameters)) {
      const existing = values.get(name) ?? [];
      existing.push(value);
      values.set(name, existing);
    }
  }
  for (const constraint of constraints) {
    const candidates = values.get(constraint.parameter);
    if (!candidates || candidates.length === 0) {
      throw new SignalWizardApiError(
        `Constraint references an undeclared parameter: ${constraint.parameter}`,
        422,
        "PARAMETER_CONSTRAINT_UNKNOWN",
      );
    }
    for (const value of candidates) {
      if (typeof value === "number") {
        if (constraint.minimum !== null && value < constraint.minimum) {
          throw new SignalWizardApiError(
            `${constraint.parameter} is below the requested minimum`,
            422,
            constraint.reason_code,
          );
        }
        if (constraint.maximum !== null && value > constraint.maximum) {
          throw new SignalWizardApiError(
            `${constraint.parameter} exceeds the requested maximum`,
            422,
            constraint.reason_code,
          );
        }
      }
      if (
        constraint.allowed_values.length > 0 &&
        !constraint.allowed_values.some((allowed) => JSON.stringify(allowed) === JSON.stringify(value))
      ) {
        throw new SignalWizardApiError(
          `${constraint.parameter} is outside the requested allowed values`,
          422,
          constraint.reason_code,
        );
      }
    }
  }
}

function fixturePreview(
  command: SignalWizardPreviewCommand,
  fixtureView: SignalWizardFixtureView,
): SignalWizardPreviewResult {
  const store = fixtureStore();
  const idempotencyIdentity = `${command.context.tenant_id}:${command.idempotency_key}`;
  const requestDigest = sha256Json({
    strategy_id: command.strategy_id,
    base_strategy_version: command.base_strategy_version,
    feature_selections: command.feature_selections,
    parameter_constraints: command.parameter_constraints,
    condition_ast: command.condition_ast,
  });
  const existing = store.previewByIdempotency.get(idempotencyIdentity);
  if (existing) {
    if (existing.requestDigest !== requestDigest) {
      throw new SignalWizardApiError(
        "Preview idempotency key was already used for another command",
        409,
        "SIGNAL_WIZARD_CONFLICT",
      );
    }
    return structuredClone(existing.result);
  }

  const warnings: SignalWizardLeakageWarning[] =
    fixtureView === "leakage"
      ? [
          {
            contract_version: "v2",
            reason_code: "FEATURE_TIMESTAMP_POLICY_REQUIRES_REVIEW",
            field_path: "feature_selections[0].feature_id",
            message: "Fixture simulates a feature timestamp policy that requires review.",
            blocking: true,
          },
        ]
      : [];
  const strategyVersion =
    command.base_strategy_version ?? `${command.strategy_id}:wizard:${requestDigest.slice(0, 12)}`;
  const strategyDefinition: Record<string, JsonValue> = {
    schema_version: "2.0.0",
    strategy_id: command.strategy_id,
    version: strategyVersion,
    base_strategy_version: command.base_strategy_version,
    features: command.feature_selections
      .filter((selection) => selection.enabled)
      .map((selection) => ({
        id: selection.feature_id,
        params: selection.parameters,
        timeframe: selection.timeframe,
        confirmation: "closed_bar",
      })),
    condition_ast: command.condition_ast,
    parameter_constraints: command.parameter_constraints,
    feature_registry: {
      registry_version: command.registry_version,
      snapshot_sha256: command.snapshot_sha256,
    },
    execution: {
      mode: "simulated",
      use_closed_bars_only: true,
      execution_authority: false,
    },
    risk: { max_leverage: 1, live_capital_authority: false },
    authority: "research_only",
    provenance: command.context.provenance,
  };
  const previewHash = sha256Json({
    tenant_id: command.context.tenant_id,
    strategy_definition: strategyDefinition,
  });
  const result: SignalWizardPreviewResult = {
    contract_version: "v2",
    context: command.context,
    idempotency_key: command.idempotency_key,
    strategy_definition: strategyDefinition,
    leakage_warnings: warnings,
    reason_codes: [
      "SIGNAL_WIZARD_PREVIEW_VALIDATED",
      "RESEARCH_ONLY",
      ...(warnings.length > 0 ? ["LEAKAGE_WARNING_PRESENT"] : []),
    ],
    preview_hash: previewHash,
    execution_authority: false,
    promotion_authority: false,
  };
  store.previewByIdempotency.set(idempotencyIdentity, { requestDigest, result });
  store.previewByHash.set(`${command.context.tenant_id}:${previewHash}`, result);
  return structuredClone(result);
}

function fixtureSubmit(
  command: SignalWizardSubmitCommand,
  fixtureView: SignalWizardFixtureView,
): SignalWizardSubmitResult {
  if (fixtureView === "conflict") {
    throw new SignalWizardApiError(
      "Fixture simulates an expected strategy version conflict",
      409,
      "SIGNAL_WIZARD_CONFLICT",
    );
  }
  const store = fixtureStore();
  const preview = store.previewByHash.get(
    `${command.context.tenant_id}:${command.preview_hash}`,
  );
  if (!preview) {
    throw new SignalWizardApiError(
      "Signal Wizard preview was not found",
      404,
      "SIGNAL_WIZARD_PREVIEW_NOT_FOUND",
    );
  }
  if (preview.context.resource_id !== command.context.resource_id) {
    throw new SignalWizardApiError(
      "Preview target does not match submit target",
      409,
      "SIGNAL_WIZARD_CONFLICT",
    );
  }
  const version = preview.strategy_definition.version;
  if (typeof version !== "string" || version !== command.expected_strategy_version) {
    throw new SignalWizardApiError(
      "Expected strategy version does not match the persisted preview",
      409,
      "SIGNAL_WIZARD_CONFLICT",
    );
  }
  if (preview.leakage_warnings.some((warning) => warning.blocking)) {
    throw new SignalWizardApiError(
      "Preview contains blocking leakage warnings",
      409,
      "SIGNAL_WIZARD_CONFLICT",
    );
  }

  const identity = `${command.context.tenant_id}:${command.idempotency_key}`;
  const requestDigest = sha256Json({
    preview_hash: command.preview_hash,
    experiment_name: command.experiment_name,
    expected_strategy_version: command.expected_strategy_version,
    strategy_id: command.strategy_id,
  });
  const existing = store.submissionByIdempotency.get(identity);
  if (existing) {
    if (existing.requestDigest !== requestDigest) {
      throw new SignalWizardApiError(
        "Submit idempotency key was already used for another command",
        409,
        "SIGNAL_WIZARD_CONFLICT",
      );
    }
    return structuredClone(existing.result);
  }
  const result: SignalWizardSubmitResult = {
    contract_version: "v2",
    context: command.context,
    idempotency_key: command.idempotency_key,
    experiment_id: `fixture-experiment-${requestDigest.slice(0, 20)}`,
    accepted: true,
    reason_codes: ["SIGNAL_WIZARD_CANDIDATE_PERSISTED", "RESEARCH_ONLY"],
    execution_authority: false,
    promotion_authority: false,
  };
  store.submissionByIdempotency.set(identity, { requestDigest, result });
  return structuredClone(result);
}

function fixtureStore(): FixtureStore {
  const target = globalThis as SignalWizardGlobal;
  target.__signalWizardFixtureStore ??= {
    previewByHash: new Map(),
    previewByIdempotency: new Map(),
    submissionByIdempotency: new Map(),
  };
  return target.__signalWizardFixtureStore;
}

function fixtureSnapshot(): FeatureRegistrySnapshot {
  const features = fixtureFeatures();
  return {
    contract_version: "v1",
    registry_version: FIXTURE_REGISTRY_VERSION,
    manifest_sha256: FIXTURE_MANIFEST_SHA,
    snapshot_sha256: FIXTURE_SNAPSHOT_SHA,
    feature_count: features.length,
    features,
    execution_authority: false,
  };
}

function fixtureFeatures(): FeatureRegistryFeature[] {
  return [
    feature("atr.v1", "validated", ["regime", "risk", "ml_feature"], [
      parameter("period", ["integer"], 14, 2, 200),
      parameter("ma_type", ["string"], "rma", null, null, ["rma", "sma"]),
    ], [], "closed_bar", "period + 1", "atr / close", "1"),
    feature("squeeze_ratio.v1", "experimental", ["regime", "ml_feature"], [], [], "closed_bar", "22", "bb_width / kc_width", "2", false),
    feature("macd.v1", "validated", ["trigger", "confirmation", "ml_feature"], [
      parameter("fast", ["integer"], 12, 2, 100),
      parameter("slow", ["integer"], 26, 3, 200),
      parameter("signal", ["integer"], 9, 2, 100),
      parameter("signal_ma_type", ["string"], "ema", null, null, ["ema", "sma"]),
      parameter("confirmation", ["string"], "closed_bar", null, null, ["closed_bar", "confirmed_htf"]),
    ], ["fast < slow"], "closed_bar_or_confirmed_htf", "slow + signal + 2", "macd / atr", "3"),
    feature("candle_geometry.v1", "validated", ["confirmation", "ml_feature"], [], [], "closed_bar", "1", "ratios in [0,1]", "4"),
    feature("rsi.v1", "validated", ["confirmation", "ml_feature"], [
      parameter("period", ["integer"], 14, 2, 100),
      parameter("ma_type", ["string"], "rma", null, null, ["rma", "sma"]),
    ], [], "closed_bar", "period + 1", "value / 100", "5"),
    feature("roc.v1", "validated", ["trigger", "confirmation", "ml_feature"], [
      parameter("period", ["integer"], 12, 1, 200),
    ], [], "closed_bar", "period + 1", "percent", "6"),
    feature("volume_ema_osc.v1", "validated", ["confirmation", "ml_feature"], [
      parameter("fast", ["integer"], 5, 1, 50),
      parameter("slow", ["integer"], 10, 2, 200),
    ], ["fast < slow"], "closed_bar", "slow + 1", "percent", "7"),
    feature("volume_robust_z.v1", "validated", ["confirmation", "ml_feature"], [
      parameter("window", ["integer"], 100, 20, 5000),
    ], [], "closed_bar", "2 * window", "median absolute deviation z-score", "8"),
    feature("no_repeat_signals_policy.v1", "validated", ["signal_policy"], [
      parameter("cooldown_bars", ["integer"], 0, 0, 1000),
    ], [], "same_as_confirmed_input_signal", "none", "event {-1,0,1}", "9"),
  ];
}

function feature(
  featureId: string,
  status: string,
  roles: string[],
  parameters: FeatureParameterReadModel[],
  constraints: string[],
  timestampPolicy: string,
  warmup: string,
  normalizationPolicy: string,
  hashSeed: string,
  approvedForAi = true,
): FeatureRegistryFeature {
  return {
    contract_version: "v1",
    feature_id: featureId,
    status,
    approved_for_ai: approvedForAi,
    research_only: true,
    roles,
    inputs: [],
    dependencies: [],
    required_sources: [],
    parameters,
    constraints,
    warmup,
    timestamp_policy: timestampPolicy,
    normalization_policy: normalizationPolicy,
    license_origin: "repository_fixture_from_frozen_registry",
    definition_sha256: hashSeed.repeat(64).slice(0, 64),
    execution_authority: false,
  };
}

function parameter(
  name: string,
  kinds: FeatureParameterReadModel["kinds"],
  defaultValue: JsonValue,
  minimum: number | null,
  maximum: number | null,
  choices: JsonValue[] = [],
): FeatureParameterReadModel {
  return {
    contract_version: "v1",
    name,
    kinds,
    default: defaultValue,
    minimum,
    maximum,
    choices,
  };
}

function assertNoExecutionAuthority(snapshot: FeatureRegistrySnapshot): void {
  if (
    snapshot.execution_authority ||
    snapshot.features.some((feature) => feature.execution_authority)
  ) {
    throw new SignalWizardApiError(
      "Feature Registry returned unexpected execution authority",
      502,
      "FEATURE_REGISTRY_AUTHORITY_INVALID",
    );
  }
}

function sha256Json(value: unknown): string {
  return createHash("sha256").update(canonicalJson(value)).digest("hex");
}

function canonicalJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (isRecord(value)) {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
