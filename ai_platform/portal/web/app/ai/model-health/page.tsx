import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listModelHealth } from "@/lib/product-api";

function valueOrUnavailable(value: string | null): string {
  return value ?? "Unavailable";
}

export default async function ModelHealthPage() {
  const cookieHeader = (await cookies()).toString();
  const models = await listModelHealth(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">AI Intelligence</span><h1>Model Health</h1></div>
        <span className="freshness">Aggregate inference telemetry · PSI-v1 evidence</span>
      </div>
      <div className="status-banner status-info">
        <strong>Measured evidence only</strong>
        <span>Health uses tenant-scoped aggregate windows attributed to the exact model, feature schema, bot configuration and runtime. It cannot promote, retrain or mutate a model.</span>
      </div>
      <article className="panel">
        {models.length === 0 ? (
<div className="empty-state"><strong>No model versions available</strong><span>Model health cannot be represented without registered immutable model metadata.</span></div>
        ) : (
<div className="table-wrap">
  <table>
    <thead><tr><th>Model / scope</th><th>Lifecycle</th><th>Drift</th><th>Windows</th><th>Samples</th><th>PSI / quality</th><th>Source</th></tr></thead>
    <tbody>
      {models.map((model) => (
        <tr key={model.health_record_id}>
          <td><strong>{model.model_version_id}</strong><span>{model.model_family_id}</span><span>{valueOrUnavailable(model.bot_id)} · {valueOrUnavailable(model.runtime_id)}</span><span>{valueOrUnavailable(model.feature_schema_version_id)}</span></td>
          <td><StatusPill value={model.lifecycle_state} /><span>{model.metadata_age_days} metadata days</span></td>
          <td><StatusPill value={model.drift_status} /><span>{model.drift_reason}</span><span>{valueOrUnavailable(model.policy_version)}</span></td>
          <td><span>Ref: {valueOrUnavailable(model.reference_window_id)}</span><span>Obs: {valueOrUnavailable(model.observation_window_id)}</span></td>
          <td><span>{model.reference_sample_count} reference</span><span>{model.observation_sample_count} observed</span><span>{model.accepted_predictions} accepted · {model.rejected_predictions} rejected</span></td>
          <td><span>Prediction: {valueOrUnavailable(model.prediction_drift_score)}</span><span>Feature: {valueOrUnavailable(model.max_feature_drift_score)} ({valueOrUnavailable(model.worst_feature_name)})</span><span>Quality issue rate: {valueOrUnavailable(model.max_feature_quality_issue_rate)}</span></td>
          <td><StatusPill value={model.source_availability} /><span>{valueOrUnavailable(model.source_id)}</span><span>{model.source_checked_at ? new Date(model.source_checked_at).toLocaleString() : "Not checked"}</span></td>
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
