"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import styles from "./market-evidence-dashboard.module.css";

import type {
  MarketEvidenceInstrumentsResponse,
  MarketEvidenceRunsResponse,
  MarketEvidenceSourcesResponse,
  MarketEvidenceSummaryResponse,
  MarketEvidenceUniverseInstrument,
} from "../lib/market-evidence/contracts";

type MarketEvidenceDashboardProps = {
  initialSummary: MarketEvidenceSummaryResponse;
  initialSources: MarketEvidenceSourcesResponse;
  initialRuns: MarketEvidenceRunsResponse;
  initialInstruments: MarketEvidenceInstrumentsResponse;
};

type FilterStatus = "all" | "eligible" | "excluded";

function formatTimestamp(value: number | null): string {
  if (value === null) {
    return "brak danych";
  }
  return new Date(value).toLocaleString("pl-PL", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "UTC",
  });
}

function formatDuration(value: number | null): string {
  if (value === null) {
    return "brak danych";
  }
  if (value < 1_000) {
    return `${value} ms`;
  }
  if (value < 60_000) {
    return `${(value / 1_000).toFixed(1)} s`;
  }
  return `${(value / 60_000).toFixed(1)} min`;
}

function formatNumber(value: number | null, maximumFractionDigits = 2): string {
  if (value === null) {
    return "brak danych";
  }
  return new Intl.NumberFormat("pl-PL", { maximumFractionDigits }).format(value);
}

function statusLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function statusClass(value: string): string {
  if (["accepted", "active", "eligible", "healthy", "online"].includes(value)) {
    return styles.healthy;
  }
  if (["blocked", "excluded", "stale", "offline", "failed", "rejected"].includes(value)) {
    return styles.blocked;
  }
  return styles.degraded;
}

function sourceCapability(label: string, enabled: boolean) {
  return (
    <span className={enabled ? styles.capabilityEnabled : styles.capabilityDisabled}>
      {label}: {enabled ? "tak" : "nie"}
    </span>
  );
}

