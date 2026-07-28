import { createHash } from "node:crypto";

import { NextRequest, NextResponse } from "next/server";

import type {
  CreateBotConfigurationDraftRequest,
  FinalizedConfigurationSummary,
} from "@/lib/bot-management-contracts";
import {
  forwardControlPlaneMutation,
  identityErrorResponse,
  requireBrowserMutation,
} from "@/lib/identity";
import { dataMode } from "@/lib/portal-api";

interface DraftRevision {
  draft_id: string;
  tenant_id: string;
  bot_id: string;
  revision: number;
}

interface DraftPreview {
  draft_ref: {
    tenant_id: string;
    draft_id: string;
    revision: number;
  };
  status: "INCOMPLETE" | "INVALID" | "INCOMPATIBLE" | "READY";
  missing_fields?: string[];
  validation_errors?: string[];
  compatibility_decision?: { status: "COMPATIBLE" | "REJECTED" } | null;
}

interface FinalizedConfiguration {
  draft_ref: DraftPreview["draft_ref"];
  configuration: {
    configuration_id: string;
    bot_id: string;
    revision: number;
    execution_mode: "dry_run";
  };
  compatibility_decision: { status: "COMPATIBLE" };
  configuration_sha256: string;
}

function isRequest(value: unknown): value is CreateBotConfigurationDraftRequest {
  if (typeof value !== "object" || value === null) return false;
  const request = value as Partial<CreateBotConfigurationDraftRequest>;
  return (
    typeof request.draft_id === "string" &&
    request.draft_id.trim().length > 0 &&
    typeof request.bot_id === "string" &&
    request.bot_id.trim().length > 0 &&
    typeof request.payload === "object" &&
    request.payload !== null &&
    request.payload.execution_mode === "dry_run" &&
    request.payload.runtime_policy?.execution_mode === "dry_run"
  );
}

function fixtureSummary(request: CreateBotConfigurationDraftRequest): FinalizedConfigurationSummary {
  const canonical = JSON.stringify(request);
  return {
    draft_id: request.draft_id,
    configuration_id: `fixture-config:${request.bot_id}:1`,
    bot_id: request.bot_id,
    revision: 1,
    configuration_sha256: createHash("sha256").update(canonical).digest("hex"),
    compatibility_status: "COMPATIBLE",
    execution_mode: "dry_run",
    runtime_submission_performed: false,
  };
}

function summary(finalized: FinalizedConfiguration): FinalizedConfigurationSummary {
  return {
    draft_id: finalized.draft_ref.draft_id,
    configuration_id: finalized.configuration.configuration_id,
    bot_id: finalized.configuration.bot_id,
    revision: finalized.configuration.revision,
    configuration_sha256: finalized.configuration_sha256,
    compatibility_status: finalized.compatibility_decision.status,
    execution_mode: finalized.configuration.execution_mode,
    runtime_submission_performed: false,
  };
}

export async function POST(request: NextRequest) {
  try {
    requireBrowserMutation(request);
    const payload: unknown = await request.json();
    if (!isRequest(payload)) {
      return NextResponse.json(
        { detail: "Request must match the canonical dry-run bot builder contract" },
        { status: 422, headers: { "cache-control": "no-store" } },
      );
    }

    if (dataMode() === "fixture") {
      return NextResponse.json(fixtureSummary(payload), {
        status: 201,
        headers: { "cache-control": "no-store" },
      });
    }

    const draft = await forwardControlPlaneMutation<DraftRevision>(
      request,
      "/v1/bot-management/builder/drafts",
      "POST",
      payload,
    );
    const draftRef = {
      tenant_id: draft.tenant_id,
      draft_id: draft.draft_id,
      revision: draft.revision,
    };
    const preview = await forwardControlPlaneMutation<DraftPreview>(
      request,
      "/v1/bot-management/builder/drafts/preview",
      "POST",
      draftRef,
    );
    if (preview.status !== "READY") {
      return NextResponse.json(
        {
          detail: "Bot configuration is not ready for finalization",
          preview,
        },
        { status: 422, headers: { "cache-control": "no-store" } },
      );
    }
    const finalized = await forwardControlPlaneMutation<FinalizedConfiguration>(
      request,
      "/v1/bot-management/builder/drafts/finalize",
      "POST",
      { draft_ref: draftRef, expected_configuration_revision: null },
    );
    return NextResponse.json(summary(finalized), {
      status: 201,
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    const identityResponse = identityErrorResponse(error);
    if (identityResponse) return identityResponse;
    return NextResponse.json(
      { detail: "Bot builder request failed closed" },
      { status: 502, headers: { "cache-control": "no-store" } },
    );
  }
}
