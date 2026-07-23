import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listModels } from "@/lib/portal-api";

export default async function ModelHealthPage() {
  const cookieHeader = (await cookies()).toString();
  const models = await listModels(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">AI Intelligence</span><h1>Model Health</h1></div>
        <span className="freshness">Lifecycle metadata · no execution authority</span>
      </div>
      <div className="status-banner status-info">
        <strong>Current health boundary</strong>
        <span>Lifecycle identity and training age are available now. Drift and inference-distribution telemetry remain unknown until their canonical observability read models are connected.</span>
      </div>
      <article className="panel">
        {models.length === 0 ? (
          <div className="empty-state"><strong>No model versions available</strong><span>Model health cannot be inferred without registered immutable model metadata.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Model</th><th>Family</th><th>Lifecycle</th><th>Feature schema</th><th>Dataset</th><th>Created</th></tr></thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.model_version_id}>
                    <td><strong>{model.model_version_id}</strong><span>{model.git_revision}</span></td>
                    <td>{model.model_family_id}</td>
                    <td><StatusPill value={model.lifecycle_state} /></td>
                    <td>{model.feature_schema_version_id}</td>
                    <td>{model.dataset_version_id}</td>
                    <td>{new Date(model.created_at).toLocaleString()}</td>
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
