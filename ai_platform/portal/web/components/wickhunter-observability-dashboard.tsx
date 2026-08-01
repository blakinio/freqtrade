"use client";

import { useCallback, useEffect, useState } from "react";

import type {
  WickHunterObservabilityView,
  WickHunterRuntimeHealth,
} from "@/lib/wickhunter-observability";

import styles from "./wickhunter-observability-dashboard.module.css";

const REFRESH_INTERVAL_MS = 15_000;

function statusClass(health: WickHunterRuntimeHealth, stale: boolean): string {
  if (stale || health === "fail_closed") return `${styles.badge} ${styles.bad}`;
  if (health === "degraded") return `${styles.badge} ${styles.warn}`;
  return `${styles.badge} ${styles.good}`;
}

function timestamp(value: number): string {
  return new Intl.DateTimeFormat("pl-PL", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "Europe/Warsaw",
  }).format(new Date(value));
}

function age(value: number | null): string {
  if (value === null) return "brak";
  if (value < 1_000) return `${value} ms`;
  if (value < 60_000) return `${Math.round(value / 1_000)} s`;
  return `${Math.round(value / 60_000)} min`;
}

function decimal(value: string, digits = 8): string {
  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? new Intl.NumberFormat("pl-PL", { maximumFractionDigits: digits }).format(parsed)
    : value;
}

function identity(value: string | null): string {
  return value ? `${value.slice(0, 12)}…${value.slice(-8)}` : "brak";
}

