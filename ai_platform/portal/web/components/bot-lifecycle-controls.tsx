"use client";

import { useEffect, useState } from "react";

import { csrfFetch } from "@/lib/client-fetch";
import type { BotMutationPermissions } from "@/lib/bot-operations";
import type {
  LifecycleAction,
  LifecycleIntentResult,
} from "@/lib/bot-command-contracts";
import type { BotDesiredState, BotObservedState } from "@/lib/contracts";
import type {
  BotRuntimeTruth,
  RuntimeGenerationTruth,
} from "@/lib/runtime-generation-contracts";

export function BotLifecycleControls({
  botId,
  configRevision,
  desiredState,
  observedState,
  permissions,
}: {
  botId: string;
  configRevision: number;
  desiredState: BotDesiredState;
  observedState: BotObservedState;
  permissions: BotMutationPermissions;
}) {
  const [pending, setPending] = useState<LifecycleAction | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [runtimeTruth, setRuntimeTruth] = useState<BotRuntimeTruth | null>(null);
  const [runtimeTruthUnavailable, setRuntimeTruthUnavailable] = useState(false);

  useEffect(() => {
    let active = true;
    async function loadRuntimeTruth() {
      try {
        const response = await fetch(
          `/api/bots/${encodeURIComponent(botId)}/runtime-truth`,
          { cache: "no-store" },
        );
        if (!response.ok) {
          if (active) setRuntimeTruthUnavailable(true);
          return;
        }
        const payload = (await response.json()) as BotRuntimeTruth;
        if (active) {
          setRuntimeTruth(payload);
          setRuntimeTruthUnavailable(false);
        }
      } catch {
        if (active) setRuntimeTruthUnavailable(true);
      }
    }
    void loadRuntimeTruth();
    return () => {
      active = false;
    };
  }, [botId]);

  const revisions = runtimeTruth?.revisions ?? [];
  const latestSaved = revisions.reduce(
    (latest, revision) =>
      latest === null || revision.revision > latest.revision ? revision : latest,
    null as (typeof revisions)[number] | null,
  );
  const latestEligible = revisions.reduce(
    (latest, revision) =>
      revision.state === "PROMOTED" &&
      (latest === null || revision.revision > latest.revision)
        ? revision
        : latest,
    null as (typeof revisions)[number] | null,
  );
  const desiredGeneration = runtimeTruth?.desired_generation ?? null;
  const observedGeneration = runtimeTruth?.observed_generation ?? null;
  const rollout = runtimeTruth?.latest_rollout ?? null;

  function commandTarget(action: LifecycleAction): RuntimeGenerationTruth | null {
    return action === "START" || action === "RESUME"
      ? desiredGeneration
      : observedGeneration;
  }

  const startAction: LifecycleAction = desiredState === "PAUSED" ? "RESUME" : "START";
  const actions: Array<{
    action: LifecycleAction;
    label: string;
    allowed: boolean;
    inactive: boolean;
  }> = [
    {
      action: startAction,
      label: startAction === "RESUME" ? "Resume" : "Start",
      allowed: permissions.start && desiredGeneration !== null,
      inactive: desiredState === "RUNNING",
    },
    {
      action: "PAUSE_NEW_ENTRIES",
      label: "Pause",
      allowed: permissions.pause && observedGeneration !== null,
      inactive: desiredState === "PAUSED",
    },
    {
      action: "STOP_KEEP_POSITIONS",
      label: "Stop",
      allowed: permissions.stop && observedGeneration !== null,
      inactive: desiredState === "STOPPED",
    },
  ];

  async function requestAction(action: LifecycleAction) {
    const target = commandTarget(action);
    if (target === null) {
      setError(
        action === "START" || action === "RESUME"
          ? "No desired RuntimeGeneration is available. Promote and apply a revision first."
          : "No observed RuntimeGeneration is available for this lifecycle command.",
      );
      return;
    }
    const confirmed = window.confirm(
      `Record lifecycle command intent ${action} for ${botId} generation ${target.generation_id} (${target.managed_mode.toUpperCase()})? This does not execute a runtime action or submit trades.`,
    );
    if (!confirmed) return;

    setPending(action);
    setMessage(null);
    setError(null);
    try {
      const response = await csrfFetch(
        "/api/bot-management/commands/lifecycle-intents",
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            bot_id: botId,
            action,
            expected_config_revision: target.config_revision_number,
            expected_runtime_generation_id: target.generation_id,
            idempotency_key: crypto.randomUUID(),
          }),
        },
      );
      const payload = (await response.json()) as LifecycleIntentResult & { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail ?? `Lifecycle intent failed with status ${response.status}`);
      }
      if (payload.execution_submission_performed !== false) {
        throw new Error("Lifecycle intent response violated the no-execution boundary");
      }
      if (payload.status === "ACCEPTED" && payload.command_id) {
        setMessage(
          `Command intent ${payload.command_id} accepted for generation ${target.generation_id} (${target.managed_mode.toUpperCase()}). Desired and observed runtime state remain unchanged pending separate execution and reconciliation.`,
        );
      } else {
        const reasons = payload.reason_codes.join(", ") || "UNKNOWN";
        setError(`${payload.status}: ${reasons}. No runtime action was submitted.`);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Lifecycle intent failed closed");
    } finally {
      setPending(null);
    }
  }

  return (
    <article className="panel surface-card">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Runtime lifecycle</span>
          <h2>Command intent controls</h2>
        </div>
      </div>
      <p className="freshness">
        Desired lifecycle: <strong>{desiredState}</strong> · Observed lifecycle: <strong>{observedState}</strong>.
        Commands are capability-gated, generation-bound and audited; this surface never calls a runtime or exchange endpoint.
      </p>
      <dl className="definition-list">
        <div>
          <dt>Latest saved</dt>
          <dd>{latestSaved ? `R${latestSaved.revision} · ${latestSaved.state} · ${latestSaved.managed_mode.toUpperCase()}` : `R${configRevision} · truth unavailable`}</dd>
        </div>
        <div>
          <dt>Eligible</dt>
          <dd>{latestEligible ? `R${latestEligible.revision} · PROMOTED · ${latestEligible.managed_mode.toUpperCase()}` : "None"}</dd>
        </div>
        <div>
          <dt>Desired</dt>
          <dd>
            {desiredGeneration
              ? `R${desiredGeneration.config_revision_number} · G${desiredGeneration.generation_ordinal} · ${desiredGeneration.managed_mode.toUpperCase()} · ${desiredGeneration.generation_id}`
              : "No desired RuntimeGeneration"}
          </dd>
        </div>
        <div>
          <dt>Active</dt>
          <dd>
            {observedGeneration
              ? `R${observedGeneration.config_revision_number} · G${observedGeneration.generation_ordinal} · ${observedGeneration.managed_mode.toUpperCase()} · ${observedGeneration.generation_id}`
              : "No active runtime"}
          </dd>
        </div>
        <div>
          <dt>Pending rollout</dt>
          <dd>
            {runtimeTruthUnavailable
              ? "Unavailable"
              : runtimeTruth?.pending_rollout
                ? "Yes"
                : "No"}
          </dd>
        </div>
        <div>
          <dt>Rollout</dt>
          <dd>{rollout ? `${rollout.status}${rollout.reason_code ? ` · ${rollout.reason_code}` : ""}` : "None"}</dd>
        </div>
      </dl>
      <div className="status-cluster" aria-label="Bot lifecycle actions">
        {actions.map((action) => (
          <button
            className="primary-button"
            disabled={pending !== null || !action.allowed || action.inactive}
            key={action.action}
            onClick={() => requestAction(action.action)}
            title={
              action.allowed
                ? undefined
                : action.action === "START" || action.action === "RESUME"
                  ? "A PROMOTED revision must be explicitly applied before start or resume"
                  : "An observed RuntimeGeneration is required for pause or stop"
            }
            type="button"
          >
            {pending === action.action ? `${action.label}…` : action.label}
          </button>
        ))}
      </div>
      {!permissions.start && !permissions.pause && !permissions.stop ? (
        <p className="error-message" role="status">
          Lifecycle controls are permission denied for this actor.
        </p>
      ) : null}
      {message ? <p className="success-message" role="status">{message}</p> : null}
      {error ? <p className="error-message" role="alert">{error}</p> : null}
    </article>
  );
}
