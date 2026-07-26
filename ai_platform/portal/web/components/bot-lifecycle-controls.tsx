"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { BotDesiredState, BotObservedState } from "@/lib/contracts";
import type { BotMutationPermissions } from "@/lib/bot-operations";

type LifecycleState = Exclude<BotDesiredState, "CREATED">;

export function BotLifecycleControls({
  botId,
  desiredState,
  observedState,
  permissions,
}: {
  botId: string;
  desiredState: BotDesiredState;
  observedState: BotObservedState;
  permissions: BotMutationPermissions;
}) {
  const router = useRouter();
  const [currentDesiredState, setCurrentDesiredState] = useState(desiredState);
  const [pending, setPending] = useState<LifecycleState | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const actions: Array<{ state: LifecycleState; label: string; allowed: boolean }> = [
    { state: "RUNNING", label: "Start", allowed: permissions.start },
    { state: "PAUSED", label: "Pause", allowed: permissions.pause },
    { state: "STOPPED", label: "Stop", allowed: permissions.stop },
  ];

  async function requestState(nextState: LifecycleState) {
    const confirmed = window.confirm(
      `Request desired state ${nextState} for ${botId}? This changes runtime lifecycle intent only and does not submit trades.`,
    );
    if (!confirmed) return;

    setPending(nextState);
    setMessage(null);
    setError(null);
    try {
      const response = await fetch(
        `/api/bots/${encodeURIComponent(botId)}/desired-state`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            desired_state: nextState,
            expected_current_state: currentDesiredState,
          }),
        },
      );
      const payload = (await response.json()) as {
        desired_state?: BotDesiredState;
        detail?: string;
      };
      if (!response.ok || !payload.desired_state) {
        throw new Error(payload.detail ?? `Lifecycle request failed with status ${response.status}`);
      }
      const idempotent = response.headers.get("x-idempotent-replay") === "true";
      setCurrentDesiredState(payload.desired_state);
      setMessage(
        idempotent
          ? `${payload.desired_state} was already the current desired state.`
          : `${payload.desired_state} requested. Observed state remains independent until runtime reconciliation.`,
      );
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Lifecycle request failed");
    } finally {
      setPending(null);
    }
  }

  return (
    <article className="panel surface-card">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Runtime lifecycle</span>
          <h2>Desired-state controls</h2>
        </div>
      </div>
      <p className="freshness">
        Desired: <strong>{currentDesiredState}</strong> · Observed: <strong>{observedState}</strong>.
        Commands are capability-gated and audited; they never call an exchange order endpoint.
      </p>
      <div className="status-cluster" aria-label="Bot lifecycle actions">
        {actions.map((action) => (
          <button
            className={action.state === "STOPPED" ? "secondary-button" : "primary-button"}
            disabled={pending !== null || !action.allowed || currentDesiredState === action.state}
            key={action.state}
            onClick={() => requestState(action.state)}
            title={action.allowed ? undefined : `Missing bot.${action.label.toLowerCase()} permission`}
            type="button"
          >
            {pending === action.state ? `${action.label}ing…` : action.label}
          </button>
        ))}
      </div>
      {!permissions.start && !permissions.pause && !permissions.stop ? (
        <p className="error-message" role="status">Lifecycle controls are permission denied for this actor.</p>
      ) : null}
      {message ? <p className="success-message" role="status">{message}</p> : null}
      {error ? <p className="error-message" role="alert">{error}</p> : null}
    </article>
  );
}