export function WickHunterObservabilityDashboard() {
  const [view, setView] = useState<WickHunterObservabilityView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/market/wickhunter", { cache: "no-store" });
      const payload = (await response.json()) as WickHunterObservabilityView | { error?: string };
      if (!response.ok || !("snapshot" in payload)) {
        throw new Error("error" in payload && payload.error ? payload.error : "Brak danych runtime");
      }
      setView(payload);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Nie udało się pobrać danych runtime");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const initialRefresh = window.setTimeout(() => {
      void refresh();
    }, 0);
    const interval = window.setInterval(() => {
      void refresh();
    }, REFRESH_INTERVAL_MS);
    return () => {
      window.clearTimeout(initialRefresh);
      window.clearInterval(interval);
    };
  }, [refresh]);

  if (!view && loading) {
    return <main className={styles.page}>Ładowanie obserwowalności WickHunter…</main>;
  }

  if (!view) {
    return (
      <main className={styles.page}>
        <h1 className={styles.title}>WickHunter Observability</h1>
        <div className={styles.error} role="alert">
          {error ?? "Snapshot runtime jest niedostępny."}
        </div>
        <button className={styles.button} type="button" onClick={() => void refresh()}>
          Ponów
        </button>
      </main>
    );
  }

  const { snapshot } = view;
  const riskRejections = snapshot.decisions.filter(
    (decision) => decision.status === "rejected_by_risk",
  ).length;

  return (
    <main className={styles.page} data-testid="wickhunter-observability">
      <section className={styles.hero}>
        <div>
          <h1 className={styles.title}>WickHunter Observability</h1>
          <p className={styles.subtitle}>
            Wyłącznie odczyt: runtime shadow/paper, symulowane pozycje i decyzje Risk Engine.
          </p>
        </div>
        <div className={styles.actions}>
          <span className={statusClass(snapshot.health, view.stale)} data-testid="runtime-health">
            {view.stale ? "STALE" : snapshot.health}
          </span>
          <button
            className={styles.button}
            type="button"
            disabled={loading}
            onClick={() => void refresh()}
          >
            {loading ? "Odświeżanie…" : "Odśwież"}
          </button>
        </div>
      </section>

      {error ? (
        <div className={styles.error} role="alert">
          Ostatnie odświeżenie nie powiodło się: {error}
        </div>
      ) : null}

      <section className={styles.grid} aria-label="Stan runtime">
        <article className={`${styles.panel} ${styles.metric}`}>
          <span className={styles.metricLabel}>Tryb</span>
          <strong className={styles.metricValue} data-testid="runtime-mode">
            {snapshot.mode}
          </strong>
        </article>
        <article className={`${styles.panel} ${styles.metric}`}>
          <span className={styles.metricLabel}>Snapshot</span>
          <strong className={styles.metricValue}>{timestamp(snapshot.observed_at_ms)}</strong>
          <span className={styles.muted}>wiek {age(view.snapshot_age_ms)}</span>
        </article>
        <article className={`${styles.panel} ${styles.metric}`}>
          <span className={styles.metricLabel}>Kapitał symulowany</span>
          <strong className={styles.metricValue}>
            {decimal(snapshot.simulated_equity_quote, 2)} quote
          </strong>
          <span className={styles.muted}>
            PnL: {decimal(snapshot.cumulative_realized_pnl_quote, 2)} /{" "}
            {decimal(snapshot.unrealized_pnl_quote, 2)}
          </span>
        </article>
        <article className={`${styles.panel} ${styles.metric}`}>
          <span className={styles.metricLabel}>Drawdown</span>
          <strong className={styles.metricValue}>
            {decimal(String(Number(snapshot.drawdown_ratio) * 100), 3)}%
          </strong>
        </article>
        <article className={`${styles.panel} ${styles.metric}`}>
          <span className={styles.metricLabel}>Circuit breaker</span>
          <strong className={styles.metricValue} data-testid="circuit-breaker">
            {snapshot.circuit_breaker_active ? "AKTYWNY" : "nieaktywny"}
          </strong>
          <span className={styles.muted}>
            {snapshot.circuit_breaker_reasons.join(", ") || "brak powodów blokady"}
          </span>
        </article>
        <article className={`${styles.panel} ${styles.metric}`}>
          <span className={styles.metricLabel}>Walidacja / retraining</span>
          <strong className={styles.metricValue}>{snapshot.validation_state}</strong>
          <span className={styles.muted}>{snapshot.retraining_state}</span>
        </article>
      </section>

      <section className={styles.panel}>
        <h2>Dynamiczny universe</h2>
        <ul className={styles.list} data-testid="dynamic-universe">
          {snapshot.dynamic_universe.map((symbol) => (
            <li className={styles.chip} key={symbol}>
              {symbol}
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.panel}>
        <h2>Świeżość źródeł</h2>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Źródło</th>
                <th>Stan</th>
                <th>Świeże</th>
                <th>Wiek</th>
                <th>Ostatni event</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.source_freshness.map((source) => (
                <tr key={source.source} data-testid={`source-${source.source}`}>
                  <td>{source.source}</td>
                  <td>{source.health}</td>
                  <td>{source.fresh ? "tak" : "nie"}</td>
                  <td>{age(source.age_ms)}</td>
                  <td>
                    {source.last_received_at_ms === null
                      ? "brak"
                      : timestamp(source.last_received_at_ms)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className={styles.grid} aria-label="Tożsamości artefaktów">
        <article className={`${styles.panel} ${styles.metric}`}>
          <span className={styles.metricLabel}>Model</span>
          <strong className={styles.metricValue}>{snapshot.model_version ?? "brak"}</strong>
          <code className={styles.code}>{identity(snapshot.model_hash)}</code>
        </article>
        <article className={`${styles.panel} ${styles.metric}`}>
          <span className={styles.metricLabel}>Parametry</span>
          <strong className={styles.metricValue}>{snapshot.parameter_version ?? "brak"}</strong>
          <code className={styles.code}>{identity(snapshot.parameter_hash)}</code>
        </article>
        <article className={`${styles.panel} ${styles.metric}`}>
          <span className={styles.metricLabel}>Dataset / kod</span>
          <code className={styles.code}>{identity(snapshot.dataset_hash)}</code>
          <code className={styles.code}>{identity(snapshot.code_sha)}</code>
        </article>
        <article className={`${styles.panel} ${styles.metric}`}>
          <span className={styles.metricLabel}>Drift</span>
          <strong className={styles.metricValue}>
            model {snapshot.model_drift} / dane {snapshot.data_drift}
          </strong>
        </article>
      </section>

      <section className={styles.panel}>
        <h2>Ostatnie decyzje</h2>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Status</th>
                <th>Kierunek</th>
                <th>Powody</th>
                <th>Czas</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.decisions.map((decision) => (
                <tr key={decision.shadow_decision_id} data-testid={`decision-${decision.symbol}`}>
                  <td>{decision.symbol}</td>
                  <td>{decision.status}</td>
                  <td>{decision.side ?? "—"}</td>
                  <td>{decision.reason_codes.join(", ")}</td>
                  <td>{timestamp(decision.observed_at_ms)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={styles.muted} data-testid="risk-rejection-count">
          Odrzucone przez Risk Engine: {riskRejections}
        </p>
      </section>

      <section className={styles.panel}>
        <h2>Pozycje symulowane</h2>
        {snapshot.positions.length ? (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Kierunek</th>
                  <th>Wejście</th>
                  <th>Mark</th>
                  <th>Ilość</th>
                  <th>TP / SL</th>
                </tr>
              </thead>
              <tbody>
                {snapshot.positions.map((position) => (
                  <tr key={position.position_id} data-testid={`position-${position.symbol}`}>
                    <td>{position.symbol}</td>
                    <td>{position.side}</td>
                    <td>{decimal(position.entry_price)}</td>
                    <td>{decimal(position.mark_price)}</td>
                    <td>{decimal(position.quantity)}</td>
                    <td>
                      {decimal(position.take_profit_price)} / {decimal(position.stop_loss_price)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className={styles.empty}>Brak otwartych pozycji symulowanych.</p>
        )}
      </section>

      <section className={styles.panel} data-testid="authority-boundary">
        <h2>Granica uprawnień</h2>
        <p className={styles.muted}>
          Snapshot jest tylko do odczytu. Poświadczenia: nie. Adapter zleceń: nie. Złożone
          zlecenia: {snapshot.orders_submitted}. Autoryzacja live capital: nie.
        </p>
      </section>
    </main>
  );
}
