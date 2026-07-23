import { cookies } from "next/headers";

import { listSignals } from "@/lib/product-api";

export default async function SignalLogsPage() {
  const cookieHeader = (await cookies()).toString();
  const signals = await listSignals(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Operations</span><h1>Signal Logs</h1></div>
        <span className="freshness">Tenant-scoped persisted signal evidence</span>
      </div>
      <div className="status-banner status-info">
        <strong>Evidence boundary</strong>
        <span>These records are advisory signal events. They are not TradeIntents and do not prove that an order was submitted.</span>
      </div>
      <article className="panel">
        {signals.length === 0 ? (
          <div className="empty-state"><strong>No signal evidence</strong><span>No canonical signal events exist for this tenant.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Occurred</th><th>Signal</th><th>Bot</th><th>Pair</th><th>Side</th><th>Confidence</th><th>Source</th><th>Rationale</th></tr></thead>
              <tbody>{signals.map((signal) => (
                <tr key={signal.signal_id}>
                  <td>{new Date(signal.occurred_at).toLocaleString()}</td>
                  <td>{signal.signal_id}</td>
                  <td>{signal.bot_id}</td>
                  <td><strong>{signal.pair}</strong><span>{signal.timeframe}</span></td>
                  <td>{signal.side}</td>
                  <td>{signal.confidence}</td>
                  <td>{signal.source}</td>
                  <td>{signal.rationale}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
