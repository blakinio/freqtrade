import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import {
  getRuntimeObservabilityAvailability,
  searchRuntimeLogs,
} from "@/lib/product-api";
import { listExecutionActivity } from "@/lib/portal-api";

export default async function ExecutionLogsPage() {
  const cookieHeader = (await cookies()).toString();
  const [entries, sourceStatus] = await Promise.all([
    listExecutionActivity(cookieHeader),
    getRuntimeObservabilityAvailability(cookieHeader),
  ]);
  const endAt = new Date();
  const startAt = new Date(endAt.getTime() - 60 * 60 * 1000);
  const runtimeLogs =
    sourceStatus.availability === "AVAILABLE"
      ? await searchRuntimeLogs(
          {
            start_at: startAt.toISOString(),
            end_at: endAt.toISOString(),
            limit: 100,
          },
          cookieHeader,
        )
      : null;

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Operations</span>
          <h1>Execution Activity</h1>
        </div>
        <span className="freshness">Runtime telemetry and durable audit remain separate</span>
      </div>

      <div className="status-banner status-info">
        <strong>Raw runtime logs: {sourceStatus.availability.toLowerCase()}</strong>
        <span>
          {sourceStatus.availability === "AVAILABLE"
            ? `${sourceStatus.source_id} · logs ${sourceStatus.log_retention_days}d · traces ${sourceStatus.trace_retention_days}d · metrics ${sourceStatus.metric_retention_days}d`
            : `${sourceStatus.reason_code}. Durable execution-related audit evidence remains available independently.`}
        </span>
      </div>

      <article className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Operational telemetry</span>
            <h2>Runtime logs · last hour</h2>
          </div>
          <span className="freshness">Bounded to 100 tenant-scoped records</span>
        </div>
        {runtimeLogs === null || runtimeLogs.records.length === 0 ? (
          <div className="empty-state">
            <strong>No runtime log records available</strong>
            <span>
              The private source is unavailable or returned no records. This is not interpreted as
              successful or healthy execution.
            </span>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Level</th>
                  <th>Service</th>
                  <th>Runtime / Bot</th>
                  <th>Message</th>
                  <th>Correlation / Trace</th>
                </tr>
              </thead>
              <tbody>
                {runtimeLogs.records.map((record) => (
                  <tr key={record.record_id}>
                    <td>{new Date(record.timestamp).toLocaleString()}</td>
                    <td>
                      <StatusPill value={record.level} />
                    </td>
                    <td>
                      <strong>{record.service}</strong>
                      <span>{record.component}</span>
                    </td>
                    <td>
                      <strong>{record.runtime_id}</strong>
                      <span>{record.bot_id}</span>
                    </td>
                    <td>{record.message}</td>
                    <td>
                      <strong>{record.correlation_id}</strong>
                      <span>{record.trace_id ?? "No trace ID"}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      <article className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Durable evidence</span>
            <h2>Execution audit activity</h2>
          </div>
          <span className="freshness">Append-only business and security evidence</span>
        </div>
        {entries.length === 0 ? (
          <div className="empty-state">
            <strong>No execution activity available</strong>
            <span>
              No attributable execution-related audit events are visible to the current authorized
              identity.
            </span>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Action</th>
                  <th>Resource</th>
                  <th>Actor</th>
                  <th>Result</th>
                  <th>Correlation</th>
                  <th>Request</th>
                </tr>
              </thead>
              <tbody>
                {entries.map(({ audit }) => (
                  <tr key={audit.audit_id}>
                    <td>{new Date(audit.occurred_at).toLocaleString()}</td>
                    <td>{audit.action}</td>
                    <td>
                      <strong>{audit.resource_type}</strong>
                      <span>{audit.resource_id}</span>
                    </td>
                    <td>{audit.actor_id}</td>
                    <td>
                      <StatusPill value={audit.result} />
                    </td>
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
