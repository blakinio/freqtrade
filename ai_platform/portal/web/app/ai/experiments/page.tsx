import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listLearningHistory } from "@/lib/portal-api";

export default async function ExperimentsPage() {
  const cookieHeader = (await cookies()).toString();
  const history = await listLearningHistory(cookieHeader);
  const experiments = history.flatMap((entry) => entry.experiments);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">AI Intelligence</span><h1>Experiments</h1></div>
        <span className="freshness">Bounded research history</span>
      </div>
      <div className="status-banner status-info">
        <strong>Candidate creation is not promotion</strong>
        <span>Experiments and candidates are research provenance. Active model assignment changes only through the separately authorized model-control workflow.</span>
      </div>
      <article className="panel">
        {experiments.length === 0 ? (
          <div className="empty-state"><strong>No experiments recorded</strong><span>Validated insights may create bounded hypotheses and experiments without changing the active model.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Experiment</th><th>Hypothesis</th><th>Window</th><th>Autonomy</th><th>Outcome</th><th>Result</th></tr></thead>
              <tbody>
                {experiments.map((experiment) => (
                  <tr key={experiment.experiment_id}>
                    <td><strong>{experiment.experiment_id}</strong><span>{new Date(experiment.created_at).toLocaleString()}</span></td>
                    <td>{experiment.hypothesis_id}</td>
                    <td><strong>{new Date(experiment.evidence_window.start_at).toLocaleDateString()}</strong><span>to {new Date(experiment.evidence_window.end_at).toLocaleDateString()}</span></td>
                    <td><StatusPill value={experiment.autonomy_level} /></td>
                    <td><StatusPill value={experiment.outcome} /></td>
                    <td>{experiment.result_summary}</td>
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
