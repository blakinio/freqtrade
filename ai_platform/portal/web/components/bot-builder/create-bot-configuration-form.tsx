"use client";

import { FormEvent, useState } from "react";

import type {
  BotCatalogSnapshot,
  BotConfigurationDraftPayload,
  CreateBotConfigurationDraftRequest,
  FinalizedConfigurationSummary,
} from "@/lib/bot-management-contracts";
import { csrfFetch } from "@/lib/client-fetch";
import type { PortalEnvironment } from "@/lib/contracts";

const wizardSteps = [
  "Approved template",
  "Market policy",
  "Sizing & entry",
  "Runtime policy",
  "Review & finalize",
];

interface Props {
  catalog: BotCatalogSnapshot;
  environment: PortalEnvironment;
}

function sortedPairs(raw: string): string[] {
  return [...new Set(raw.split(",").map((pair) => pair.trim()).filter(Boolean))].sort();
}

function policyId(botId: string, family: string): string {
  return `${botId}:${family}:1`;
}

export function CreateBotConfigurationForm({ catalog, environment }: Props) {
  const activeTemplates = catalog.templates.filter((entry) => entry.state === "ACTIVE");
  const activeStrategies = catalog.strategies.filter((entry) => entry.state === "ACTIVE");
  const activeModels = catalog.models.filter((entry) => entry.state === "ACTIVE");
  const activeProfiles = catalog.exchange_profiles.filter((entry) => entry.state === "ACTIVE");
  const activeRuntimes = catalog.runtimes.filter((entry) => entry.state === "ACTIVE");
  const activeRiskPolicies = catalog.risk_policies.filter((entry) => entry.state === "ACTIVE");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<FinalizedConfigurationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const available =
    activeTemplates.length > 0 &&
    activeStrategies.length > 0 &&
    activeModels.length > 0 &&
    activeProfiles.length > 0 &&
    activeRuntimes.length > 0 &&
    activeRiskPolicies.length > 0;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setResult(null);
    setError(null);

    const form = new FormData(event.currentTarget);
    const botId = String(form.get("bot_id") ?? "").trim();
    const template = activeTemplates.find(
      (entry) => entry.template.template_id === String(form.get("template_id")),
    );
    const strategyVersion = String(form.get("strategy_version") ?? "");
    const modelVersion = String(form.get("model_version") ?? "");
    const exchangeProfileVersion = String(form.get("exchange_profile_version") ?? "");
    const runtimeVersion = String(form.get("runtime_version") ?? "");
    const riskPolicyVersion = String(form.get("risk_policy_version") ?? "");
    const pairs = sortedPairs(String(form.get("pairs") ?? ""));
    const timeframe = String(form.get("timeframe") ?? "").trim();
    const fixedQuoteAmount = String(form.get("fixed_quote_amount") ?? "").trim();
    const maxConcurrentPositions = Number(form.get("max_concurrent_positions"));
    const cooldownSeconds = Number(form.get("cooldown_seconds"));

    if (!template || pairs.length === 0) {
      setError("Select an approved template and at least one market pair.");
      setSubmitting(false);
      return;
    }

    const payload: BotConfigurationDraftPayload = {
      catalog_ref: { catalog_id: catalog.catalog_id, version: String(catalog.revision) },
      template_ref: {
        catalog_id: template.template.template_id,
        version: String(template.template.revision),
      },
      strategy_version: strategyVersion,
      model_version: modelVersion,
      exchange_connection_ref: "simulated-dry-run",
      exchange_profile_version: exchangeProfileVersion,
      market_policy: {
        policy_id: policyId(botId, "market"),
        revision: 1,
        pairs,
        market_type: "spot",
        direction: "long",
        timeframe,
        margin_mode: null,
        leverage: null,
      },
      entry_policy: {
        policy_id: policyId(botId, "entry"),
        revision: 1,
        order_type: "market",
        limit_offset_percent: null,
        cooldown_seconds: cooldownSeconds,
        duplicate_signal_behavior: "reject",
        max_concurrent_positions: maxConcurrentPositions,
      },
      position_sizing_policy: {
        policy_id: policyId(botId, "sizing"),
        revision: 1,
        mode: "fixed_quote_amount",
        fixed_base_quantity: null,
        fixed_quote_amount: fixedQuoteAmount,
        quote_allocation_percent: null,
        max_per_pair_allocation_percent: "100",
        max_total_allocation_percent: "100",
      },
      dca_policy: null,
      exit_policy: {
        policy_id: policyId(botId, "exit"),
        revision: 1,
        take_profit: null,
        stop_loss: null,
        break_even: null,
        trailing_stop: null,
        time_exit_seconds: null,
        strategy_exit_enabled: true,
      },
      risk_policy_version: riskPolicyVersion,
      signal_policy: null,
      grid_policy: null,
      runtime_policy: {
        policy_id: policyId(botId, "runtime"),
        revision: 1,
        runtime_version: runtimeVersion,
        execution_mode: "dry_run",
        heartbeat_timeout_seconds: 60,
        command_timeout_seconds: 15,
        reconciliation_timeout_seconds: 60,
        restart_policy: "never",
        max_restart_attempts: 0,
      },
      environment,
      execution_mode: "dry_run",
    };
    const request: CreateBotConfigurationDraftRequest = {
      draft_id: crypto.randomUUID(),
      bot_id: botId,
      payload,
    };

    try {
      const response = await csrfFetch("/api/bot-management/builder", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
      });
      const responsePayload = (await response.json()) as FinalizedConfigurationSummary & {
        detail?: string;
      };
      if (!response.ok) {
        throw new Error(responsePayload.detail ?? `Builder failed with status ${response.status}`);
      }
      setResult(responsePayload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Bot configuration failed closed");
    } finally {
      setSubmitting(false);
    }
  }

  if (!available) {
    return (
      <div className="empty-state" role="status">
        <strong>Approved catalog is incomplete</strong>
        <span>The builder remains unavailable until all required server-owned catalog entries exist.</span>
      </div>
    );
  }

  return (
    <form className="bot-form" onSubmit={submit}>
      <ol className="wizard-steps" aria-label="Bot configuration steps">
        {wizardSteps.map((step, index) => (
          <li key={step}>
            <span>{index + 1}</span>
            {step}
          </li>
        ))}
      </ol>

      <fieldset className="form-step">
        <legend><span>1</span>Approved template</legend>
        <p>Every internal version is selected from catalog revision {catalog.revision}.</p>
        <div className="form-grid">
          <label>Bot ID<input name="bot_id" defaultValue="bot-new-dry-run" required /></label>
          <label>Template<select name="template_id" required>{activeTemplates.map((entry) => (
            <option key={entry.template.template_id} value={entry.template.template_id}>
              {entry.template.display_name} · r{entry.template.revision}
            </option>
          ))}</select></label>
          <label>Strategy<select name="strategy_version" required>{activeStrategies.map((entry) => (
            <option key={entry.version} value={entry.version}>{entry.version}</option>
          ))}</select></label>
          <label>Model<select name="model_version" required>{activeModels.map((entry) => (
            <option key={entry.version} value={entry.version}>{entry.version}</option>
          ))}</select></label>
        </div>
      </fieldset>

      <fieldset className="form-step">
        <legend><span>2</span>Market policy</legend>
        <p>Spot-long only. The simulated connection is an opaque dry-run reference and contains no credential.</p>
        <div className="form-grid">
          <label>Exchange profile<select name="exchange_profile_version" required>{activeProfiles.map((entry) => (
            <option key={entry.version} value={entry.version}>
              {entry.profile.exchange_id} · {entry.version}
            </option>
          ))}</select></label>
          <label>Pairs<input name="pairs" defaultValue="BTC/USDT" required /></label>
          <label>Timeframe<input name="timeframe" defaultValue="5m" required /></label>
          <label>Direction<input value="long" readOnly aria-label="Direction" /></label>
        </div>
      </fieldset>

      <fieldset className="form-step">
        <legend><span>3</span>Sizing & entry</legend>
        <div className="form-grid">
          <label>Fixed quote amount<input name="fixed_quote_amount" type="number" min="1" step="0.01" defaultValue="1000" required /></label>
          <label>Maximum positions<input name="max_concurrent_positions" type="number" min="1" defaultValue="1" required /></label>
          <label>Entry cooldown seconds<input name="cooldown_seconds" type="number" min="0" defaultValue="0" required /></label>
          <label>Order type<input value="market" readOnly aria-label="Order type" /></label>
        </div>
      </fieldset>

      <fieldset className="form-step">
        <legend><span>4</span>Runtime policy</legend>
        <div className="form-grid">
          <label>Runtime<select name="runtime_version" required>{activeRuntimes.map((entry) => (
            <option key={entry.version} value={entry.version}>{entry.version}</option>
          ))}</select></label>
          <label>Risk policy<select name="risk_policy_version" required>{activeRiskPolicies.map((entry) => (
            <option key={entry.version} value={entry.version}>{entry.version}</option>
          ))}</select></label>
          <label>Environment<input value={environment} readOnly aria-label="Environment" /></label>
          <label>Execution mode<input value="dry_run" readOnly aria-label="Execution mode" /></label>
        </div>
      </fieldset>

      <fieldset className="form-step review-step">
        <legend><span>5</span>Review & finalize</legend>
        <div className="form-safety">
          <strong>Configuration finalization only</strong>
          <span>The server validates compatibility and stores an immutable revision. It does not submit to Freqtrade or start a runtime.</span>
        </div>
      </fieldset>

      <button className="primary-button" type="submit" disabled={submitting}>
        {submitting ? "Validating…" : "Finalize dry-run configuration"}
      </button>
      {result ? (
        <div className="success-message" role="status">
          <strong>Configuration {result.configuration_id} · revision {result.revision}</strong>
          <span>SHA-256: {result.configuration_sha256}</span>
          <span>Runtime submitted: {result.runtime_submission_performed ? "yes" : "no"}</span>
        </div>
      ) : null}
      {error ? <p className="error-message" role="alert">{error}</p> : null}
    </form>
  );
}
