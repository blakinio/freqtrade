"use client";

import { useState } from "react";

import type {
  LifecycleAction,
  LifecycleIntentResult,
} from "@/lib/bot-command-contracts";
import type { BotMutationPermissions } from "@/lib/bot-operations";
import { csrfFetch } from "@/lib/client-fetch";
import type { BotDesiredState, BotObservedState } from "@/lib/contracts";

interface ActionDefinition {
  action: LifecycleAction;
  targetState: Exclude<BotDesiredState, "CREATED">;
  label: string;
  allowed: boolean;
}

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

  const actions: ActionDefinition[] = [
    {
      action: desiredState === "PAUSED" ? "RESUME" : "START",
      targetState: "RUNNING",
      label: desiredState === "PAUSED" ? "Resume" : "Start",
      allowed: permissions.start,
    },
    {
      action: "PAUSE_NEW_ENTRIES",
      targetState: "PAUSED",
      label: "Pause new entries",
      allowed: permissions.pause,
    },
    {
      action: "STOP_KEEP_POSITIONS",
      targetState: "STOPPED",
      label: "Stop and keep positions",
      allowed: permissions.stop,
    },
  ];

  async function requestAction(definition: ActionDefinition) {
    const confirmed = window.confirm(
      `Submit ${definition.action} intent for ${botId}? This persists an audited command only and does not execute it.`,
    );
    if (!confirmed) return;

    setPending(definition.action);
    setMessage(null);
    setError(null);
    try {
      const response = await csrfFetch("/api/bot-management/commands/lifecycle", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          bot_id: botId,
          action: definition.action,
          expected_config_revision: configRevision,
          idempotency_key: `portal:${botId}:${configRevision}:${definition.action}`,
        }),
      });
      const payload = (await response.json()) as LifecycleIntentResult & { detail?: string };
      if (!response.ok && !payload.status) {
        throw new Error(payload.detail ?? `Lifecycle intent failed with status ${response.status}`);
      }
      const reasons = payload.reason_codes.length > 0 ? ` · ${payload.reason_codes.join(", ")}` : "";
      setMessage(
        `${payload.status}${reasons} · Command persisted: ${payload.command_persisted ? "yes" : "no"} · Execution submitted: no.`,
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Lifecycle command intent failed closed");
    } finally {
      setPending(null);
    }
  }

  return (
    <article className="panel surface-card">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">BMW-02 · Runtime lifecycle</span>
          <h2>Audited command intents</h2>
        </div>
      </div>
      <p className="freshness">
        Desired: <strong>{desiredState}</strong> · Observed: <strong>{observedState}</strong> · Config revision: <strong>{configRevision}</strong>.
        Acceptance is not runtime success; PI-08 execution and reconciliation remain separate.
      </p>
      <div className="status-cluster" aria-label="Bot lifecycle actions">
        {actions.map((definition) => (
          <button
            className="primary-button"
            disabled={
              pending !== null ||
              !definition.allowed ||
              desiredState === definition.targetState
            }
            key={definition.action}
            onClick={() => requestAction(definition)}
            title={definition.allowed ? undefined : `Missing capability for ${definition.action}`}
            type="button"
          >
            {pending === definition.action ? "Submitting…" : definition.label}
          </button>
        ))}
      </div>
      {!permissions.start && !permissions.pause && !permissions.stop ? (
        <p className="error-message" role="status">
          Lifecycle command intents are permission denied for this actor.
        </p>
      ) : null}
      {message ? <p className="success-message" role="status">{message}</p> : null}
      {error ? <p className="error-message" role="alert">{error}</p> : null}
    </article>
  );
}
