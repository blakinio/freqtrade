import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listBots, listTrades } from "@/lib/portal-api";

export default async function TradesPage() {
  const cookieHeader = (await cookies()).toString();
  const [trades, bots] = await Promise.all([
    listTrades(cookieHeader),
    listBots(cookieHeader),
  ]);
  const botNames = new Map(bots.map((bot) => [bot.bot_id, bot.name]));

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Trading</span><h1>Trade History</h1></div>
        <span className="freshness">Persisted trade outcome evidence</span>
      </div>
      <article className="panel">
        {trades.length === 0 ? (
          <div className="empty-state"><strong>No completed trades available</strong><span>Trade history appears after a normalized outcome is persisted and linked to attributable decision evidence.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Trade</th><th>Bot</th><th>Pair / side</th><th>Amount</th><th>Realized PNL</th><th>Fees</th><th>Exit</th><th>Reconciliation</th><th>Closed</th></tr></thead>
              <tbody>
                {trades.map((trade) => (
                  <tr key={trade.trade_id}>
                    <td><strong>{trade.trade_id}</strong><span>analysis {trade.analysis_id}</span></td>
                    <td><strong>{botNames.get(trade.bot_id) ?? trade.bot_id}</strong><span>{trade.source_runtime_id}</span></td>
                    <td><strong>{trade.pair}</strong><span>{trade.side}</span></td>
                    <td>{trade.amount}</td>
                    <td><strong>{trade.realized_pnl}</strong></td>
                    <td>{trade.fees}</td>
                    <td>{trade.exit_reason}</td>
                    <td><StatusPill value={trade.reconciliation_status} /></td>
                    <td>{new Date(trade.closed_at).toLocaleString()}</td>
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
