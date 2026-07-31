export type JsonPrimitive = null | boolean | number | string;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

export type SignalWizardFixtureView =
  | "default"
  | "empty"
  | "stale"
  | "failure"
  | "leakage"
  | "conflict";

export type SignalWizardOperator = "gt" | "gte" | "lt" | "lte" | "eq";
export type FeatureParameterKind = "integer" | "number" | "boolean" | "string" | "null";

export interface FeatureParameterReadModel {
  contract_version: "v1";
  name: string;
  kinds: FeatureParameterKind[];
  default: JsonValue;
  minimum: number | null;
  maximum: number | null;
  choices: JsonValue[];
}

export interface FeatureRegistryFeature {
  contract_version: "v1";
  feature_id: string;
  status: string;
  approved_for_ai: boolean;
  research_only: boolean;
  roles: string[];
  inputs: string[];
  dependencies: string[];
  required_sources: string[];
  parameters: FeatureParameterReadModel[];
  constraints: string[];
  warmup: string;
  timestamp_policy: string;
  normalization_policy: string;
  license_origin: string;
  definition_sha256: string;
  execution_authority: false;
}

export interface FeatureRegistrySnapshot {
  contract_version: "v1";
  registry_version: string;
  manifest_sha256: string;
  snapshot_sha256: string;
  feature_count: number;
  features: FeatureRegistryFeature[];
  execution_authority: false;
}

export interface SignalWizardBootstrap {
  contract_version: "v2";
  tenant_id: string;
  registry_version: string;
  snapshot_sha256: string;
  generated_at: string;
  stale: boolean;
  reason_codes: string[];
  features: FeatureRegistryFeature[];
  execution_authority: false;
}

export interface SignalWizardFeatureSelection {
  contract_version: "v2";
  feature_id: string;
  timeframe: string;
  parameters: Record<string, JsonValue>;
  enabled: boolean;
}

export interface SignalWizardParameterConstraint {
  contract_version: "v2";
  parameter: string;
  minimum: number | null;
  maximum: number | null;
  allowed_values: JsonValue[];
  reason_code: string;
}

export interface SignalWizardLeakageWarning {
  contract_version: "v2";
  reason_code: string;
  field_path: string;
  message: string;
  blocking: boolean;
}

export interface SignalWizardPreviewRequest {
  idempotency_key: string;
  strategy_id: string;
  base_strategy_version: string | null;
  registry_version: string;
  snapshot_sha256: string;
  feature_selections: SignalWizardFeatureSelection[];
  parameter_constraints: SignalWizardParameterConstraint[];
  condition_ast: Record<string, JsonValue>;
}

export interface SignalWizardSubmitRequest {
  idempotency_key: string;
  strategy_id: string;
  preview_hash: string;
  experiment_name: string;
  expected_strategy_version: string;
}

export interface CorrelationContext {
  contract_version: "v1";
  request_id: string;
  correlation_id: string;
  causation_id: string | null;
}

export interface PublicContractProvenance {
  contract_version: "v2";
  producer: string;
  artifact_id: string;
  created_at: string;
  source_refs: string[];
  metadata: Record<string, JsonValue>;
}

export interface ClosureRequestContext {
  contract_version: "v2";
  tenant_id: string;
  actor_id: string;
  actor_type: "user" | "service" | "agent";
  resource_type: string;
  resource_id: string;
  environment: "research" | "test" | "staging" | "production";
  execution_mode: "simulated" | "dry_run";
  correlation: CorrelationContext;
  provenance: PublicContractProvenance;
  authority: "research_only";
}

export interface CapabilityRequirement {
  contract_version: "v2";
  capability: "strategy.research" | "experiment.submit";
  authorization_decision_ref: string;
  enforced: true;
}

export interface SignalWizardPreviewCommand extends SignalWizardPreviewRequest {
  contract_version: "v2";
  context: ClosureRequestContext;
  requested_strategy_schema_version: "2.0.0";
  capability: CapabilityRequirement;
}

