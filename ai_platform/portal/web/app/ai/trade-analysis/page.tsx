import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listTradeAnalyses } from "@/lib/portal-api";

export default async function TradeAnalysisPage() {
  const cookieHeader = (await cookies()).toString();
  const analyses = await listTradeAnalyses(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">AI Intelligence</span><h1>Trade Analysis</h1></div>
        <span className="freshness">Decision evidence separated from outcome</span>
      </div>
      <article className="panel">
        {analyses.length === 0 ? (
          <div className="empty-state"><strong>No trade analyses available</strong><span>Analyses appear only after attributable decision snapshots and reconciled trade outcomes are recorded.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Trade</th><th>Bot / pair</th><th>Decision</th><th>Outcome</th><th>Diagnosis</th><th>Evidence</th></tr></thead>
              <tbody>
                {analyses.map((analysis) => (
                  <tr key={analysis.analysis_id}>
                    <td><strong>{analysis.outcome.trade_id}</strong><span>{new Date(analysis.created_at).toLocaleString()}</span></td>
                    <td><strong>{analysis.snapshot.bot_id}</strong><span>{analysis.snapshot.pair} · {analysis.snapshot.side}</span></td>
                    <td><strong>{analysis.snapshot.model_version}</strong><span>{analysis.snapshot.risk_policy_version}</span></td>
                    <td><strong>{analysis.outcome.realized_pnl}</strong><span>{analysis.outcome.exit_reason} · fees {analysis.outcome.fees}</span></td>
                    <td><StatusPill value={analysis.diagnosis.code} /></td>
                    <td><strong>{analysis.outcome.reconciliation_status}</strong><span>{analysis.diagnosis.reason_codes.join(", ")}</span></td>
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
