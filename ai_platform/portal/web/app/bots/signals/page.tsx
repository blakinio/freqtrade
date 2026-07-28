import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import {
  loadSignalControlOverview,
  type SignalControlOverview,
} from "@/lib/signal-control";

export default async function SignalWizardPage() {
  const cookieHeader = (await cookies()).toString();
  let overview: SignalControlOverview | null = null;

  try {
    overview = await loadSignalControlOverview(cookieHeader);
  } catch {
    overview = null;
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Bots</span><h1>Signal Control</h1></div>
        <span className="freshness">BM-04 signed endpoint readiness</span>
      </div>
      {overview === null ? (
        <div className="status-banner status-warning" role="alert">
          <strong>Signal control source unavailable</strong>
          <span>The portal fails closed and does not fall back to unsigned advisory submission.</span>
        </div>
      ) : (
        <>
          <div
            className={`status-banner ${overview.authentication_provider_status === "AVAILABLE" ? "status-info" : "status-warning"}`}
            role="status"
          >
            <strong>Authentication provider: {overview.authentication_provider_status}</strong>
            <span>
              Accepted processing: {overview.accepted_signal_processing_enabled ? "enabled" : "blocked"} · Execution submission: no.
              PI-07 must provide a reviewed secret backend and verifier before signed acceptance can be enabled.
            </span>
          </div>
          <article className="panel">
            <div className="panel-heading">
              <div><span className="eyebrow">Tenant endpoints</span><h2>Public endpoint metadata</h2></div>
            </div>
            {overview.endpoints.length === 0 ? (
              <div className="empty-state">
                <strong>No signed endpoints available</strong>
                <span>Authentication references and webhook slugs are never reconstructed or exposed by this view.</span>
              </div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Endpoint</th><th>Schema</th><th>Commands</th><th>Authority</th><th>Status</th><th>Authentication material</th></tr>
                  </thead>
                  <tbody>
                    {overview.endpoints.map((endpoint) => (
                      <tr key={`${endpoint.endpoint_id}:${endpoint.revision}`}>
                        <td><strong>{endpoint.display_name}</strong><span>{endpoint.endpoint_id} · revision {endpoint.revision}</span></td>
                        <td>{endpoint.schema_id}@{endpoint.schema_revision}</td>
                        <td>{endpoint.supported_commands.join(", ")}</td>
                        <td>{endpoint.authority}</td>
                        <td><StatusPill value={endpoint.enabled ? "ENABLED" : "DISABLED"} /></td>
                        <td>{endpoint.authentication_reference_exposed || endpoint.webhook_slug_exposed ? "Rejected" : "Not exposed"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>
        </>
      )}
    </section>
  );
}
