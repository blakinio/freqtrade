import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listLearningHistory } from "@/lib/portal-api";

export default async function LearningHistoryPage() {
  const cookieHeader = (await cookies()).toString();
  const history = await listLearningHistory(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">AI Intelligence</span><h1>Learning History</h1></div>
        <span className="freshness">Insight → hypothesis → experiment → candidate</span>
      </div>
      {history.length === 0 ? (
        <article className="panel"><div className="empty-state"><strong>No learning history yet</strong><span>Negative and inconclusive experiments remain durable when the workflow begins producing evidence.</span></div></article>
      ) : (
        <div className="surface-grid">
          {history.map((entry) => (
            <article className="panel surface-card" key={entry.hypothesis.hypothesis_id}>
              <div className="panel-heading">
                <div><span className="eyebrow">Hypothesis</span><h2>{entry.hypothesis.statement}</h2></div>
              </div>
              <p className="freshness">Source insight {entry.hypothesis.source_insight_id}</p>
              <div className="detail-grid">
                <div><span>Experiments</span><strong>{entry.experiments.length}</strong></div>
                <div><span>Candidates</span><strong>{entry.candidates.length}</strong></div>
                <div><span>Promoted</span><strong>{entry.candidates.filter((candidate) => candidate.promoted).length}</strong></div>
                <div><span>Assigned</span><strong>{entry.candidates.filter((candidate) => candidate.assigned_to_bot).length}</strong></div>
              </div>
              {entry.experiments.map((experiment) => (
                <div className="timeline-entry" key={experiment.experiment_id}>
                  <div>
                    <strong>{experiment.result_summary}</strong>
                    <span>{experiment.experiment_id}</span>
                  </div>
                  <StatusPill value={experiment.outcome} />
                </div>
              ))}
              {entry.candidates.map((candidate) => (
                <div className="timeline-entry" key={candidate.candidate_id}>
                  <div>
                    <strong>{candidate.candidate_model_version_id}</strong>
                    <span>{candidate.model_family_id} · {candidate.autonomy_level}</span>
                  </div>
                  <StatusPill value={candidate.promoted ? "PROMOTED" : "UNPROMOTED"} />
                </div>
              ))}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