export function MarketEvidenceDashboard({
  initialSummary,
  initialSources,
  initialRuns,
  initialInstruments,
}: MarketEvidenceDashboardProps) {
  const [summary, setSummary] = useState(initialSummary);
  const [sources, setSources] = useState(initialSources);
  const [runs, setRuns] = useState(initialRuns);
  const [instruments, setInstruments] = useState(initialInstruments);
  const [query, setQuery] = useState("");
  const [venue, setVenue] = useState("all");
  const [status, setStatus] = useState<FilterStatus>("all");
  const [selectedInstrument, setSelectedInstrument] = useState<MarketEvidenceUniverseInstrument | null>(null);
  const [refreshState, setRefreshState] = useState<"idle" | "refreshing" | "failed">("idle");
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [lastRefreshAt, setLastRefreshAt] = useState(() => Date.now());

  const refresh = useCallback(async () => {
    setRefreshState("refreshing");
    setRefreshError(null);
    try {
      const responses = await Promise.all([
        fetch("/api/market/evidence/summary", { cache: "no-store" }),
        fetch("/api/market/evidence/sources", { cache: "no-store" }),
        fetch("/api/market/evidence/runs", { cache: "no-store" }),
        fetch("/api/market/evidence/instruments", { cache: "no-store" }),
      ]);
      if (responses.some((response) => !response.ok)) {
        throw new Error("Nie udało się odświeżyć danych market evidence.");
      }
      const [nextSummary, nextSources, nextRuns, nextInstruments] = await Promise.all(
        responses.map((response) => response.json()),
      );
      setSummary(nextSummary as MarketEvidenceSummaryResponse);
      setSources(nextSources as MarketEvidenceSourcesResponse);
      setRuns(nextRuns as MarketEvidenceRunsResponse);
      setInstruments(nextInstruments as MarketEvidenceInstrumentsResponse);
      setLastRefreshAt(Date.now());
      setRefreshState("idle");
    } catch (error) {
      setRefreshState("failed");
      setRefreshError(error instanceof Error ? error.message : "Nie udało się odświeżyć danych.");
    }
  }, []);

  useEffect(() => {
    const interval = window.setInterval(() => {
      void refresh();
    }, 30_000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  const venues = useMemo(
    () => ["all", ...Array.from(new Set(instruments.items.map((item) => item.venue))).sort()],
    [instruments.items],
  );

  const filteredInstruments = useMemo(() => {
    const normalizedQuery = query.trim().toUpperCase();
    return instruments.items.filter((item) => {
      if (venue !== "all" && item.venue !== venue) {
        return false;
      }
      if (status === "eligible" && !item.wickhunter_eligible) {
        return false;
      }
      if (status === "excluded" && item.wickhunter_eligible) {
        return false;
      }
      if (
        normalizedQuery &&
        !item.instrument_id.toUpperCase().includes(normalizedQuery) &&
        !item.base_asset.toUpperCase().includes(normalizedQuery)
      ) {
        return false;
      }
      return true;
    });
  }, [instruments.items, query, status, venue]);

  return (
    <main className={styles.page}>
      <section className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>WickHunter / Market Evidence</p>
          <h1>Publiczne dane rynkowe gotowe do audytu</h1>
          <p>
            Read-only widok źródeł, jakości danych, pokrycia dynamicznego universe i immutable evidence runs.
            Brak ścieżki do giełdy, Vault i Freqtrade.
          </p>
        </div>
        <div className={styles.heroActions}>
          <button type="button" onClick={() => void refresh()} disabled={refreshState === "refreshing"}>
            {refreshState === "refreshing" ? "Odświeżanie…" : "Odśwież teraz"}
          </button>
          <span>Portal read: {formatTimestamp(lastRefreshAt)}</span>
        </div>
      </section>

      {refreshError ? <div className={styles.errorBanner}>{refreshError}</div> : null}

      <section className={styles.summaryGrid}>
        <article className={styles.summaryCard}>
          <span>Stan pakietu</span>
          <strong className={statusClass(summary.status)}>{statusLabel(summary.status)}</strong>
          <small>{summary.package_id ?? summary.run_id ?? "brak aktywnego pakietu"}</small>
        </article>
        <article className={styles.summaryCard}>
          <span>Freshness</span>
          <strong>{formatDuration(summary.freshness_ms)}</strong>
          <small>ostatni event: {formatTimestamp(summary.last_event_at_ms)}</small>
        </article>
        <article className={styles.summaryCard}>
          <span>Universe</span>
          <strong>{summary.eligible_instruments} / {summary.total_instruments}</strong>
          <small>eligible / wszystkie instrumenty</small>
        </article>
        <article className={styles.summaryCard}>
          <span>Jakość rynku</span>
          <strong>{summary.market_quality_observations}</strong>
          <small>obserwacji jakości</small>
        </article>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <p className={styles.eyebrow}>Źródła</p>
            <h2>Zdrowie i zakres kontraktu</h2>
          </div>
          <span>{sources.items.length} source(s)</span>
        </div>
        <div className={styles.sourceGrid}>
          {sources.items.map((source) => (
            <article key={source.source_id} className={styles.sourceCard}>
              <div className={styles.cardHeading}>
                <div>
                  <strong>{source.display_name}</strong>
                  <small>{source.market_type}</small>
                </div>
                <span className={statusClass(source.status)}>{statusLabel(source.status)}</span>
              </div>
              <div className={styles.capabilities}>
                {sourceCapability("Liquidation feed", source.liquidation_feed)}
                {sourceCapability("Candle evidence", source.candle_evidence)}
                {sourceCapability("Market quality", source.market_quality_evidence)}
                {sourceCapability("Instrument history", source.instrument_history)}
                <div className={styles.capability}>
                  <span>WickHunter eligibility</span>
                  <strong className={source.wickhunter_available ? styles.eligible : styles.blocked}>
                    {source.wickhunter_available ? "eligible" : "excluded"}
                  </strong>
                </div>
              </div>
              <div className={styles.sourceMeta}>
                <div><span>Ostatni event</span><strong>{formatTimestamp(source.last_event_at_ms)}</strong></div>
                <div><span>Ostatni ticker</span><strong>{formatTimestamp(source.last_ticker_at_ms)}</strong></div>
                <div><span>Ostatnia świeca</span><strong>{formatTimestamp(source.last_completed_candle_at_ms)}</strong></div>
                <div><span>Freshness</span><strong>{formatDuration(source.freshness_ms)}</strong></div>
                <div><span>Aktywne pary</span><strong>{source.active_symbols}</strong></div>
                <div><span>Reconnects / gaps</span><strong>{source.reconnect_count} / {source.gaps}</strong></div>
              </div>
              {source.exclusion_reason ? (
                <div className={styles.warning}>{source.exclusion_reason}</div>
              ) : null}
            </article>
          ))}
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <p className={styles.eyebrow}>Evidence runs</p>
            <h2>Immutable package i weryfikacja</h2>
          </div>
          <span>{runs.items.length} run(s)</span>
        </div>
        <div className={styles.runList}>
          {runs.items.map((run) => (
            <article key={run.run_id} className={styles.runCard}>
              <div>
                <strong>{run.run_id}</strong>
                <small>{run.package_id ?? "brak package id"}</small>
              </div>
              <div>
                <span className={statusClass(run.status)}>{statusLabel(run.status)}</span>
                <small>start {formatTimestamp(run.started_at_ms)}</small>
                <small>koniec {formatTimestamp(run.completed_at_ms)}</small>
              </div>
              <div>
                <strong>{run.instrument_count}</strong>
                <small>instrumentów</small>
              </div>
              <div>
                <strong>{run.market_quality_observations}</strong>
                <small>quality observations</small>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <p className={styles.eyebrow}>Universe</p>
            <h2>Instrumenty i kwalifikacja WickHunter</h2>
          </div>
          <span>{filteredInstruments.length} / {instruments.items.length}</span>
        </div>
        <div className={styles.filters}>
          <label>
            Szukaj
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="BTC, ETH, SOL…"
            />
          </label>
          <label>
            Giełda
            <select value={venue} onChange={(event) => setVenue(event.target.value)}>
              {venues.map((value) => (
                <option key={value} value={value}>
                  {value === "all" ? "Wszystkie" : value}
                </option>
              ))}
            </select>
          </label>
          <label>
            Status
            <select value={status} onChange={(event) => setStatus(event.target.value as FilterStatus)}>
              <option value="all">Wszystkie</option>
              <option value="eligible">Eligible</option>
              <option value="excluded">Excluded</option>
            </select>
          </label>
        </div>
        <div className={styles.instrumentTableWrapper}>
          <table className={styles.instrumentTable}>
            <thead>
              <tr>
                <th>Instrument</th>
                <th>Venue</th>
                <th>Status</th>
                <th>24h notional</th>
                <th>ATR ratio</th>
                <th>24h volatility</th>
                <th>Spread</th>
                <th>Depth</th>
              </tr>
            </thead>
            <tbody>
              {filteredInstruments.map((instrument) => (
                <tr key={instrument.instrument_id} onClick={() => setSelectedInstrument(instrument)}>
                  <td>
                    <strong>{instrument.instrument_id}</strong>
                    <small>{instrument.base_asset}</small>
                  </td>
                  <td>{instrument.venue}</td>
                  <td><span className={instrument.wickhunter_eligible ? styles.healthy : styles.blocked}>{instrument.wickhunter_eligible ? "eligible" : "excluded"}</span></td>
                  <td>{formatNumber(instrument.notional_volume_24h)}</td>
                  <td>{formatNumber(instrument.atr_ratio_24h, 6)}</td>
                  <td>{formatNumber(instrument.volatility_24h, 6)}</td>
                  <td>{formatNumber(instrument.spread_bps, 3)}</td>
                  <td>{formatNumber(instrument.depth_notional)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredInstruments.length === 0 ? <div className={styles.emptyState}>Brak instrumentów dla wybranych filtrów.</div> : null}
        </div>
      </section>

      {selectedInstrument ? (
        <div className={styles.drawerBackdrop} role="presentation" onClick={() => setSelectedInstrument(null)}>
          <aside className={styles.drawer} role="dialog" aria-modal="true" aria-label="Szczegóły instrumentu" onClick={(event) => event.stopPropagation()}>
            <button type="button" className={styles.closeButton} onClick={() => setSelectedInstrument(null)}>Zamknij</button>
            <p className={styles.eyebrow}>{selectedInstrument.venue}</p>
            <h2>{selectedInstrument.instrument_id}</h2>
            <span className={selectedInstrument.wickhunter_eligible ? styles.healthy : styles.blocked}>
              {selectedInstrument.wickhunter_eligible ? "eligible" : "excluded"}
            </span>
            <dl className={styles.detailList}>
              <div><dt>Base asset</dt><dd>{selectedInstrument.base_asset}</dd></div>
              <div><dt>Status kontraktu</dt><dd>{selectedInstrument.contract_status}</dd></div>
              <div><dt>Pierwsza obserwacja</dt><dd>{formatTimestamp(selectedInstrument.first_observed_at_ms)}</dd></div>
              <div><dt>Ostatnia obserwacja</dt><dd>{formatTimestamp(selectedInstrument.last_observed_at_ms)}</dd></div>
              <div><dt>Ostatni ticker</dt><dd>{formatTimestamp(selectedInstrument.last_ticker_at_ms)}</dd></div>
              <div><dt>Ostatnia świeca</dt><dd>{formatTimestamp(selectedInstrument.last_completed_candle_at_ms)}</dd></div>
              <div><dt>Notional 24h</dt><dd>{formatNumber(selectedInstrument.notional_volume_24h)}</dd></div>
              <div><dt>ATR ratio</dt><dd>{formatNumber(selectedInstrument.atr_ratio_24h, 6)}</dd></div>
              <div><dt>Volatility 24h</dt><dd>{formatNumber(selectedInstrument.volatility_24h, 6)}</dd></div>
              <div><dt>Spread bps</dt><dd>{formatNumber(selectedInstrument.spread_bps, 3)}</dd></div>
              <div><dt>Depth notional</dt><dd>{formatNumber(selectedInstrument.depth_notional)}</dd></div>
              <div><dt>Powód wykluczenia</dt><dd>{selectedInstrument.exclusion_reason ?? "brak"}</dd></div>
            </dl>
          </aside>
        </div>
      ) : null}
    </main>
  );
}
