export type StrategyCapability =
  | "strategy.read"
  | "strategy.research"
  | "experiment.submit"
  | "strategy.approve"
  | "strategy.deploy_dry_run"
  | "strategy.rollback_dry_run";

export type StrategyLifecycleState =
  | "DRAFT"
  | "REVIEW_PENDING"
  | "APPROVED"
  | "DRY_RUN"
  | "SHADOW"
  | "ROLLED_BACK"
  | "RETIRED";

export type StrategyApprovalDecision = "PENDING" | "APPROVED" | "REJECTED";
export type StrategyDeploymentMode = "SIMULATED" | "DRY_RUN" | "SHADOW";
export type StrategyDeploymentState =
  | "REQUESTED"
  | "ACTIVE"
  | "STOPPED"
  | "ROLLED_BACK"
  | "FAILED";

export interface PublicContractProvenance {
  contract_version: "v2";
  producer: string;
  artifact_id: string;
  created_at: string;
  source_refs: string[];
  metadata: Record<string, unknown>;
}

export interface StrategyCatalogEntry {
  strategy_version: string;
  display_name: string;
  description: string;
  kind: "DIRECTIONAL" | "GRID";
  allowed_execution_modes: Array<"simulated" | "dry_run">;
  runtime_status: "BOT_REFERENCE" | "PORTAL_CONFIG_ONLY";
  immutable: boolean;
  lifecycle_state: StrategyLifecycleState;
  current_revision: number;
  approval_required: boolean;
  required_capabilities: StrategyCapability[];
  provenance_ref: string | null;
}

export interface StrategyVersionHistoryEntry {
  contract_version: "v2";
  tenant_id: string;
  strategy_version: string;
  revision: number;
  lifecycle_state: StrategyLifecycleState;
  immutable_hash: string;
  created_by_actor_id: string;
  created_at: string;
  provenance: PublicContractProvenance;
}

export interface StrategyApprovalRecord {
  contract_version: "v2";
  tenant_id: string;
  strategy_version: string;
  approval_id: string;
  decision: StrategyApprovalDecision;
  required_capability: "strategy.approve";
  decided_by_actor_id: string | null;
  decided_at: string | null;
  reason_codes: string[];
  provenance: PublicContractProvenance;
}

export interface StrategyDeploymentRecord {
  contract_version: "v2";
  tenant_id: string;
  deployment_id: string;
  strategy_version: string;
  environment: "research" | "test" | "staging" | "production";
  mode: StrategyDeploymentMode;
  state: StrategyDeploymentState;
  deployed_by_actor_id: string;
  deployed_at: string;
  provenance: PublicContractProvenance;
  live_capital_authority: false;
}

export interface StrategyCatalogDetail {
  contract_version: "v2";
  tenant_id: string;
  entry: StrategyCatalogEntry;
  history: StrategyVersionHistoryEntry[];
  approvals: StrategyApprovalRecord[];
  deployments: StrategyDeploymentRecord[];
  rollback_targets: string[];
  provenance: PublicContractProvenance;
  required_capabilities: StrategyCapability[];
}

export interface StrategyCatalogListResponse {
  contract_version: "v2";
  tenant_id: string;
  generated_at: string;
  stale: boolean;
  reason_codes: string[];
  entries: StrategyCatalogEntry[];
}

export interface StrategyRollbackRequest {
  to_strategy_version: string;
  reason: string;
  idempotency_key: string;
}

export interface StrategyRollbackResult {
  contract_version: "v2";
  tenant_id: string;
  source_strategy_version: string;
  target_strategy_version: string;
  accepted: boolean;
  lifecycle_state: StrategyLifecycleState;
  reason_codes: string[];
  audit_evidence_ref: string;
  evidence_state: "RECORDED" | "REJECTED";
  execution_authority: false;
  live_capital_authority: false;
}

export interface StrategyCatalogErrorPayload {
  detail: string;
  code?: string;
}
