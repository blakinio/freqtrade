import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listBots, listPerformance } from "@/lib/portal-api";
import { listValuations } from "@/lib/valuation";

export default async function PerformancePage() {
  const cookieHeader = (await cookies()).toString();
  const [performance, valuations, bots] = await Promise.all([
    listPerformance(cookieHeader),
    listValuations(cookieHeader),
    listBots(cookieHeader),
  ]);
  const botNames = new Map(bots.map((bot) => [bot.bot_id, bot.name]));
  const currentValuations = valuations.filter((valuation) => valuation.state === "CURRENT");
  const unavailableCount = valuations.length - currentValuations.length;

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Overview</span><h1>PNL &amp; Performance</h1></div>
        <span className="freshness">Closed-trade evidence + private runtime marks</span>
      </div>
      <div className={`status-banner ${unavailableCount === 0 ? "status-info" : "status-warning"}`}>
        <strong>Authoritative valuation boundary</strong>
        <span>
          {currentValuations.length} open position(s) have current exact-runtime marks.
          {unavailableCount > 0
            ? ` ${unavailableCount} position(s) remain stale, unavailable or unpriced.`
            : ""}
          {" "}Realized PNL remains independent closed-trade evidence.
        </span>
      </div>
      <article className="panel">
        <div className="page-heading">
          <div><span className="eyebrow">Closed trades</span><h2>Realized performance</h2></div>
        </div>
        {performance.length === 0 ? (
          <div className="empty-state"><strong>No realized performance available</strong><span>Performance appears after an attributable closed-trade outcome is persisted.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Bot</th><th>Realized PNL</th><th>Fees</th><th>Net PNL</th><th>Trades</th><th>Win / loss</th><th>Reconciliation gaps</th></tr></thead>
              <tbody>
                {performance.map((row) => (
                  <tr key={row.bot_id}>
                    <td><strong>{botNames.get(row.bot_id) ?? row.bot_id}</strong><span>{row.bot_id}</span></td>
                    <td>{row.realized_pnl}</td>
                    <td>{row.fees}</td>
                    <td><strong>{row.net_pnl}</strong></td>
                    <td>{row.trade_count}</td>
                    <td>{row.winning_trades} / {row.losing_trades}</td>
                    <td>{row.reconciliation_gaps}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
      <article className="panel">
        <div className="page-heading">
          <div><span className="eyebrow">Open positions</span><h2>Open position valuation</h2></div>
          <span className="freshness">mark-to-entry-v1</span>
        </div>
        {valuations.length === 0 ? (
          <div className="empty-state"><strong>No open positions</strong><span>No tenant-scoped runtime positions require valuation.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Position</th><th>Bot</th><th>State</th><th>Amount</th><th>Entry</th><th>Mark</th><th>Market value</th><th>Unrealized PNL</th><th>Price evidence</th></tr></thead>
              <tbody>
                {valuations.map((valuation) => (
                  <tr key={valuation.valuation_id}>
                    <td><strong>{valuation.pair}</strong><span>{valuation.source_position_id ?? valuation.position_id}</span></td>
                    <td><strong>{botNames.get(valuation.bot_id) ?? valuation.bot_id}</strong><span>{valuation.source_runtime_id}</span></td>
                    <td><StatusPill value={valuation.state} /></td>
                    <td>{valuation.amount}</td>
                    <td>{valuation.entry_rate ?? "unavailable"}</td>
                    <td>{valuation.mark_rate ?? "unavailable"}</td>
                    <td>{valuation.market_value ?? "unavailable"} {valuation.valuation_currency ?? ""}</td>
                    <td><strong>{valuation.unrealized_pnl ?? "unavailable"}</strong></td>
                    <td>
                      <span>{valuation.source_price_id ?? valuation.reason_code ?? "unavailable"}</span>
                      <span>{valuation.source_observed_at ? new Date(valuation.source_observed_at).toLocaleString() : "no current timestamp"}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
