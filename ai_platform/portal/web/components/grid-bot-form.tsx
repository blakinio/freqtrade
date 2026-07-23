"use client";

import { FormEvent, useMemo, useState } from "react";

import type { BotInstance } from "@/lib/contracts";
import type { CreateGridBotConfigRequest } from "@/lib/product-contracts";

export function GridBotForm({ bots }: { bots: BotInstance[] }) {
  const eligibleBots = useMemo(
    () => bots.filter(
      (bot) => bot.spec.execution_mode === "dry_run" && bot.spec.strategy_version === "grid-dry-run-v1",
    ),
    [bots],
  );
  const [selectedBotId, setSelectedBotId] = useState(eligibleBots[0]?.bot_id ?? "");
  const selectedBot = eligibleBots.find((bot) => bot.bot_id === selectedBotId) ?? eligibleBots[0];
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    setError(null);
    const form = new FormData(event.currentTarget);
    const request: CreateGridBotConfigRequest = {
      bot_id: String(form.get("bot_id")),
      pair: String(form.get("pair")),
      lower_price: String(form.get("lower_price")),
      upper_price: String(form.get("upper_price")),
      levels: Number(form.get("levels")),
      quote_allocation: String(form.get("quote_allocation")),
    };

    try {
      const response = await fetch("/api/grid-bots", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
      });
      const payload = (await response.json()) as { grid_config_id?: string; detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail ?? `Grid configuration failed with status ${response.status}`);
      }
      setMessage(`Dry-run grid configuration recorded (${payload.grid_config_id ?? "new config"}).`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Grid configuration failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (eligibleBots.length === 0) {
    return (
      <div className="empty-state">
        <strong>No eligible grid dry-run bot</strong>
        <span>Create a dry-run bot pinned to strategy_version grid-dry-run-v1 before adding grid parameters.</span>
      </div>
    );
  }

  return (
    <form className="bot-form" onSubmit={submit}>
      <div className="form-safety">
        <strong>Dry-run only</strong>
        <span>This configuration cannot switch execution mode, submit live orders, or bypass the private runtime adapter.</span>
      </div>
      <div className="form-grid">
        <label>Bot<select name="bot_id" value={selectedBotId} onChange={(event) => setSelectedBotId(event.target.value)}>{eligibleBots.map((bot) => <option key={bot.bot_id} value={bot.bot_id}>{bot.name} · {bot.bot_id}</option>)}</select></label>
        <label>Pair<select name="pair" key={selectedBotId} defaultValue={selectedBot?.spec.pair_universe[0]}>{selectedBot?.spec.pair_universe.map((pair) => <option key={pair} value={pair}>{pair}</option>)}</select></label>
        <label>Lower price<input name="lower_price" type="number" min="0.00000001" step="any" defaultValue="90000" required /></label>
        <label>Upper price<input name="upper_price" type="number" min="0.00000001" step="any" defaultValue="110000" required /></label>
        <label>Levels<input name="levels" type="number" min="2" max="200" defaultValue="10" required /></label>
        <label>Quote allocation<input name="quote_allocation" type="number" min="0.01" step="0.01" defaultValue="1000" required /></label>
      </div>
      <button className="primary-button" type="submit" disabled={submitting}>{submitting ? "Saving…" : "Save dry-run grid config"}</button>
      {message ? <p className="success-message" role="status">{message}</p> : null}
      {error ? <p className="error-message" role="alert">{error}</p> : null}
    </form>
  );
}
