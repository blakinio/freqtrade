"use client";

import { FormEvent, useState } from "react";

import { csrfFetch } from "@/lib/client-fetch";
import type { CreateBotRequest, PortalEnvironment } from "@/lib/contracts";

const wizardSteps = [
  "Identity & template",
  "Exchange & market",
  "AI & risk",
  "Capital & runtime",
  "Review & deploy",
];

export function CreateBotForm({ environment }: { environment: PortalEnvironment }) {
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    setError(null);
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const pairs = String(form.get("pair_universe") ?? "")
      .split(",")
      .map((pair) => pair.trim())
      .filter(Boolean);

    const request: CreateBotRequest = {
      bot_id: String(form.get("bot_id")),
      name: String(form.get("name")),
      spec: {
        tenant_id: String(form.get("tenant_id")),
        strategy_version: String(form.get("strategy_version")),
        model_version: String(form.get("model_version")),
        risk_policy_version: String(form.get("risk_policy_version")),
        exchange_connection_ref: String(form.get("exchange_connection_ref")),
        pair_universe: pairs,
        timeframe: String(form.get("timeframe")),
        capital_allocation: String(form.get("capital_allocation")),
        capital_currency: String(form.get("capital_currency")),
        runtime_version: String(form.get("runtime_version")),
        config_revision: Number(form.get("config_revision")),
        environment,
        execution_mode: "dry_run",
      },
    };

    try {
      const response = await csrfFetch("/api/bots", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
      });
      const payload = (await response.json()) as { bot_id?: string; name?: string; detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail ?? `Create bot failed with status ${response.status}`);
      }
      setMessage(
        `Created ${payload.name ?? request.name} (${payload.bot_id ?? request.bot_id}) in dry-run mode.`,
      );
      formElement.reset();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Create bot failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="bot-form" onSubmit={submit}>
      <ol className="wizard-steps" aria-label="Create bot steps">
        {wizardSteps.map((step, index) => (
          <li key={step}><span>{index + 1}</span>{step}</li>
        ))}
      </ol>

      <fieldset className="form-step">
        <legend><span>1</span>Identity & template</legend>
        <p>Choose the portal resource identity and immutable strategy template reference.</p>
        <div className="form-grid">
          <label>Bot ID<input name="bot_id" defaultValue="bot-new-01" required /></label>
          <label>Name<input name="name" defaultValue="New Dry Run Bot" required /></label>
          <label>Tenant ID<input name="tenant_id" defaultValue="tenant-demo" required /></label>
          <label>Strategy version<input name="strategy_version" defaultValue="ai-directional-v1" required /></label>
        </div>
      </fieldset>

      <fieldset className="form-step">
        <legend><span>2</span>Exchange & market</legend>
        <p>Only an opaque connection reference reaches the browser. Exchange credentials stay behind the secret boundary.</p>
        <div className="form-grid">
          <label>Exchange connection ref<input name="exchange_connection_ref" defaultValue="exchange-simulated-kraken" required /></label>
          <label>Pairs<input name="pair_universe" defaultValue="BTC/USDT" required /></label>
          <label>Timeframe<input name="timeframe" defaultValue="5m" required /></label>
        </div>
      </fieldset>

      <fieldset className="form-step">
        <legend><span>3</span>AI & risk</legend>
        <p>The bot pins exact model and deterministic risk-policy versions. A model prediction never bypasses the risk layer.</p>
        <div className="form-grid">
          <label>Model version<input name="model_version" defaultValue="model-validated-2026-07" required /></label>
          <label>Risk policy<input name="risk_policy_version" defaultValue="risk-default-v1" required /></label>
        </div>
      </fieldset>

      <fieldset className="form-step">
        <legend><span>4</span>Capital & runtime</legend>
        <p>Current portal creation is constrained to dry-run. Unsupported DCA/exit-specific parameters are not fabricated by the UI.</p>
        <div className="form-grid">
          <label>Capital allocation<input name="capital_allocation" type="number" min="1" step="0.01" defaultValue="1000" required /></label>
          <label>Capital currency<input name="capital_currency" defaultValue="USDT" required /></label>
          <label>Runtime version<input name="runtime_version" defaultValue="freqtrade-2026.7" required /></label>
          <label>Config revision<input name="config_revision" type="number" min="1" defaultValue="1" required /></label>
        </div>
      </fieldset>

      <fieldset className="form-step review-step">
        <legend><span>5</span>Review & deploy</legend>
        <div className="form-safety">
          <strong>Execution mode: DRY RUN · Environment: {environment.toUpperCase()}</strong>
          <span>Creation records desired configuration only. Browser code does not contact a trading runtime, exchange or secret store.</span>
        </div>
        <p className="freshness">Submitting creates the canonical bot resource. Runtime reconciliation remains a private server-side operation.</p>
      </fieldset>

      <button className="primary-button" type="submit" disabled={submitting}>
        {submitting ? "Creating…" : "Create dry-run bot"}
      </button>
      {message ? <p className="success-message" role="status">{message}</p> : null}
      {error ? <p className="error-message" role="alert">{error}</p> : null}
    </form>
  );
}
