"use client";

import { FormEvent, useMemo, useState } from "react";

import { csrfFetch } from "@/lib/client-fetch";
import type { BotInstance, TerminalIntentResult } from "@/lib/contracts";

export function TerminalForm({ bots }: { bots: BotInstance[] }) {
  const [selectedBotId, setSelectedBotId] = useState(bots[0]?.bot_id ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<TerminalIntentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selectedBot = useMemo(
    () => bots.find((bot) => bot.bot_id === selectedBotId) ?? bots[0],
    [bots, selectedBotId],
  );

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setResult(null);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      const response = await csrfFetch("/api/terminal", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          bot_id: String(form.get("bot_id")),
          pair: String(form.get("pair")),
          side: String(form.get("side")),
          amount: String(form.get("amount")),
        }),
      });
      const payload = (await response.json()) as TerminalIntentResult & { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail ?? `Terminal request failed with status ${response.status}`);
      }
      setResult(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Terminal request failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (bots.length === 0 || !selectedBot) {
    return <div className="empty-state"><strong>No eligible bots</strong><span>Create a dry-run bot first.</span></div>;
  }

  return (
    <form className="bot-form" onSubmit={submit}>
      <div className="form-grid">
        <label>
          Bot
          <select name="bot_id" value={selectedBot.bot_id} onChange={(event) => setSelectedBotId(event.target.value)}>
            {bots.map((bot) => <option key={bot.bot_id} value={bot.bot_id}>{bot.name}</option>)}
          </select>
        </label>
        <label>
          Pair
          <select name="pair" defaultValue={selectedBot.spec.pair_universe[0]} key={selectedBot.bot_id}>
            {selectedBot.spec.pair_universe.map((pair) => <option key={pair} value={pair}>{pair}</option>)}
          </select>
        </label>
        <label>Side<select name="side" defaultValue="BUY"><option value="BUY">BUY</option><option value="SELL">SELL</option></select></label>
        <label>Amount<input name="amount" type="number" min="0.00000001" step="0.00000001" defaultValue="0.01" required /></label>
      </div>
      <div className="form-safety">
        <strong>Deterministic risk gate required</strong>
        <span>Exposure, loss, drawdown and runtime-health inputs are resolved server-side. The browser cannot submit a risk snapshot.</span>
      </div>
      <button className="primary-button" type="submit" disabled={submitting}>
        {submitting ? "Evaluating…" : "Submit trade intent"}
      </button>
      {result ? (
        <div className="success-message" role="status">
          Risk: {result.risk_decision.decision} · Execution: {result.execution_state} · {result.execution_reason_code}
        </div>
      ) : null}
      {error ? <p className="error-message" role="alert">{error}</p> : null}
    </form>
  );
}
