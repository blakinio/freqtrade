"use client";

import { FormEvent, useState } from "react";

import type { NotificationPreference } from "@/lib/product-contracts";

export function NotificationPreferencesForm({ preference }: { preference: NotificationPreference }) {
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    setError(null);
    const form = new FormData(event.currentTarget);
    const request = {
      in_app_enabled: form.get("in_app_enabled") === "on",
      signal_events: form.get("signal_events") === "on",
      risk_events: form.get("risk_events") === "on",
      execution_events: form.get("execution_events") === "on",
    };

    try {
      const response = await fetch("/api/notifications/preferences", {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
      });
      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail ?? `Preference update failed with status ${response.status}`);
      }
      setMessage("Notification preferences saved.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Preference update failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="bot-form" onSubmit={submit}>
      <div className="form-grid">
        <label><input name="in_app_enabled" type="checkbox" defaultChecked={preference.in_app_enabled} /> In-app notifications enabled</label>
        <label><input name="signal_events" type="checkbox" defaultChecked={preference.signal_events} /> Signal evidence</label>
        <label><input name="risk_events" type="checkbox" defaultChecked={preference.risk_events} /> Risk decisions</label>
        <label><input name="execution_events" type="checkbox" defaultChecked={preference.execution_events} /> My execution activity</label>
      </div>
      <button className="primary-button" type="submit" disabled={submitting}>{submitting ? "Saving…" : "Save preferences"}</button>
      {message ? <p className="success-message" role="status">{message}</p> : null}
      {error ? <p className="error-message" role="alert">{error}</p> : null}
    </form>
  );
}
