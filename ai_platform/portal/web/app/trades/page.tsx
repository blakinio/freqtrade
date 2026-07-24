import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listBots } from "@/lib/portal-api";
import { aggregateFreshness, runtimeEvidence, sourceStatusFor } from "@/lib/runtime-evidence";

export default async function TradesPage() {
  const cookieHeader = (await cookies()).toString();
  const [evidence, bots] = await Promise.all([
    runtimeEvidence(cookieHeader),
    listBots(cookieHeader),
  ]);
  const trades = evidence.trades;
  const statuses = sourceStatusFor(evidence, "TRADES");
  const freshness = aggregateFreshness(statuses);
  const unavailable = freshness === "SOURCE_UNAVAILABLE" || freshness === "UNAVAILABLE";
  const botNames = new Map(bots.map((bot) => [bot.bot_id, bot.name]));

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Trading</span><h1>Trade History</h1></div>
        <span className="freshness">Runtime evidence · {freshness}</span>
      </div>
      <article className="panel">
        {trades.length === 0 ? (
          <div className="empty-state">
            <strong>{unavailable ? "Trade source unavailable" : "No trades available"}</strong>
            <span>
              {unavailable
                ? "The private runtime source is unavailable or incomplete; the portal does not present a fabricated current history."
                : "A complete authoritative runtime read found no trades for this tenant."}
            </span>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Trade</th><th>Bot</th><th>Pair / side</th><th>State</th><th>Amount</th><th>Realized PNL</th><th>Fees</th><th>Exit</th><th>Freshness</th><th>Reconciliation</th><th>Closed</th></tr></thead>
              <tbody>
                {trades.map((trade) => (
                  <tr key={trade.trade_id}>
                    <td>
                      <strong>{trade.source_trade_id}</strong>
                      {trade.trade_id !== trade.source_trade_id ? <span>{trade.trade_id}</span> : null}
                    </td>
                    <td><strong>{botNames.get(trade.bot_id) ?? trade.bot_id}</strong><span>{trade.source_runtime_id}</span></td>
                    <td><strong>{trade.pair}</strong><span>{trade.side}</span></td>
                    <td><StatusPill value={trade.state} /></td>
                    <td>{trade.amount}</td>
                    <td><strong>{trade.realized_pnl ?? "unavailable"}</strong></td>
                    <td>{trade.fees ?? "unavailable"}</td>
                    <td>{trade.exit_reason ?? "unavailable"}</td>
                    <td><StatusPill value={trade.freshness} /></td>
                    <td><StatusPill value={trade.reconciliation_status} /></td>
                    <td>{trade.closed_at ? new Date(trade.closed_at).toLocaleString() : "open"}</td>
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
