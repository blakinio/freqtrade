import "server-only";

import type { BotRuntimeTruth } from "./runtime-generation-contracts";
import { listFixtureBots } from "./fixtures";
import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "./portal-api";

function fixtureRuntimeTruth(botId: string): BotRuntimeTruth | null {
  const bot = listFixtureBots().find((candidate) => candidate.bot_id === botId);
  if (!bot) return null;

  const revisionId = `fixture-revision:${bot.bot_id}:${bot.spec.config_revision}`;
  const generationId = `fixture-generation:${bot.bot_id}:${bot.spec.config_revision}`;
  const generation = {
    generation_id: generationId,
    generation_ordinal: 1,
    config_revision_id: revisionId,
    config_revision_number: bot.spec.config_revision,
    generation_spec_digest: "f".repeat(64),
  };

  return {
    bot: {
      ...bot,
      latest_authored_revision_id: revisionId,
      desired_revision_id: revisionId,
      desired_runtime_generation_id: generationId,
      observed_runtime_generation_id: generationId,
      state_version: 1,
    },
    revisions: [
      {
        revision_id: revisionId,
        revision: bot.spec.config_revision,
        state: "PROMOTED",
        revision_content_digest: null,
      },
    ],
    desired_generation: generation,
    observed_generation: generation,
    latest_rollout: null,
    pending_rollout: false,
  };
}

export async function getBotRuntimeTruth(
  botId: string,
  cookieHeader?: string | null,
): Promise<BotRuntimeTruth | null> {
  if (dataMode() === "fixture") return fixtureRuntimeTruth(botId);
  const value = process.env.PORTAL_CONTROL_PLANE_URL;
  if (!value) {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL is required in API mode");
  }
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL must use http or https");
  }
  const response = await fetch(
    `${url.toString().replace(/\/$/, "")}/v1/bots/${encodeURIComponent(botId)}/runtime-truth`,
    {
      cache: "no-store",
      headers: {
        accept: "application/json",
        ...(cookieHeader ? { cookie: cookieHeader } : {}),
      },
    },
  );
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new PortalApiResponseError(
      `Portal API request failed with status ${response.status}`,
      response.status,
    );
  }
  return (await response.json()) as BotRuntimeTruth;
}
