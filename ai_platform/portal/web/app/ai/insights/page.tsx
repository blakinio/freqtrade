import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listInsights } from "@/lib/portal-api";

export default async function InsightsPage() {
  const cookieHeader = (await cookies()).toString();
  const insights = await listInsights(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">AI Intelligence</span><h1>Insights</h1></div>
        <span className="freshness">Evidence-linked observations</span>
      </div>
      {insights.length === 0 ? (
        <article className="panel"><div className="empty-state"><strong>No insights yet</strong><span>Insights are append-only analysis outputs and never mutate running bots or active model assignments.</span></div></article>
      ) : (
        <div className="surface-grid">
          {insights.map((insight) => (
            <article className="panel surface-card" key={insight.insight_id}>
              <div className="panel-heading">
                <div><span className="eyebrow">{insight.synthesis_source}</span><h2>{insight.summary}</h2></div>
                <StatusPill value={insight.severity} />
              </div>
              <p className="freshness">Created {new Date(insight.created_at).toLocaleString()}</p>
              <div>
                <strong>Evidence links</strong>
                <ul className="capability-list">
                  {insight.evidence_links.map((link) => <li key={link}>{link}</li>)}
                </ul>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
