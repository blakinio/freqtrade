"use client";

import { useMemo, useState, useTransition } from "react";

import { StatusPill } from "@/components/status-pill";
import type {
  ExperimentBundle,
  ExperimentComparison,
  ExperimentCreateRequest,
  ExperimentSummary,
  StrategyLabDefinition,
} from "@/lib/strategy-lab-contracts";

import {
  compareStrategyLabExperimentVariants,
  loadStrategyLabExperiment,
  runStrategyLabExperiment,
} from "./actions";

interface Props {
  strategies: StrategyLabDefinition[];
  initialExperiments: ExperimentSummary[];
  initialBundle: ExperimentBundle | null;
  initialComparison: ExperimentComparison | null;
}

function number(value: string | number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function percent(value: string | number): string {
  return `${(number(value) * 100).toFixed(2)}%`;
}

function money(value: string | number): string {
  return new Intl.NumberFormat("pl-PL", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(number(value));
}

function summary(bundle: ExperimentBundle): ExperimentSummary {
  const value = bundle.detail;
  return {
    experiment_id: value.experiment_id,
    status: value.status,
    strategy_id: value.strategy_id,
    strategy_version: value.strategy_version,
    pair: value.pair,
    timeframe: value.timeframe,
    started_at: value.started_at,
    trade_count: value.trade_count,
    profit_abs: value.profit_abs,
    profit_pct: value.profit_pct,
    max_drawdown: value.max_drawdown,
  };
}

export function StrategyLabClient({ strategies, initialExperiments, initialBundle, initialComparison }: Props) {
  const [experiments, setExperiments] = useState(initialExperiments);
  const [selected, setSelected] = useState(initialBundle);
  const [comparison, setComparison] = useState(initialComparison);
  const [baselineId, setBaselineId] = useState(initialExperiments[0]?.experiment_id ?? "");
  const [variantId, setVariantId] = useState(initialExperiments[1]?.experiment_id ?? "");
  const [strategyId, setStrategyId] = useState(strategies[0]?.strategy_id ?? "tv_supertrend_v1");
  const selectedStrategy = strategies.find((item) => item.strategy_id === strategyId) ?? strategies[0];
  const defaults = useMemo(
    () => Object.fromEntries((selectedStrategy?.parameters ?? []).map((item) => [item.name, item.default])),
    [selectedStrategy],
  );
  const [parameters, setParameters] = useState<Record<string, unknown>>(defaults);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function changeStrategy(value: string) {
    setStrategyId(value);
    const definition = strategies.find((item) => item.strategy_id === value);
    setParameters(Object.fromEntries((definition?.parameters ?? []).map((item) => [item.name, item.default])));
  }

  function submit(formData: FormData) {
    const definition = strategies.find((item) => item.strategy_id === strategyId);
    if (!definition) return;
    const request: ExperimentCreateRequest = {
      strategy_id: definition.strategy_id,
      strategy_version: definition.strategy_version,
      pair: String(formData.get("pair") ?? "BTC/USDT"),
      timeframe: String(formData.get("timeframe") ?? "15m"),
      timerange: {
        start_at: new Date(String(formData.get("start_at"))).toISOString(),
        end_at: new Date(String(formData.get("end_at"))).toISOString(),
      },
      starting_balance: String(formData.get("starting_balance") ?? "10000"),
      fee_rate: "0.001",
      slippage_rate: "0",
      parameter_overrides: parameters,
      execution_mode: "backtest",
    };
    const idempotencyKey = `lab-${crypto.randomUUID()}`;
    startTransition(async () => {
      try {
        setError(null);
        const created = await runStrategyLabExperiment(request, idempotencyKey.slice(0, 128));
        setSelected(created);
        setExperiments((current) => [summary(created), ...current.filter((item) => item.experiment_id !== created.detail.experiment_id)]);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Nie udało się uruchomić testu");
      }
    });
  }

  function openExperiment(experimentId: string) {
    startTransition(async () => {
      try {
        setError(null);
        setSelected(await loadStrategyLabExperiment(experimentId));
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Nie udało się pobrać eksperymentu");
      }
    });
  }

  function runComparison() {
    if (!baselineId || !variantId) return;
    startTransition(async () => {
      try {
        setError(null);
        setComparison(await compareStrategyLabExperimentVariants(baselineId, variantId));
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Nie udało się porównać eksperymentów");
      }
    });
  }

  return (
    <section className="page-stack" data-testid="strategy-lab">
      <div className="page-heading">
        <div><span className="eyebrow">Bot Management</span><h1>Testy / Laboratorium</h1></div>
        <span className="freshness">Research-only · closed bars · no live orders</span>
      </div>
      <div className="status-banner status-info">
        <strong>Deterministyczne laboratorium strategii</strong>
        <span>Przeglądarka komunikuje się wyłącznie z Portal BFF. Wyniki nie promują strategii i nie uruchamiają handlu.</span>
      </div>
      {error ? <div className="status-banner status-error"><strong>Błąd</strong><span>{error}</span></div> : null}

      <article className="panel">
        <h2>Uruchom test</h2>
        <form action={submit} className="page-stack" data-testid="strategy-lab-form">
          <div className="form-grid">
            <label>Strategia<select name="strategy" value={strategyId} onChange={(event) => changeStrategy(event.target.value)}>{strategies.map((item) => <option key={item.strategy_id} value={item.strategy_id}>{item.display_name}</option>)}</select></label>
            <label>Para<input name="pair" defaultValue="BTC/USDT" /></label>
            <label>Timeframe<select name="timeframe" defaultValue="15m"><option>15m</option></select></label>
            <label>Od<input name="start_at" type="datetime-local" defaultValue="2026-01-01T00:00" /></label>
            <label>Do<input name="end_at" type="datetime-local" defaultValue="2026-01-01T09:30" /></label>
            <label>Kapitał początkowy<input name="starting_balance" type="number" min="1" step="0.01" defaultValue="10000" /></label>
          </div>
          <div className="form-grid" data-testid="strategy-parameters">
            {(selectedStrategy?.parameters ?? []).map((spec) => (
              <label key={spec.name}>{spec.name}
                {spec.kind === "boolean" ? (
                  <input type="checkbox" checked={Boolean(parameters[spec.name])} onChange={(event) => setParameters((current) => ({ ...current, [spec.name]: event.target.checked }))} />
                ) : spec.kind === "enum" ? (
                  <select value={String(parameters[spec.name])} onChange={(event) => setParameters((current) => ({ ...current, [spec.name]: event.target.value }))}>{spec.choices.map((choice) => <option key={String(choice)}>{String(choice)}</option>)}</select>
                ) : (
                  <input type="number" value={Number(parameters[spec.name])} min={spec.minimum ?? undefined} max={spec.maximum ?? undefined} step={spec.kind === "integer" ? 1 : "any"} onChange={(event) => setParameters((current) => ({ ...current, [spec.name]: spec.kind === "integer" ? Number.parseInt(event.target.value, 10) : Number(event.target.value) }))} />
                )}
              </label>
            ))}
          </div>
          <button type="submit" disabled={pending}>{pending ? "Wykonywanie…" : "Uruchom test"}</button>
        </form>
      </article>

      <article className="panel">
        <h2>Eksperymenty</h2>
        <div className="table-wrap"><table><thead><tr><th>Status</th><th>Strategia</th><th>Para / TF</th><th>Data</th><th>Transakcje</th><th>Wynik</th><th>Drawdown</th><th>Akcja</th></tr></thead><tbody>
          {experiments.map((item) => <tr key={item.experiment_id}><td><StatusPill value={item.status} /></td><td><strong>{item.strategy_id}</strong><span>{item.strategy_version}</span></td><td>{item.pair}<span>{item.timeframe}</span></td><td>{new Date(item.started_at).toLocaleString("pl-PL")}</td><td>{item.trade_count}</td><td>{money(item.profit_abs)} ({percent(item.profit_pct)})</td><td>{percent(item.max_drawdown)}</td><td><button type="button" disabled={pending} onClick={() => openExperiment(item.experiment_id)} aria-label={`Otwórz eksperyment ${item.experiment_id}`}>Otwórz</button></td></tr>)}
        </tbody></table></div>
      </article>

      {selected ? <ExperimentView bundle={selected} /> : <article className="panel"><div className="empty-state"><strong>Brak wyników</strong><span>Uruchom pierwszy test na dostępnym zbiorze badawczym.</span></div></article>}

      <article className="panel" data-testid="strategy-comparison">
        <h2>Porównanie wariantów</h2>
        <div className="form-grid">
          <label>Bazowa<select value={baselineId} onChange={(event) => setBaselineId(event.target.value)}>{experiments.map((item) => <option key={item.experiment_id} value={item.experiment_id}>{item.strategy_id} · {item.experiment_id.slice(0, 8)}</option>)}</select></label>
          <label>Wariant<select value={variantId} onChange={(event) => setVariantId(event.target.value)}>{experiments.map((item) => <option key={item.experiment_id} value={item.experiment_id}>{item.strategy_id} · {item.experiment_id.slice(0, 8)}</option>)}</select></label>
        </div>
        <button type="button" disabled={pending || !baselineId || !variantId} onClick={runComparison}>Porównaj</button>
        {comparison ? <div className="table-wrap"><table><thead><tr><th>Metryka</th><th>Różnica</th></tr></thead><tbody>{Object.entries(comparison.metric_deltas).map(([name, value]) => <tr key={name}><td>{name}</td><td>{name.includes("rate") || name.includes("pct") || name.includes("drawdown") ? percent(value) : value}</td></tr>)}</tbody></table><h3>Zmiany parametrów</h3><pre>{JSON.stringify(comparison.parameter_differences, null, 2)}</pre></div> : null}
      </article>
    </section>
  );
}

function ExperimentView({ bundle }: { bundle: ExperimentBundle }) {
  const value = bundle.detail;
  const equities = bundle.equity.map((point) => number(point.equity));
  const minimum = equities.length > 0 ? Math.min(...equities) : 0;
  const maximum = equities.length > 0 ? Math.max(...equities) : 1;
  const range = Math.max(1, maximum - minimum);
  const equityPath = bundle.equity
    .map(
      (point, index) =>
        `${index === 0 ? "M" : "L"} ${(index / Math.max(1, bundle.equity.length - 1)) * 100} ${90 - ((number(point.equity) - minimum) / range) * 80}`,
    )
    .join(" ");
  const signalPrices = bundle.signals.map((signal) => number(signal.price));
  const minPrice = signalPrices.length > 0 ? Math.min(...signalPrices) : 0;
  const maxPrice = signalPrices.length > 0 ? Math.max(...signalPrices) : 1;
  const priceRange = Math.max(1, maxPrice - minPrice);
  return <>
    <article className="panel" data-testid="experiment-detail" data-experiment-id={value.experiment_id}><h2>Szczegóły eksperymentu</h2><div className="metric-grid"><div><span>Wynik</span><strong>{money(value.profit_abs)}</strong><small>{percent(value.profit_pct)}</small></div><div><span>Win rate</span><strong>{percent(value.win_rate)}</strong><small>{value.wins}W / {value.losses}L</small></div><div><span>Max drawdown</span><strong>{percent(value.max_drawdown)}</strong></div><div><span>Transakcje</span><strong>{value.trade_count}</strong><small>Ekspozycja {percent(value.exposure)}</small></div></div><h3>Parametry</h3><pre>{JSON.stringify(value.parameters, null, 2)}</pre></article>
    <article className="panel"><h2>Equity curve</h2><svg viewBox="0 0 100 100" role="img" aria-label="Equity curve" style={{ width: "100%", minHeight: 220 }}><path d={equityPath} fill="none" stroke="currentColor" strokeWidth="1.5" /></svg></article>
    <article className="panel" data-testid="signal-chart"><h2>Wejścia i wyjścia</h2><svg viewBox="0 0 100 100" role="img" aria-label="Signal entry and exit chart" style={{ width: "100%", minHeight: 220 }}>{bundle.signals.map((signal, index) => { const x = 10 + (index / Math.max(1, bundle.signals.length - 1)) * 80; const y = 90 - ((number(signal.price) - minPrice) / priceRange) * 80; return <g key={signal.signal_id}><circle cx={x} cy={y} r="4" fill={signal.decision === "ENTER_LONG" ? "currentColor" : "none"} stroke="currentColor" /><text x={x} y={Math.max(8, y - 7)} textAnchor="middle" fontSize="4">{signal.decision === "ENTER_LONG" ? "ENTRY" : "EXIT"}</text></g>; })}</svg></article>
    <article className="panel"><h2>Transakcje</h2><div className="table-wrap"><table><thead><tr><th>Wejście</th><th>Wyjście</th><th>Ceny</th><th>Wynik</th><th>Uzasadnienie</th></tr></thead><tbody>{bundle.trades.map((trade) => <tr key={trade.trade_id}><td>{new Date(trade.entry_at).toLocaleString("pl-PL")}</td><td>{new Date(trade.exit_at).toLocaleString("pl-PL")}</td><td>{trade.entry_price} → {trade.exit_price}</td><td>{money(trade.profit_abs)} ({percent(trade.profit_pct)})</td><td>{[...trade.entry_reason_codes, ...trade.exit_reason_codes].join(", ")}</td></tr>)}</tbody></table></div></article>
    <article className="panel"><h2>Uzasadnienie sygnałów</h2><div className="table-wrap"><table><thead><tr><th>Czas</th><th>Decyzja</th><th>Warunki</th><th>Reason codes</th><th>Cechy</th></tr></thead><tbody>{bundle.signals.map((signal) => <tr key={signal.signal_id}><td>{new Date(signal.timestamp).toLocaleString("pl-PL")}</td><td><StatusPill value={signal.decision} /></td><td>{signal.matched_conditions.join(", ")}</td><td>{signal.reason_codes.join(", ")}</td><td><code>{JSON.stringify(signal.feature_values)}</code></td></tr>)}</tbody></table></div></article>
  </>;
}
