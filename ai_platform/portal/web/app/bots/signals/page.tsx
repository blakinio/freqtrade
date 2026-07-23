import { cookies } from "next/headers";

import { SignalWizardForm } from "@/components/signal-wizard-form";
import { listSignals } from "@/lib/product-api";
import { listBots } from "@/lib/portal-api";

export default async function SignalWizardPage() {
  const cookieHeader = (await cookies()).toString();
  const [bots, signals] = await Promise.all([listBots(cookieHeader), listSignals(cookieHeader)]);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Bots</span><h1>Signal Wizard</h1></div>
        <span className="freshness">Advisory signal evidence · no execution authority</span>
      </div>
      <article className="panel form-panel">
        <div className="panel-heading"><div><span className="eyebrow">Signal ingestion</span><h2>Record a reviewed signal</h2></div></div>
        <SignalWizardForm bots={bots} />
      </article>
      <article className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Recent evidence</span><h2>Recorded signals</h2></div></div>
        {signals.length === 0 ? (
          <div className="empty-state"><strong>No signals recorded</strong><span>API mode returns no placeholder rows when the tenant has no signal evidence.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Time</th><th>Bot</th><th>Market</th><th>Side</th><th>Confidence</th><th>Authority</th></tr></thead>
              <tbody>{signals.slice(0, 8).map((signal) => (
                <tr key={signal.signal_id}>
                  <td>{new Date(signal.occurred_at).toLocaleString()}</td>
                  <td>{signal.bot_id}</td>
                  <td><strong>{signal.pair}</strong><span>{signal.timeframe}</span></td>
                  <td>{signal.side}</td>
                  <td>{signal.confidence}</td>
                  <td>{signal.execution_authority ? "Execution" : "Advisory only"}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
