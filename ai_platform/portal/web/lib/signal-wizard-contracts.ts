export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

export interface PortalSessionView {
  principal_id: string;
  tenant_id: string;
}

export interface FeatureParameter {
  name: string;
  kinds: string[];
  default: JsonValue;
  minimum: number | null;
  maximum: number | null;
  choices: JsonValue[];
}

export interface SignalWizardFeature {
  feature_id: string;
  status: string;
  approved_for_ai: boolean;
  research_only: boolean;
  roles: string[];
  inputs: string[];
  dependencies: string[];
  required_sources: string[];
  parameters: FeatureParameter[];
  constraints: string[];
  warmup: string;
  timestamp_policy: string;
  normalization_policy: string;
  license_origin: string;
  definition_sha256: string;
  execution_authority: false;
}

export interface SignalWizardFeatureCatalog {
  registry_version: string;
  snapshot_sha256: string;
  features: SignalWizardFeature[];
  stale: boolean;
  reason_codes: string[];
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
  actor_type: "user";
  resource_type: "strategy";
  resource_id: string;
  environment: "research" | "test" | "staging";
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

export interface SignalWizardPreviewCommand {
  contract_version: "v2";
  context: ClosureRequestContext;
  idempotency_key: string;
  strategy_id: string;
  base_strategy_version: string | null;
  feature_selections: SignalWizardFeatureSelection[];
  parameter_constraints: SignalWizardParameterConstraint[];
  condition_ast: Record<string, JsonValue>;
  requested_strategy_schema_version: "2.0.0";
  capability: CapabilityRequirement;
}

export interface SignalWizardLeakageWarning {
  contract_version: "v2";
  reason_code: string;
  field_path: string;
  message: string;
  blocking: boolean;
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

export interface SignalWizardSubmitCommand {
  contract_version: "v2";
  context: ClosureRequestContext;
  idempotency_key: string;
  preview_hash: string;
  experiment_name: string;
  expected_strategy_version: string;
  capability: CapabilityRequirement;
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
  detail?: string | { reason_code?: string; message?: string };
  code?: string;
}
