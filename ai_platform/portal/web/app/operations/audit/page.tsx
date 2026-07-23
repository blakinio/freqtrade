import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listAuditEvents } from "@/lib/portal-api";

export default async function AuditEventsPage() {
  const cookieHeader = (await cookies()).toString();
  const events = await listAuditEvents(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Operations</span><h1>Audit Events</h1></div>
        <span className="freshness">AUDIT_READ required server-side</span>
      </div>
      <div className="status-banner status-info">
        <strong>Authorization is enforced by the control plane</strong>
        <span>Navigation visibility does not grant audit access. The API requires the trusted identity context to include AUDIT_READ.</span>
      </div>
      <article className="panel">
        {events.length === 0 ? (
          <div className="empty-state"><strong>No audit events available</strong><span>No tenant-scoped audit evidence is visible to the current authorized identity.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Resource</th><th>Result</th><th>Correlation</th><th>Reason</th></tr></thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.audit_id}>
                    <td>{new Date(event.occurred_at).toLocaleString()}</td>
                    <td><strong>{event.actor_id}</strong><span>{event.actor_type}</span></td>
                    <td>{event.action}</td>
                    <td><strong>{event.resource_type}</strong><span>{event.resource_id}</span></td>
                    <td><StatusPill value={event.result} /></td>
                    <td>{event.correlation_id}</td>
                    <td>{event.reason_code ?? "—"}</td>
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
