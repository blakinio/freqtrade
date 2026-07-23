import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listInsights, listLearningHistory, listModels, listTradeAnalyses } from "@/lib/portal-api";

export default async function AiOverviewPage() {
  const cookieHeader = (await cookies()).toString();
  const [models, analyses, insights, history] = await Promise.all([
    listModels(cookieHeader),
    listTradeAnalyses(cookieHeader),
    listInsights(cookieHeader),
    listLearningHistory(cookieHeader),
  ]);
  const candidates = history.flatMap((entry) => entry.candidates);
  const attentionInsights = insights.filter((insight) => insight.severity !== "INFO");

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">AI Intelligence</span><h1>AI Overview</h1></div>
        <span className="freshness">Immutable read models</span>
      </div>
      <div className="metric-grid">
        <article className="metric-card"><span>Model versions</span><strong>{models.length}</strong></article>
        <article className="metric-card"><span>Trade analyses</span><strong>{analyses.length}</strong></article>
        <article className="metric-card"><span>Attention insights</span><strong>{attentionInsights.length}</strong></article>
        <article className="metric-card"><span>Learning hypotheses</span><strong>{history.length}</strong></article>
        <article className="metric-card"><span>Unpromoted candidates</span><strong>{candidates.filter((item) => !item.promoted).length}</strong></article>
      </div>
      <div className="surface-grid">
        <article className="panel">
          <div className="panel-heading"><div><span className="eyebrow">Models</span><h2>Lifecycle state</h2></div></div>
          {models.length === 0 ? (
            <div className="empty-state"><strong>No model metadata available</strong><span>Register tenant-scoped model metadata before assigning it to bot revisions.</span></div>
          ) : (
            <div className="bot-list">
              {models.slice(0, 6).map((model) => (
                <div className="bot-row" key={model.model_version_id}>
                  <div><strong>{model.model_version_id}</strong><span>{model.model_family_id} · {model.feature_schema_version_id}</span></div>
                  <StatusPill value={model.lifecycle_state} />
                </div>
              ))}
            </div>
          )}
        </article>
        <article className="panel">
          <div className="panel-heading"><div><span className="eyebrow">Insights</span><h2>Latest evidence</h2></div></div>
          {insights.length === 0 ? (
            <div className="empty-state"><strong>No insights yet</strong><span>Post-trade analysis creates attributable insights without changing active models.</span></div>
          ) : (
            <div className="bot-list">
              {insights.slice(0, 6).map((insight) => (
                <div className="bot-row" key={insight.insight_id}>
                  <div><strong>{insight.summary}</strong><span>{insight.synthesis_source} · {new Date(insight.created_at).toLocaleString()}</span></div>
                  <StatusPill value={insight.severity} />
                </div>
              ))}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