export interface SignalWizardSubmitCommand extends SignalWizardSubmitRequest {
  contract_version: "v2";
  context: ClosureRequestContext;
  capability: CapabilityRequirement;
}

export interface SignalWizardPreviewResult {
  contract_version: "v2";
  context: ClosureRequestContext;
  idempotency_key: string;
  strategy_definition: Record<string, JsonValue>;
  leakage_warnings: SignalWizardLeakageWarning[];
  reason_codes: string[];
  preview_hash: string;
  execution_authority: false;
  promotion_authority: false;
}

export interface SignalWizardSubmitResult {
  contract_version: "v2";
  context: ClosureRequestContext;
  idempotency_key: string;
  experiment_id: string;
  accepted: boolean;
  reason_codes: string[];
  execution_authority: false;
  promotion_authority: false;
}

export interface SignalWizardErrorPayload {
  detail: string;
  reason_code?: string;
  code?: string;
}

export interface ParameterValidationIssue {
  parameter: string;
  message: string;
  reason_code: string;
}

export function isSignalWizardPreviewRequest(value: unknown): value is SignalWizardPreviewRequest {
  if (!isRecord(value)) return false;
  return (
    isNonEmptyString(value.idempotency_key) &&
    isNonEmptyString(value.strategy_id) &&
    (value.base_strategy_version === null || typeof value.base_strategy_version === "string") &&
    isNonEmptyString(value.registry_version) &&
    isSha256(value.snapshot_sha256) &&
    Array.isArray(value.feature_selections) &&
    value.feature_selections.length > 0 &&
    value.feature_selections.every(isFeatureSelection) &&
    Array.isArray(value.parameter_constraints) &&
    value.parameter_constraints.every(isParameterConstraint) &&
    isRecord(value.condition_ast)
  );
}

export function isSignalWizardSubmitRequest(value: unknown): value is SignalWizardSubmitRequest {
  if (!isRecord(value)) return false;
  return (
    isNonEmptyString(value.idempotency_key) &&
    isNonEmptyString(value.strategy_id) &&
    isSha256(value.preview_hash) &&
    isNonEmptyString(value.experiment_name) &&
    isNonEmptyString(value.expected_strategy_version)
  );
}

export function defaultFeatureParameters(
  feature: FeatureRegistryFeature,
): Record<string, JsonValue> {
  return Object.fromEntries(feature.parameters.map((parameter) => [parameter.name, parameter.default]));
}

