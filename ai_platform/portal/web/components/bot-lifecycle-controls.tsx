"use client";

import { useState } from "react";

import { csrfFetch } from "@/lib/client-fetch";
import type { BotMutationPermissions } from "@/lib/bot-operations";
import type {
  LifecycleAction,
  LifecycleIntentResult,
} from "@/lib/bot-command-contracts";
import type { BotDesiredState, BotObservedState } from "@/lib/contracts";

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
      allowed: permissions.start,
      inactive: desiredState === "RUNNING",
    },
    {
      action: "PAUSE_NEW_ENTRIES",
      label: "Pause",
      allowed: permissions.pause,
      inactive: desiredState === "PAUSED",
    },
    {
      action: "STOP_KEEP_POSITIONS",
      label: "Stop",
      allowed: permissions.stop,
      inactive: desiredState === "STOPPED",
    },
  ];

  async function requestAction(action: LifecycleAction) {
    const confirmed = window.confirm(
      `Record lifecycle command intent ${action} for ${botId}? This does not execute a runtime action or submit trades.`,
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
            expected_config_revision: configRevision,
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
          `Command intent ${payload.command_id} accepted and persisted. Desired and observed runtime state remain unchanged pending separate execution and reconciliation.`,
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
        Desired: <strong>{desiredState}</strong> · Observed: <strong>{observedState}</strong> · Config
        revision: <strong>{configRevision}</strong>. Commands are capability-gated and audited; this
        surface never calls a runtime or exchange endpoint.
      </p>
      <div className="status-cluster" aria-label="Bot lifecycle actions">
        {actions.map((action) => (
          <button
            className="primary-button"
            disabled={pending !== null || !action.allowed || action.inactive}
            key={action.action}
            onClick={() => requestAction(action.action)}
            title={action.allowed ? undefined : `Missing bot.${action.label.toLowerCase()} permission`}
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
