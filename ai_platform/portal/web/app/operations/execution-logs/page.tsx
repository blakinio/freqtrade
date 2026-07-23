import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { getRuntimeLogAvailability } from "@/lib/product-api";
import { listExecutionActivity } from "@/lib/portal-api";

export default async function ExecutionLogsPage() {
  const cookieHeader = (await cookies()).toString();
  const [entries, runtimeLogs] = await Promise.all([
    listExecutionActivity(cookieHeader),
    getRuntimeLogAvailability(cookieHeader),
  ]);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Operations</span><h1>Execution Activity</h1></div>
        <span className="freshness">Audited correlation-aware activity</span>
      </div>
      <div className="status-banner status-info">
        <strong>Raw runtime logs: {runtimeLogs.available ? "available" : "unavailable"}</strong>
        <span>{runtimeLogs.available ? runtimeLogs.source : `${runtimeLogs.reason_code}. This surface therefore shows durable execution-related audit evidence only.`}</span>
      </div>
      <article className="panel">
        {entries.length === 0 ? (
          <div className="empty-state"><strong>No execution activity available</strong><span>No attributable execution-related audit events are visible to the current authorized identity.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Time</th><th>Action</th><th>Resource</th><th>Actor</th><th>Result</th><th>Correlation</th><th>Request</th></tr></thead>
              <tbody>
                {entries.map(({ audit }) => (
                  <tr key={audit.audit_id}>
                    <td>{new Date(audit.occurred_at).toLocaleString()}</td>
                    <td>{audit.action}</td>
                    <td><strong>{audit.resource_type}</strong><span>{audit.resource_id}</span></td>
                    <td>{audit.actor_id}</td>
                    <td><StatusPill value={audit.result} /></td>
                    <td>{audit.correlation_id}</td>
                    <td>{audit.request_id}</td>
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
