"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import type { BotInstance, BotSpec } from "@/lib/contracts";

export function BotRevisionForm({
  botId,
  spec,
  allowed,
}: {
  botId: string;
  spec: BotSpec;
  allowed: boolean;
}) {
  const router = useRouter();
  const [currentSpec, setCurrentSpec] = useState(spec);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!allowed) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const pairUniverse = String(form.get("pair_universe") ?? "")
      .split(",")
      .map((pair) => pair.trim())
      .filter(Boolean);
    const nextSpec: BotSpec = {
      tenant_id: currentSpec.tenant_id,
      strategy_version: String(form.get("strategy_version")),
      model_version: String(form.get("model_version")),
      risk_policy_version: String(form.get("risk_policy_version")),
      exchange_connection_ref: String(form.get("exchange_connection_ref")),
      pair_universe: pairUniverse,
      timeframe: String(form.get("timeframe")),
      capital_allocation: String(form.get("capital_allocation")),
      capital_currency: String(form.get("capital_currency")),
      runtime_version: String(form.get("runtime_version")),
      config_revision: currentSpec.config_revision + 1,
      environment: currentSpec.environment,
      execution_mode: currentSpec.execution_mode,
    };

    const confirmed = window.confirm(
      `Create immutable revision ${nextSpec.config_revision} for ${botId}? Revision ${currentSpec.config_revision} will remain unchanged in history.`,
    );
    if (!confirmed) return;

    setSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      const response = await fetch(`/api/bots/${encodeURIComponent(botId)}/revisions`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ spec: nextSpec }),
      });
      const payload = (await response.json()) as Partial<BotInstance> & { detail?: string };
      if (!response.ok || !payload.spec) {
        throw new Error(payload.detail ?? `Revision creation failed with status ${response.status}`);
      }
      const idempotent = response.headers.get("x-idempotent-replay") === "true";
      setCurrentSpec(payload.spec);
      setMessage(
        idempotent
          ? `Revision ${payload.spec.config_revision} already exists with the same immutable content.`
          : `Immutable revision ${payload.spec.config_revision} created and attributed to the bot.`,
      );
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Revision creation failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (!allowed) {
    return (
      <article className="panel surface-card">
        <div className="panel-heading"><div><span className="eyebrow">Configuration</span><h2>Immutable revision</h2></div></div>
        <div className="status-banner status-error">
          <strong>Permission denied</strong>
          <span>This actor does not have the existing bot.create capability required to create a new immutable revision.</span>
        </div>
      </article>
    );
  }

  return (
    <article className="panel surface-card">
      <div className="panel-heading">
        <div><span className="eyebrow">Configuration</span><h2>Create immutable revision</h2></div>
      </div>
      <form className="bot-form" onSubmit={submit}>
        <div className="form-safety">
          <strong>Next revision: {currentSpec.config_revision + 1}</strong>
          <span>Environment and execution mode remain fixed at {currentSpec.environment} / {currentSpec.execution_mode}. Existing revisions are never edited.</span>
        </div>
        <div className="form-grid">
          <label>Strategy version<input name="strategy_version" defaultValue={currentSpec.strategy_version} required /></label>
          <label>Model version<input name="model_version" defaultValue={currentSpec.model_version} required /></label>
          <label>Risk policy<input name="risk_policy_version" defaultValue={currentSpec.risk_policy_version} required /></label>
          <label>Exchange connection ref<input name="exchange_connection_ref" defaultValue={currentSpec.exchange_connection_ref} required /></label>
          <label>Markets<input name="pair_universe" defaultValue={currentSpec.pair_universe.join(", ")} required /></label>
          <label>Timeframe<input name="timeframe" defaultValue={currentSpec.timeframe} required /></label>
          <label>Capital allocation<input name="capital_allocation" type="number" min="0.00000001" step="any" defaultValue={currentSpec.capital_allocation} required /></label>
          <label>Capital currency<input name="capital_currency" defaultValue={currentSpec.capital_currency} required /></label>
          <label>Runtime version<input name="runtime_version" defaultValue={currentSpec.runtime_version} required /></label>
        </div>
        <button className="primary-button" disabled={submitting} type="submit">
          {submitting ? "Creating revision…" : `Create revision ${currentSpec.config_revision + 1}`}
        </button>
        {message ? <p className="success-message" role="status">{message}</p> : null}
        {error ? <p className="error-message" role="alert">{error}</p> : null}
      </form>
    </article>
  );
}
