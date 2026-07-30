import "server-only";

import type { NextRequest } from "next/server";

import { forwardControlPlaneMutation } from "./identity";
import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "./portal-api";
import type {
  PublicContractProvenance,
  StrategyApprovalRecord,
  StrategyCatalogDetail,
  StrategyCatalogEntry,
  StrategyCatalogListResponse,
  StrategyDeploymentRecord,
  StrategyRollbackRequest,
  StrategyRollbackResult,
  StrategyVersionHistoryEntry,
} from "./strategy-catalog-contracts";

export type StrategyCatalogFixtureView = "default" | "empty" | "stale" | "failure";

const TENANT_ID = "tenant-demo";
const GENERATED_AT = "2026-07-30T18:00:00Z";

function provenance(artifactId: string, createdAt: string): PublicContractProvenance {
  return {
    contract_version: "v2",
    producer: "portal-strategy-catalog-fixture",
    artifact_id: artifactId,
    created_at: createdAt,
    source_refs: [`strategy-catalog:${artifactId}`],
    metadata: { evidence_scope: "repository_fixture", secrets_exposed: false },
  };
}

const fixtureEntries: StrategyCatalogEntry[] = [
  {
    strategy_version: "ai-directional-v3",
    display_name: "AI Directional",
    description:
      "Immutable directional research strategy approved for deterministic dry-run and shadow evaluation.",
    kind: "DIRECTIONAL",
    allowed_execution_modes: ["simulated", "dry_run"],
    runtime_status: "BOT_REFERENCE",
    immutable: true,
    lifecycle_state: "SHADOW",
    current_revision: 3,
    approval_required: true,
    required_capabilities: [
      "strategy.read",
      "strategy.approve",
      "strategy.deploy_dry_run",
      "strategy.rollback_dry_run",
    ],
    provenance_ref: "prov-ai-directional-v3",
  },
  {
    strategy_version: "grid-dry-run-v2",
    display_name: "Grid Dry Run",
    description:
      "Portal-managed grid configuration retained in review pending state until approval evidence exists.",
    kind: "GRID",
    allowed_execution_modes: ["dry_run"],
    runtime_status: "PORTAL_CONFIG_ONLY",
    immutable: true,
    lifecycle_state: "REVIEW_PENDING",
    current_revision: 2,
    approval_required: true,
    required_capabilities: ["strategy.read", "strategy.approve"],
    provenance_ref: "prov-grid-dry-run-v2",
  },
];

const directionalHistory: StrategyVersionHistoryEntry[] = [
  {
    contract_version: "v2",
    tenant_id: TENANT_ID,
    strategy_version: "ai-directional-v1",
    revision: 1,
    lifecycle_state: "ROLLED_BACK",
    immutable_hash: "1".repeat(64),
    created_by_actor_id: "actor-researcher",
    created_at: "2026-07-21T09:00:00Z",
    provenance: provenance("prov-ai-directional-v1", "2026-07-21T09:00:00Z"),
  },
  {
    contract_version: "v2",
    tenant_id: TENANT_ID,
    strategy_version: "ai-directional-v2",
    revision: 2,
    lifecycle_state: "DRY_RUN",
    immutable_hash: "2".repeat(64),
    created_by_actor_id: "actor-researcher",
    created_at: "2026-07-24T10:30:00Z",
    provenance: provenance("prov-ai-directional-v2", "2026-07-24T10:30:00Z"),
  },
  {
    contract_version: "v2",
    tenant_id: TENANT_ID,
    strategy_version: "ai-directional-v3",
    revision: 3,
    lifecycle_state: "SHADOW",
    immutable_hash: "3".repeat(64),
    created_by_actor_id: "actor-researcher",
    created_at: "2026-07-28T13:15:00Z",
    provenance: provenance("prov-ai-directional-v3", "2026-07-28T13:15:00Z"),
  },
];

const directionalApprovals: StrategyApprovalRecord[] = [
  {
    contract_version: "v2",
    tenant_id: TENANT_ID,
    strategy_version: "ai-directional-v3",
    approval_id: "approval-ai-directional-v3",
    decision: "APPROVED",
    required_capability: "strategy.approve",
    decided_by_actor_id: "actor-reviewer",
    decided_at: "2026-07-28T14:00:00Z",
    reason_codes: ["OOS_EVIDENCE_ACCEPTED", "DRY_RUN_ONLY"],
    provenance: provenance("approval-ai-directional-v3", "2026-07-28T14:00:00Z"),
  },
];

const directionalDeployments: StrategyDeploymentRecord[] = [
  {
    contract_version: "v2",
    tenant_id: TENANT_ID,
    deployment_id: "deployment-ai-directional-v2-dry-run",
    strategy_version: "ai-directional-v2",
    environment: "test",
    mode: "DRY_RUN",
    state: "ROLLED_BACK",
    deployed_by_actor_id: "actor-operator",
    deployed_at: "2026-07-25T08:00:00Z",
    provenance: provenance("deployment-ai-directional-v2-dry-run", "2026-07-25T08:00:00Z"),
    live_capital_authority: false,
  },
  {
    contract_version: "v2",
    tenant_id: TENANT_ID,
    deployment_id: "deployment-ai-directional-v3-shadow",
    strategy_version: "ai-directional-v3",
    environment: "test",
    mode: "SHADOW",
    state: "ACTIVE",
    deployed_by_actor_id: "actor-operator",
    deployed_at: "2026-07-29T07:45:00Z",
    provenance: provenance("deployment-ai-directional-v3-shadow", "2026-07-29T07:45:00Z"),
    live_capital_authority: false,
  },
];

