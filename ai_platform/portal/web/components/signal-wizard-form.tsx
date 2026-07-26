"use client";

import { FormEvent, useMemo, useState } from "react";

import { csrfFetch } from "@/lib/client-fetch";
import type { BotInstance, TradeSide } from "@/lib/contracts";
import type { SubmitSignalRequest } from "@/lib/product-contracts";

export function SignalWizardForm({ bots }: { bots: BotInstance[] }) {
  const [selectedBotId, setSelectedBotId] = useState(bots[0]?.bot_id ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selectedBot = useMemo(
    () => bots.find((bot) => bot.bot_id === selectedBotId) ?? bots[0],
    [bots, selectedBotId],
  );

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setSubmitting(true);
    setMessage(null);
    setError(null);
    const form = new FormData(formElement);
    const request: SubmitSignalRequest = {
      bot_id: String(form.get("bot_id")),
      pair: String(form.get("pair")),
      side: String(form.get("side")) as TradeSide,
      timeframe: String(form.get("timeframe")),
      confidence: String(form.get("confidence")),
      rationale: String(form.get("rationale")),
    };

    try {
      const response = await csrfFetch("/api/signals", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
      });
      const payload = (await response.json()) as { signal_id?: string; detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail ?? `Signal submission failed with status ${response.status}`);
      }
      setMessage(
        `Signal evidence recorded (${payload.signal_id ?? "new signal"}). No execution was triggered.`,
      );
      formElement.reset();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Signal submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (bots.length === 0) {
    return (
      <div className="empty-state">
        <strong>No bots available</strong>
        <span>Create a tenant-scoped dry-run bot before recording advisory signal evidence.</span>
      </div>
    );
  }

  return (
    <form className="bot-form" onSubmit={submit}>
      <div className="form-safety">
        <strong>Advisory evidence only</strong>
        <span>
          Recording a signal does not create a TradeIntent, bypass risk controls, or submit an
          order.
        </span>
      </div>
      <div className="form-grid">
        <label>
          Bot
          <select
            name="bot_id"
            value={selectedBotId}
            onChange={(changeEvent) => setSelectedBotId(changeEvent.target.value)}
            required
          >
            {bots.map((bot) => (
              <option key={bot.bot_id} value={bot.bot_id}>
                {bot.name} · {bot.bot_id}
              </option>
            ))}
          </select>
        </label>
        <label>
          Pair
          <select
            name="pair"
            key={selectedBotId}
            defaultValue={selectedBot?.spec.pair_universe[0]}
            required
          >
            {selectedBot?.spec.pair_universe.map((pair) => (
              <option key={pair} value={pair}>
                {pair}
              </option>
            ))}
          </select>
        </label>
        <label>
          Side
          <select name="side" defaultValue="BUY">
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>
        </label>
        <label>
          Timeframe
          <input name="timeframe" value={selectedBot?.spec.timeframe ?? ""} readOnly />
        </label>
        <label>
          Confidence
          <input
            name="confidence"
            type="number"
            min="0"
            max="1"
            step="0.01"
            defaultValue="0.75"
            required
          />
        </label>
      </div>
      <label>
        Rationale
        <textarea
          name="rationale"
          defaultValue="Manual advisory signal recorded for review."
          required
        />
      </label>
      <button className="primary-button" type="submit" disabled={submitting}>
        {submitting ? "Recording…" : "Record advisory signal"}
      </button>
      {message ? (
        <p className="success-message" role="status">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="error-message" role="alert">
          {error}
        </p>
      ) : null}
    </form>
  );
}
