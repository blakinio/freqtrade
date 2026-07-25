"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  LiquidatedPositionSide,
  LiquidationHealth,
  LiquidationPage,
  LiquidationSource,
  LiquidationSummary,
} from "@/lib/liquidations";

import styles from "./liquidations-dashboard.module.css";

type TimeRange = "5m" | "1h" | "24h";

interface Filters {
  source: LiquidationSource | "all";
  symbol: string;
  side: LiquidatedPositionSide | "all";
  range: TimeRange;
}

const RANGE_MS: Record<TimeRange, number> = {
  "5m": 5 * 60 * 1_000,
  "1h": 60 * 60 * 1_000,
  "24h": 24 * 60 * 60 * 1_000,
};

const INITIAL_FILTERS: Filters = {
  source: "all",
  symbol: "",
  side: "all",
  range: "24h",
};

async function fetchJson<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(path, {
    cache: "no-store",
    headers: { accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

function buildQuery(filters: Filters, health: LiquidationHealth, includeRange: boolean): string {
  const query = new URLSearchParams();
  if (filters.source !== "all") {
    query.set("source", filters.source);
  }
  if (filters.symbol.trim()) {
    query.set("symbol", filters.symbol.trim().toUpperCase());
  }
  if (filters.side !== "all") {
    query.set("side", filters.side);
  }
  if (includeRange) {
    const anchor =
      health.mode === "historical" && health.last_event_at_ms
        ? health.last_event_at_ms
        : Date.now();
    query.set("since", String(Math.max(0, anchor - RANGE_MS[filters.range])));
    query.set("until", String(anchor));
    query.set("limit", "100");
  }
  const value = query.toString();
  return value ? `?${value}` : "";
}

function formatNotional(value: string): string {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return `${value} USDT`;
  }
  return `${new Intl.NumberFormat("pl-PL", {
    maximumFractionDigits: 2,
  }).format(parsed)} USDT`;
}

function formatTimestamp(value: number | null): string {
  if (!value) {
    return "brak";
  }
  return new Intl.DateTimeFormat("pl-PL", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(new Date(value));
}

function modeLabel(mode: LiquidationHealth["mode"]): string {
  if (mode === "historical") {
    return "historyczne";
  }
  return mode === "live" ? "live" : "nieświeże";
}

function acceptanceLabel(status: LiquidationHealth["acceptance_status"]): string {
  if (status === "accepted") {
    return "zaakceptowane";
  }
  if (status === "failed") {
    return "acceptance failed";
  }
  if (status === "in-progress") {
    return "w trakcie oceny";
  }
  return "brak raportu";
}

export function LiquidationsDashboard() {
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  const [health, setHealth] = useState<LiquidationHealth | null>(null);
  const [summary, setSummary] = useState<LiquidationSummary | null>(null);
  const [page, setPage] = useState<LiquidationPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (signal: AbortSignal) => {
      try {
        const nextHealth = await fetchJson<LiquidationHealth>(
          "/api/market/liquidations/health",
          signal,
        );
        const [nextSummary, nextPage] = await Promise.all([
          fetchJson<LiquidationSummary>(
            `/api/market/liquidations/summary${buildQuery(filters, nextHealth, false)}`,
            signal,
          ),
          fetchJson<LiquidationPage>(
            `/api/market/liquidations${buildQuery(filters, nextHealth, true)}`,
            signal,
          ),
        ]);
        setError(null);
        setHealth(nextHealth);
        setSummary(nextSummary);
        setPage(nextPage);
      } catch (loadError) {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Nie udało się pobrać danych");
      } finally {
        if (!signal.aborted) {
          setLoading(false);
        }
      }
    },
    [filters],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    const interval = window.setInterval(() => {
      void load(controller.signal);
    }, 10_000);
    return () => {
      controller.abort();
      window.clearInterval(interval);
    };
  }, [load]);

  const symbols = useMemo(
    () => [...new Set(page?.events.map((event) => event.symbol) ?? [])].sort(),
    [page],
  );

  if (loading && !health) {
    return <div className={styles.state}>Ładowanie danych o likwidacjach…</div>;
  }

  if (error && !health) {
    return (
      <div className={`${styles.state} ${styles.errorState}`} role="alert">
        <strong>Dane Liquid20 są niedostępne.</strong>
        <span>{error}</span>
      </div>
    );
  }

  if (!health || !summary || !page) {
    return <div className={styles.state}>Brak bezpiecznego snapshotu Liquid20.</div>;
  }

  const completedFailure =
    health.latest_completed_acceptance?.status === "failed"
      ? health.latest_completed_acceptance
      : null;
  const failedGates =
    health.failed_gates.length > 0
      ? health.failed_gates
      : completedFailure?.failed_gates ?? [];

  return (
    <div className={styles.dashboard}>
      <section className={styles.hero}>
        <div>
          <span className={styles.eyebrow}>Market Data · Research preview</span>
          <h1>Likwidacje</h1>
          <p>
            Źródłowo oznaczone zdarzenia Liquid20 z Bybit i Binance. Moduł jest wyłącznie
            do odczytu i nie autoryzuje handlu.
          </p>
        </div>
        <div className={styles.statusCluster} aria-label="Stan danych">
          <span className={`${styles.badge} ${styles[health.mode]}`}>
            {modeLabel(health.mode)}
          </span>
          <span className={`${styles.badge} ${styles.acceptance}`}>
            {acceptanceLabel(health.acceptance_status)}
          </span>
          <small>Aktualizacja: {formatTimestamp(health.refreshed_at_ms)}</small>
        </div>
      </section>

      {health.stale ? (
        <div className={styles.warning} role="status">
          Źródło nie aktualizuje się w oczekiwanym czasie. Dane pozostają dostępne jako
          nieświeży research preview.
        </div>
      ) : null}

      {health.acceptance_status === "failed" || completedFailure ? (
        <div className={styles.warning} role="status">
          <strong>Acceptance failed.</strong>{" "}
          Niespełniona bramka: {failedGates.join(", ") || "brak szczegółu"}. Dane nie stanowią
          autoryzacji handlowej.
        </div>
      ) : null}

      {error ? <div className={styles.inlineError}>{error}</div> : null}

      <section className={styles.filters} aria-label="Filtry likwidacji">
        <label>
          Źródło
          <select
            value={filters.source}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                source: event.target.value as Filters["source"],
              }))
            }
          >
            <option value="all">Wszystkie</option>
            <option value="bybit-linear">Bybit</option>
            <option value="binance-usdm">Binance</option>
          </select>
        </label>
        <label>
          Symbol
          <input
            list="liquidation-symbols"
            placeholder="np. BTCUSDT"
            value={filters.symbol}
            onChange={(event) =>
              setFilters((current) => ({ ...current, symbol: event.target.value }))
            }
          />
          <datalist id="liquidation-symbols">
            {symbols.map((symbol) => (
              <option key={symbol} value={symbol} />
            ))}
          </datalist>
        </label>
        <label>
          Likwidowana pozycja
          <select
            value={filters.side}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                side: event.target.value as Filters["side"],
              }))
            }
          >
            <option value="all">Long i short</option>
            <option value="long">Long</option>
            <option value="short">Short</option>
          </select>
        </label>
        <label>
          Zakres tabeli
          <select
            value={filters.range}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                range: event.target.value as TimeRange,
              }))
            }
          >
            <option value="5m">5 minut</option>
            <option value="1h">1 godzina</option>
            <option value="24h">24 godziny</option>
          </select>
        </label>
      </section>

      <section className={styles.metrics} aria-label="Podsumowanie likwidacji">
        {summary.windows.map((window) => (
          <article className={styles.metricCard} key={window.window}>
            <span>{window.window}</span>
            <strong>{formatNotional(window.notional_usd)}</strong>
            <small>{window.event_count} zdarzeń</small>
            <div className={styles.split}>
              <span>Long: {formatNotional(window.long.notional_usd)}</span>
              <span>Short: {formatNotional(window.short.notional_usd)}</span>
            </div>
          </article>
        ))}
      </section>

      <section className={styles.grid}>
        <article className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <span className={styles.eyebrow}>Ostatnie zdarzenia</span>
              <h2>Strumień likwidacji</h2>
            </div>
            <small>{page.events.length} rekordów</small>
          </div>
          {page.events.length === 0 ? (
            <div className={styles.empty}>Brak zdarzeń dla wybranych filtrów.</div>
          ) : (
            <div className={styles.tableWrap}>
              <table>
                <thead>
                  <tr>
                    <th>Czas</th>
                    <th>Giełda</th>
                    <th>Symbol</th>
                    <th>Pozycja</th>
                    <th>Cena</th>
                    <th>Ilość</th>
                    <th>Wartość</th>
                    <th>Ingest</th>
                  </tr>
                </thead>
                <tbody>
                  {page.events.map((event) => (
                    <tr key={`${event.source}:${event.source_event_id}`}>
                      <td>{formatTimestamp(event.occurred_at_ms)}</td>
                      <td>{event.source === "bybit-linear" ? "Bybit" : "Binance"}</td>
                      <td>
                        <strong>{event.symbol}</strong>
                      </td>
                      <td>
                        <span
                          className={`${styles.side} ${styles[event.liquidated_position_side]}`}
                        >
                          {event.liquidated_position_side}
                        </span>
                      </td>
                      <td>{event.price}</td>
                      <td>{event.quantity}</td>
                      <td>{formatNotional(event.notional_usd)}</td>
                      <td>{event.ingest_latency_ms} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <aside className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <span className={styles.eyebrow}>24h</span>
              <h2>Ranking symboli</h2>
            </div>
          </div>
          <ol className={styles.ranking}>
            {summary.ranking_24h.slice(0, 10).map((ranking) => (
              <li key={ranking.symbol}>
                <div>
                  <strong>{ranking.symbol}</strong>
                  <span>{ranking.event_count} zdarzeń</span>
                </div>
                <div className={styles.rankingValue}>
                  <strong>{formatNotional(ranking.notional_usd)}</strong>
                  <span>
                    long {ranking.long_event_count} · short {ranking.short_event_count}
                  </span>
                </div>
              </li>
            ))}
          </ol>
        </aside>
      </section>

      <section className={styles.sourceNotes} aria-label="Semantyka źródeł">
        <article>
          <strong>Bybit</strong>
          <p>{health.source_semantics["bybit-linear"]}</p>
        </article>
        <article>
          <strong>Binance</strong>
          <p>{health.source_semantics["binance-usdm"]}</p>
        </article>
        <p className={styles.semanticWarning}>
          Zdarzeń między giełdami nie deduplikuje się ani nie sumuje bez zachowania etykiety
          źródła, ponieważ semantyka publikacji nie jest identyczna.
        </p>
      </section>
    </div>
  );
}