export function formatParameterInput(value: JsonValue): string {
  if (value === null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

export function parseParameterInput(
  parameter: FeatureParameterReadModel,
  rawValue: string,
): JsonValue {
  const trimmed = rawValue.trim();
  if (!trimmed && parameter.kinds.includes("null")) return null;
  if (parameter.kinds.includes("boolean")) return trimmed === "true";
  if (parameter.kinds.includes("integer")) {
    const parsed = Number(trimmed);
    return Number.isInteger(parsed) ? parsed : Number.NaN;
  }
  if (parameter.kinds.includes("number")) return Number(trimmed);
  return rawValue;
}

export function validateFeatureParameters(
  feature: FeatureRegistryFeature,
  parameters: Record<string, JsonValue>,
): ParameterValidationIssue[] {
  const issues: ParameterValidationIssue[] = [];
  const specifications = new Map(feature.parameters.map((parameter) => [parameter.name, parameter]));

  for (const parameter of feature.parameters) {
    const value = parameters[parameter.name];
    if (!matchesKind(value, parameter.kinds)) {
      issues.push({
        parameter: parameter.name,
        message: `${feature.feature_id}.${parameter.name} has an invalid value type`,
        reason_code: "FEATURE_PARAMETER_TYPE_INVALID",
      });
      continue;
    }
    if (typeof value === "number") {
      if (!Number.isFinite(value)) {
        issues.push({
          parameter: parameter.name,
          message: `${feature.feature_id}.${parameter.name} must be a finite number`,
          reason_code: "FEATURE_PARAMETER_TYPE_INVALID",
        });
        continue;
      }
      if (parameter.minimum !== null && value < parameter.minimum) {
        issues.push({
          parameter: parameter.name,
          message: `${feature.feature_id}.${parameter.name} must be at least ${parameter.minimum}`,
          reason_code: "FEATURE_PARAMETER_BELOW_MINIMUM",
        });
      }
      if (parameter.maximum !== null && value > parameter.maximum) {
        issues.push({
          parameter: parameter.name,
          message: `${feature.feature_id}.${parameter.name} must be at most ${parameter.maximum}`,
          reason_code: "FEATURE_PARAMETER_ABOVE_MAXIMUM",
        });
      }
    }
    if (parameter.choices.length > 0 && !parameter.choices.some((choice) => jsonEqual(choice, value))) {
      issues.push({
        parameter: parameter.name,
        message: `${feature.feature_id}.${parameter.name} must use an approved registry value`,
        reason_code: "FEATURE_PARAMETER_CHOICE_INVALID",
      });
    }
  }

  for (const name of Object.keys(parameters)) {
    if (!specifications.has(name)) {
      issues.push({
        parameter: name,
        message: `${feature.feature_id}.${name} is not declared by the registry`,
        reason_code: "FEATURE_PARAMETER_UNKNOWN",
      });
    }
  }

  for (const constraint of feature.constraints) {
    const issue = validateRelationalConstraint(feature, parameters, constraint);
    if (issue) issues.push(issue);
  }
  return issues;
}

function validateRelationalConstraint(
  feature: FeatureRegistryFeature,
  parameters: Record<string, JsonValue>,
  constraint: string,
): ParameterValidationIssue | null {
  const match = constraint.match(/^([A-Za-z0-9_]+)\s*(<=|<|>=|>)\s*([A-Za-z0-9_]+)$/);
  if (!match) return null;
  const [, leftName, operator, rightName] = match;
  const left = parameters[leftName];
  const right = parameters[rightName];
  if (typeof left !== "number" || typeof right !== "number") return null;
  const valid =
    (operator === "<" && left < right) ||
    (operator === "<=" && left <= right) ||
    (operator === ">" && left > right) ||
    (operator === ">=" && left >= right);
  if (valid) return null;
  return {
    parameter: leftName,
    message: `${feature.feature_id} requires ${constraint}`,
    reason_code: "FEATURE_PARAMETER_CONSTRAINT_INVALID",
  };
}

function isFeatureSelection(value: unknown): value is SignalWizardFeatureSelection {
  if (!isRecord(value)) return false;
  return (
    value.contract_version === "v2" &&
    isNonEmptyString(value.feature_id) &&
    isNonEmptyString(value.timeframe) &&
    typeof value.enabled === "boolean" &&
    isRecord(value.parameters)
  );
}

function isParameterConstraint(value: unknown): value is SignalWizardParameterConstraint {
  if (!isRecord(value)) return false;
  return (
    value.contract_version === "v2" &&
    isNonEmptyString(value.parameter) &&
    (value.minimum === null || typeof value.minimum === "number") &&
    (value.maximum === null || typeof value.maximum === "number") &&
    Array.isArray(value.allowed_values) &&
    isNonEmptyString(value.reason_code)
  );
}

function matchesKind(value: JsonValue | undefined, kinds: FeatureParameterKind[]): boolean {
  if (value === undefined) return false;
  if (value === null) return kinds.includes("null");
  if (typeof value === "boolean") return kinds.includes("boolean");
  if (typeof value === "string") return kinds.includes("string");
  if (typeof value === "number") {
    return (Number.isInteger(value) && kinds.includes("integer")) || kinds.includes("number");
  }
  return false;
}

function jsonEqual(left: JsonValue, right: JsonValue): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isSha256(value: unknown): value is string {
  return typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
}
