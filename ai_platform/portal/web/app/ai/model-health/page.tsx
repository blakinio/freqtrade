import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listModelHealth } from "@/lib/product-api";

export default async function ModelHealthPage() {
  const cookieHeader = (await cookies()).toString();
  const models = await listModelHealth(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">AI Intelligence</span><h1>Model Health</h1></div>
        <span className="freshness">Lifecycle metadata · truthful telemetry availability</span>
      </div>
      <div className="status-banner status-info">
        <strong>Drift evidence is never inferred</strong>
        <span>Lifecycle and metadata age come from immutable ModelVersion records. Drift remains explicitly unavailable until a canonical telemetry source is connected.</span>
      </div>
      <article className="panel">
        {models.length === 0 ? (
          <div className="empty-state"><strong>No model versions available</strong><span>Model health cannot be represented without registered immutable model metadata.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Model</th><th>Family</th><th>Lifecycle</th><th>Metadata age</th><th>Training window end</th><th>Drift telemetry</th></tr></thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.model_version_id}>
                    <td><strong>{model.model_version_id}</strong><span>{new Date(model.created_at).toLocaleString()}</span></td>
                    <td>{model.model_family_id}</td>
                    <td><StatusPill value={model.lifecycle_state} /></td>
                    <td>{model.metadata_age_days} days</td>
                    <td>{new Date(model.training_window_end).toLocaleString()}</td>
                    <td><StatusPill value={model.drift_status} /><span>{model.drift_reason}</span></td>
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
