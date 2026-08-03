import "server-only";

import type { NextRequest } from "next/server";

import { authorizeLocalReadRequest } from "@/lib/local-read-authorization";

const marketEvidencePolicy = {
  tenantEnvironmentVariable: "PORTAL_MARKET_EVIDENCE_TENANT_ID",
  fixtureTenantId: "tenant-demo",
  authorizedRoles: ["analyst", "model_reviewer", "admin"],
  permissionDeniedCode: "MARKET_EVIDENCE_PERMISSION_DENIED",
  permissionDeniedMessage: "Market Evidence read permission is required",
} as const;

export async function authorizeMarketEvidenceRequest(request: NextRequest): Promise<void> {
  await authorizeLocalReadRequest(request, marketEvidencePolicy);
}
