"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  MarketEvidenceInstrumentPage,
  MarketEvidenceRun,
  MarketEvidenceRunPage,
  MarketEvidenceSource,
  MarketEvidenceSourceStatus,
  MarketEvidenceSummary,
} from "@/lib/market-evidence";

import styles from "./market-evidence-dashboard.module.css";

interface Filters {
  symbol: string;
  source: MarketEvidenceSource | "all";
  included: "all" | "true" | "false";
  sort: "symbol" | "source" | "spread" | "volume" | "freshness";
  direction: "asc" | "desc";
  page: number;
}

const INITIAL_FILTERS: Filters = {
  symbol: "",
  source: "all",
  included: "all",
  sort: "symbol",
  direction: "asc",
  page: 1,
};

async function fetchJson<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(path, {
    cache: "no-store",
    headers: { accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

function instrumentQuery(filters: Filters): string {
  const query = new URLSearchParams({
    page: String(filters.page),
    page_size: "10",
    sort: filters.sort,
    direction: filters.direction,
  });
  if (filters.symbol.trim()) query.set("symbol", filters.symbol.trim().toUpperCase());
  if (filters.source !== "all") query.set("source", filters.source);
  if (filters.included !== "all") query.set("included", filters.included);
  return query.toString();
}

function formatTimestamp(value: number | null): string {
  if (value === null) return "brak";
  return new Intl.DateTimeFormat("pl-PL", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(new Date(value));
}

function formatDuration(value: number | null): string {
  if (value === null) return "brak";
  if (value < 1_000) return `${value} ms`;
  const minutes = value / 60_000;
  if (minutes < 60) return `${new Intl.NumberFormat("pl-PL", { maximumFractionDigits: 1 }).format(minutes)} min`;
  return `${new Intl.NumberFormat("pl-PL", { maximumFractionDigits: 1 }).format(minutes / 60)} h`;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("pl-PL").format(value);
}

function formatDecimal(value: string | null, suffix = ""): string {
  if (value === null) return "brak";
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return `${value}${suffix}`;
  return `${new Intl.NumberFormat("pl-PL", { maximumFractionDigits: 2 }).format(parsed)}${suffix}`;
}

function shortHash(value: string | null): string {
  return value ? `${value.slice(0, 12)}…` : "brak";
}

function capabilityLabel(value: "available" | "unavailable" | "unknown"): string {
  if (value === "available") return "dostępne";
  if (value === "unavailable") return "niedostępne";
  return "nieznane";
}

function statusClass(value: string): string {
  return styles[value.toLowerCase()] ?? styles.unavailable;
}

function sourceCapability(
  label: string,
  value: "available" | "unavailable" | "unknown",
) {
  return (
    <div className={styles.capability}>
      <span>{label}</span>
      <strong className={statusClass(value)}>{capabilityLabel(value)}</strong>
    </div>
  );
}

export function MarketEvidenceDashboard() {
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  const [summary, setSummary] = useState<MarketEvidenceSummary | null>(null);
  const [sources, setSources] = useState<MarketEvidenceSourceStatus[]>([]);
  const [instruments, setInstruments] = useState<MarketEvidenceInstrumentPage | null>(null);
  const [runs, setRuns] = useState<MarketEvidenceRunPage | null>(null);
  const [selectedRun, setSelectedRun] = useState<MarketEvidenceRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (signal: AbortSignal) => {
      try {
        const [nextSummary, nextSources, nextInstruments, nextRuns] = await Promise.all([
          fetchJson<MarketEvidenceSummary>("/api/market/evidence/summary", signal),
          fetchJson<MarketEvidenceSourceStatus[]>("/api/market/evidence/sources", signal),
          fetchJson<MarketEvidenceInstrumentPage>(
            `/api/market/evidence/instruments?${instrumentQuery(filters)}`,
            signal,
          ),
          fetchJson<MarketEvidenceRunPage>("/api/market/evidence/runs?page=1&page_size=20", signal),
        ]);
        setSummary(nextSummary);
        setSources(nextSources);
        setInstruments(nextInstruments);
        setRuns(nextRuns);
        setSelectedRun((current) =>
          current ? nextRuns.items.find((run) => run.run_id === current.run_id) ?? null : null,
        );
        setError(null);
      } catch (loadError) {
        if (loadError instanceof DOMException && loadError.name === "AbortError") return;
        setError(loadError instanceof Error ? loadError.message : "Nie udało się pobrać danych");
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    },
    [filters],
  );

  useEffect(() => {
    const controller = new AbortController();
    const initial = window.setTimeout(() => void load(controller.signal), 0);
    const interval = window.setInterval(() => void load(controller.signal), 15_000);
    return () => {
      controller.abort();
      window.clearTimeout(initial);
      window.clearInterval(interval);
    };
  }, [load]);

  const blocker = useMemo(() => {
    if (!summary || summary.wh01.ready) return null;
    return {
      code: summary.wh01.blocker_code ?? "WH01_NOT_READY",
      detail: summary.wh01.blocker_detail ?? "Brak szczegółu blockera.",
    };
  }, [summary]);

  if (loading && !summary) {
    return <div className={styles.state}>Ładowanie danych WickHunter Market Evidence…</div>;
  }

  if (error && !summary) {
    return (
      <div className={`${styles.state} ${styles.error}`} role="alert">
        <strong>Market evidence jest niedostępne.</strong>
        <span>{error}</span>
      </div>
    );
  }

  if (!summary || !instruments || !runs) {
    return <div className={styles.state}>Brak bezpiecznego snapshotu market evidence.</div>;
  }

  return (
    <div className={styles.dashboard}>
      <section className={styles.hero}>
        <div>
          <span className={styles.eyebrow}>WickHunter · Read-only evidence</span>
          <h1>Market Evidence</h1>
          <p>
            Źródłowo rozdzielone świece, spread, wolumen, historia instrumentów i stan jakości
            wymagany przez WH-01. Ten widok nie udostępnia handlu ani modyfikacji immutable evidence.
          </p>
        </div>
        <div className={styles.statusCluster} aria-label="Stan market evidence">
          <span className={`${styles.badge} ${statusClass(summary.status)}`}>
            {summary.status}
          </span>
          <span className={`${styles.badge} ${summary.wh01.ready ? styles.eligible : styles.blocked}`}>
            WH-01 {summary.wh01.ready ? "READY" : "BLOCKED"}
          </span>
          <small>Aktualizacja: {formatTimestamp(summary.updated_at_ms)}</small>
        </div>
      </section>

      {blocker ? (
        <div className={styles.warning} role="status" data-testid="wh01-blocker">
          <strong>{blocker.code}</strong>
          <span>{blocker.detail}</span>
        </div>
      ) : null}

      {summary.status === "STALE" ? (
        <div className={styles.warning} role="status">
          <strong>Source stale</strong>
          <span>Ostatnia aktywność przekroczyła skonfigurowany próg świeżości.</span>
        </div>
      ) : null}

      {error ? <div className={styles.warning}>{error}</div> : null}

      <section className={styles.metrics} aria-label="Podsumowanie market evidence">
        <article className={styles.metric}>
          <span>Active run</span>
          <strong>{summary.active_run_id ?? "brak"}</strong>
          <small>trwały capture</small>
        </article>
        <article className={styles.metric}>
          <span>Immutable run</span>
          <strong>{summary.latest_immutable_run_id ?? "brak"}</strong>
          <small>{Math.round(summary.completeness * 100)}% kompletności</small>
        </article>
        <article className={styles.metric}>
          <span>Pre-roll</span>
          <strong>{formatDuration(summary.pre_roll_ms)}</strong>
          <small>{formatTimestamp(summary.capture_start_ms)}</small>
        </article>
        <article className={styles.metric}>
          <span>Instrumenty</span>
          <strong>{formatNumber(summary.instrument_count)}</strong>
          <small>source-separated</small>
        </article>
        <article className={styles.metric}>
          <span>Completed candles</span>
          <strong>{formatNumber(summary.completed_candle_count)}</strong>
          <small>tylko zamknięte</small>
        </article>
        <article className={styles.metric}>
          <span>Luki</span>
          <strong>{formatNumber(summary.gap_count)}</strong>
          <small>{formatDuration(summary.gap_duration_ms)}</small>
        </article>
      </section>

      <section className={styles.sources} aria-label="Status źródeł">
        {sources.map((source) => (
          <article className={styles.sourceCard} key={source.source} data-testid={`source-${source.source}`}>
            <div className={styles.sourceHeader}>
              <div>
                <span className={styles.eyebrow}>{source.source}</span>
                <h3>{source.display_name}</h3>
              </div>
              <span className={`${styles.badge} ${source.healthy ? styles.healthy : styles.degraded}`}>
                {source.healthy ? "healthy" : "degraded"}
              </span>
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
              <div><span>Symbols</span><strong>{source.active_symbols}</strong></div>
              <div><span>Reconnects / gaps</span><strong>{source.reconnect_count} / {source.gaps}</strong></div>
            </div>
            {source.exclusion_reason ? (
              <div className={styles.warning}>{source.exclusion_reason}</div>
            ) : null}
          </article>
        ))}
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <span className={styles.eyebrow}>Latest source snapshots</span>
            <h2>Instrumenty</h2>
          </div>
          <small>{formatNumber(instruments.total)} rekordów</small>
        </div>
        <div className={styles.filters} aria-label="Filtry instrumentów">
          <label>
            Szukaj symbolu
            <input
              aria-label="Szukaj symbolu"
              placeholder="np. BTCUSDT"
              value={filters.symbol}
              onChange={(event) =>
                setFilters((current) => ({ ...current, symbol: event.target.value, page: 1 }))
              }
            />
          </label>
          <label>
            Źródło
            <select
              aria-label="Źródło instrumentu"
              value={filters.source}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  source: event.target.value as Filters["source"],
                  page: 1,
                }))
              }
            >
              <option value="all">Wszystkie</option>
              <option value="binance-usdm">Binance USD-M</option>
              <option value="bybit-linear">Bybit Linear</option>
            </select>
          </label>
          <label>
            Inclusion
            <select
              value={filters.included}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  included: event.target.value as Filters["included"],
                  page: 1,
                }))
              }
            >
              <option value="all">Wszystkie</option>
              <option value="true">Included</option>
              <option value="false">Excluded</option>
            </select>
          </label>
          <label>
            Sortowanie
            <select
              value={filters.sort}
              onChange={(event) =>
                setFilters((current) => ({ ...current, sort: event.target.value as Filters["sort"] }))
              }
            >
              <option value="symbol">Symbol</option>
              <option value="source">Źródło</option>
              <option value="spread">Spread</option>
              <option value="volume">Wolumen 24h</option>
              <option value="freshness">Freshness</option>
            </select>
          </label>
          <label>
            Kierunek
            <select
              value={filters.direction}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  direction: event.target.value as Filters["direction"],
                }))
              }
            >
              <option value="asc">Rosnąco</option>
              <option value="desc">Malejąco</option>
            </select>
          </label>
        </div>
        {instruments.items.length === 0 ? (
          <div className={styles.empty}>Brak instrumentów dla wybranych filtrów.</div>
        ) : (
          <div className={styles.tableWrap}>
            <table>
              <thead>
                <tr>
                  <th>Symbol</th><th>Źródło</th><th>Status</th><th>Cena</th><th>Spread</th>
                  <th>Wolumen 24h</th><th>Ostatnia świeca</th><th>Historia</th><th>Freshness</th><th>Reason codes</th>
                </tr>
              </thead>
              <tbody>
                {instruments.items.map((instrument) => (
                  <tr key={`${instrument.source}:${instrument.symbol}`}>
                    <td><strong>{instrument.symbol}</strong></td>
                    <td>{instrument.source}</td>
                    <td><span className={`${styles.badge} ${instrument.included ? styles.eligible : styles.blocked}`}>{instrument.included ? "included" : "excluded"}</span></td>
                    <td>{formatDecimal(instrument.latest_price)}</td>
                    <td>{formatDecimal(instrument.spread_bps, " bps")}</td>
                    <td>{formatDecimal(instrument.quote_volume_24h, " USDT")}</td>
                    <td>{formatTimestamp(instrument.last_completed_candle_at_ms)}</td>
                    <td>{formatNumber(instrument.history_depth_rows)} rows</td>
                    <td>{formatDuration(instrument.freshness_ms)}</td>
                    <td><div className={styles.reasonCodes}>{instrument.reason_codes.map((code) => <span className={styles.reasonCode} key={code}>{code}</span>)}</div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className={styles.pagination}>
          <button
            type="button"
            disabled={filters.page <= 1}
            onClick={() => setFilters((current) => ({ ...current, page: current.page - 1 }))}
          >
            Poprzednia
          </button>
          <span>Strona {instruments.page} z {Math.max(1, instruments.total_pages)}</span>
          <button
            type="button"
            disabled={instruments.total_pages === 0 || filters.page >= instruments.total_pages}
            onClick={() => setFilters((current) => ({ ...current, page: current.page + 1 }))}
          >
            Następna
          </button>
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div><span className={styles.eyebrow}>Immutable evidence</span><h2>Runy</h2></div>
          <small>{runs.total} runów</small>
        </div>
        {runs.items.length === 0 ? (
          <div className={styles.empty}>Brak runów market evidence.</div>
        ) : (
          <div className={styles.tableWrap}>
            <table>
              <thead><tr><th>Run ID</th><th>State</th><th>Zakres</th><th>Pre-roll</th><th>Kompletność</th><th>Źródła</th><th>Rekordy</th><th>Luki</th><th>Verification</th><th>WH-01</th><th>Szczegóły</th></tr></thead>
              <tbody>
                {runs.items.map((run) => (
                  <tr key={run.run_id}>
                    <td><strong>{run.run_id}</strong></td>
                    <td>{run.state}</td>
                    <td>{formatTimestamp(run.capture_start_ms)} – {formatTimestamp(run.capture_end_ms)}</td>
                    <td>{formatDuration(run.pre_roll_ms)}</td>
                    <td>{Math.round(run.completeness * 100)}%</td>
                    <td>{run.source_coverage.join(", ")}</td>
                    <td>{formatNumber(run.completed_candle_count + run.market_quality_observation_count)}</td>
                    <td>{run.gap_count}</td>
                    <td><span className={`${styles.badge} ${statusClass(run.verification_result)}`}>{run.verification_result}</span></td>
                    <td>{run.wh01_eligible ? "ready" : run.reason_codes.join(", ")}</td>
                    <td><button type="button" onClick={() => setSelectedRun(run)}>Szczegóły</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedRun ? (
        <section className={styles.panel} data-testid="run-details">
          <div className={styles.panelHeader}>
            <div><span className={styles.eyebrow}>Run detail</span><h2>{selectedRun.run_id}</h2></div>
            <span className={`${styles.badge} ${selectedRun.wh01_eligible ? styles.eligible : styles.blocked}`}>WH-01 {selectedRun.wh01_eligible ? "READY" : "BLOCKED"}</span>
          </div>
          <div className={styles.sourceMeta}>
            <div><span>Manifest SHA-256</span><strong className={styles.hash}>{shortHash(selectedRun.manifest_sha256)}</strong></div>
            <div><span>Request SHA-256</span><strong className={styles.hash}>{shortHash(selectedRun.request_sha256)}</strong></div>
            <div><span>Policy SHA-256</span><strong className={styles.hash}>{shortHash(selectedRun.policy_sha256)}</strong></div>
            <div><span>Code SHA</span><strong className={styles.hash}>{shortHash(selectedRun.code_sha)}</strong></div>
            <div><span>Verification</span><strong>{selectedRun.verification_result}</strong></div>
            <div><span>Blocker / reason</span><strong>{selectedRun.reason_codes.join(", ")}</strong></div>
          </div>
        </section>
      ) : null}
    </div>
  );
}
