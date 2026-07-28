import { cookies } from "next/headers";

import {
  loadGridControlOverview,
  type GridControlOverview,
} from "@/lib/grid-control";

export default async function GridBotsPage() {
  const cookieHeader = (await cookies()).toString();
  let overview: GridControlOverview | null = null;

  try {
    overview = await loadGridControlOverview(cookieHeader);
  } catch {
    overview = null;
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Bots</span><h1>Grid Control</h1></div>
        <span className="freshness">BM-05 canonical capability boundary</span>
      </div>
      {overview === null ? (
        <div className="status-banner status-warning" role="alert">
          <strong>Grid control source unavailable</strong>
          <span>The portal fails closed and does not fall back to browser-generated grid levels or capability evidence.</span>
        </div>
      ) : (
        <>
          <div
            className={`status-banner ${overview.capability_evidence_provider_status === "AVAILABLE" ? "status-info" : "status-warning"}`}
            role="status"
          >
            <strong>Capability evidence provider: {overview.capability_evidence_provider_status}</strong>
            <span>
              Canonical preview: {overview.canonical_preview_enabled ? "enabled" : "blocked"} · Policy persistence: {overview.policy_persistence_enabled ? "enabled" : "blocked"} · Execution submission: no.
            </span>
          </div>
          <article className="panel">
            <div className="panel-heading">
              <div><span className="eyebrow">Authoritative evidence</span><h2>Grid configuration readiness</h2></div>
            </div>
            <div className="definition-list">
              <div><dt>Browser capability evidence</dt><dd>{overview.browser_supplied_capability_evidence_accepted ? "Rejected boundary violation" : "Not accepted"}</dd></div>
              <div><dt>Canonical levels</dt><dd>{overview.canonical_preview_enabled ? "Server generated" : "Unavailable"}</dd></div>
              <div><dt>Runtime orders</dt><dd>Not submitted</dd></div>
            </div>
            {!overview.canonical_preview_enabled ? (
              <div className="empty-state">
                <strong>Trusted grid evidence is not configured</strong>
                <span>A reviewed server-side provider must resolve exact template, exchange profile, bot revision and config revision before preview or persistence can be enabled.</span>
              </div>
            ) : null}
          </article>
        </>
      )}
    </section>
  );
}
