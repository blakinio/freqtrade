import { cookies } from "next/headers";

import { listBots, listPerformance } from "@/lib/portal-api";

export default async function PerformancePage() {
  const cookieHeader = (await cookies()).toString();
  const [performance, bots] = await Promise.all([
    listPerformance(cookieHeader),
    listBots(cookieHeader),
  ]);
  const botNames = new Map(bots.map((bot) => [bot.bot_id, bot.name]));

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Overview</span><h1>PNL &amp; Performance</h1></div>
        <span className="freshness">Realized, reconciled portal evidence</span>
      </div>
      <div className="status-banner status-info">
        <strong>Realized performance only</strong>
        <span>Values are aggregated from persisted trade outcomes. Unrealized PNL and direct runtime portfolio reads remain outside this read model.</span>
      </div>
      <article className="panel">
        {performance.length === 0 ? (
          <div className="empty-state"><strong>No realized performance available</strong><span>Performance appears after an attributable trade outcome is persisted and linked to trade analysis.</span></div>
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
    </section>
  );
}