const fixtureDetails: Record<string, StrategyCatalogDetail> = {
  "ai-directional-v3": {
    contract_version: "v2",
    tenant_id: TENANT_ID,
    entry: fixtureEntries[0],
    history: directionalHistory,
    approvals: directionalApprovals,
    deployments: directionalDeployments,
    rollback_targets: ["ai-directional-v2", "ai-directional-v1"],
    provenance: provenance("catalog-detail-ai-directional-v3", GENERATED_AT),
    required_capabilities: fixtureEntries[0].required_capabilities,
  },
  "grid-dry-run-v2": {
    contract_version: "v2",
    tenant_id: TENANT_ID,
    entry: fixtureEntries[1],
    history: [
      {
        contract_version: "v2",
        tenant_id: TENANT_ID,
        strategy_version: "grid-dry-run-v1",
        revision: 1,
        lifecycle_state: "DRAFT",
        immutable_hash: "4".repeat(64),
        created_by_actor_id: "actor-researcher",
        created_at: "2026-07-22T11:00:00Z",
        provenance: provenance("prov-grid-dry-run-v1", "2026-07-22T11:00:00Z"),
      },
      {
        contract_version: "v2",
        tenant_id: TENANT_ID,
        strategy_version: "grid-dry-run-v2",
        revision: 2,
        lifecycle_state: "REVIEW_PENDING",
        immutable_hash: "5".repeat(64),
        created_by_actor_id: "actor-researcher",
        created_at: "2026-07-27T12:00:00Z",
        provenance: provenance("prov-grid-dry-run-v2", "2026-07-27T12:00:00Z"),
      },
    ],
    approvals: [
      {
        contract_version: "v2",
        tenant_id: TENANT_ID,
        strategy_version: "grid-dry-run-v2",
        approval_id: "approval-grid-dry-run-v2",
        decision: "PENDING",
        required_capability: "strategy.approve",
        decided_by_actor_id: null,
        decided_at: null,
        reason_codes: ["AWAITING_REVIEW"],
        provenance: provenance("approval-grid-dry-run-v2", "2026-07-27T12:05:00Z"),
      },
    ],
    deployments: [],
    rollback_targets: [],
    provenance: provenance("catalog-detail-grid-dry-run-v2", GENERATED_AT),
    required_capabilities: fixtureEntries[1].required_capabilities,
  },
};

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

function cookieHeaders(cookieHeader?: string | null): HeadersInit | undefined {
  return cookieHeader ? { cookie: cookieHeader } : undefined;
}

async function apiFetch<T>(path: string, cookieHeader?: string | null): Promise<T> {
  const response = await fetch(`${controlPlaneUrl()}${path}`, {
    cache: "no-store",
    redirect: "manual",
    headers: {
      accept: "application/json",
      ...cookieHeaders(cookieHeader),
    },
  });
  if (!response.ok) {
    throw new PortalApiResponseError(
      `Strategy Catalog API request failed with status ${response.status}`,
      response.status,
    );
  }
  return (await response.json()) as T;
}

export async function listStrategyCatalog(
  cookieHeader?: string | null,
  fixtureView: StrategyCatalogFixtureView = "default",
): Promise<StrategyCatalogListResponse> {
  if (dataMode() === "fixture") {
    if (fixtureView === "failure") {
      throw new PortalApiResponseError("Strategy Catalog fixture is unavailable", 503);
    }
    return {
      contract_version: "v2",
      tenant_id: TENANT_ID,
      generated_at: GENERATED_AT,
      stale: fixtureView === "stale",
      reason_codes: fixtureView === "stale" ? ["CATALOG_SNAPSHOT_STALE"] : [],
      entries: fixtureView === "empty" ? [] : structuredClone(fixtureEntries),
    };
  }
  return apiFetch<StrategyCatalogListResponse>("/v1/strategy-catalog", cookieHeader);
}

export async function getStrategyCatalogDetail(
  strategyVersion: string,
  cookieHeader?: string | null,
): Promise<StrategyCatalogDetail | null> {
  if (dataMode() === "fixture") {
    const detail = fixtureDetails[strategyVersion];
    return detail ? structuredClone(detail) : null;
  }
  try {
    return await apiFetch<StrategyCatalogDetail>(
      `/v1/strategy-catalog/${encodeURIComponent(strategyVersion)}`,
      cookieHeader,
    );
  } catch (error) {
    if (error instanceof PortalApiResponseError && error.status === 404) return null;
    throw error;
  }
}

export async function submitStrategyRollback(
  request: NextRequest,
  sourceStrategyVersion: string,
  command: StrategyRollbackRequest,
): Promise<StrategyRollbackResult> {
  if (dataMode() === "fixture") {
    const detail = fixtureDetails[sourceStrategyVersion];
    if (!detail) {
      throw new PortalApiResponseError("Strategy version was not found", 404);
    }
    if (!detail.rollback_targets.includes(command.to_strategy_version)) {
      throw new PortalApiResponseError("Rollback target is not available for this strategy", 409);
    }
    return {
      contract_version: "v2",
      tenant_id: TENANT_ID,
      source_strategy_version: sourceStrategyVersion,
      target_strategy_version: command.to_strategy_version,
      accepted: true,
      lifecycle_state: "ROLLED_BACK",
      reason_codes: ["ROLLBACK_ACCEPTED", "DRY_RUN_ONLY"],
      audit_evidence_ref: `audit:rollback:${command.idempotency_key}`,
      evidence_state: "RECORDED",
      execution_authority: false,
      live_capital_authority: false,
    };
  }
  return forwardControlPlaneMutation<StrategyRollbackResult>(
    request,
    `/v1/strategy-catalog/${encodeURIComponent(sourceStrategyVersion)}/rollback`,
    "POST",
    command,
  );
}
