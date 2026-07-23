import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listRiskEvents } from "@/lib/portal-api";

export default async function RiskEventsPage() {
  const cookieHeader = (await cookies()).toString();
  const events = await listRiskEvents(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Operations</span><h1>Risk Events</h1></div>
        <span className="freshness">Persisted deterministic decisions</span>
      </div>
      <article className="panel">
        {events.length === 0 ? (
          <div className="empty-state"><strong>No risk decisions recorded</strong><span>Risk events appear after a tenant-scoped trade intent is evaluated by the deterministic risk engine.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Decision</th><th>Policy</th><th>Outcome</th><th>Reasons</th><th>Limits</th><th>Correlation</th><th>Occurred</th></tr></thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.risk_decision_id}>
                    <td><strong>{event.risk_decision_id}</strong><span>intent {event.trade_intent_id}</span></td>
                    <td>{event.risk_policy_version}</td>
                    <td><StatusPill value={event.decision} /></td>
                    <td>{event.reason_codes.join(", ")}</td>
                    <td>{event.evaluated_limits.filter((limit) => limit.passed).length}/{event.evaluated_limits.length} passed</td>
                    <td>{event.context.correlation_id}</td>
                    <td>{new Date(event.occurred_at).toLocaleString()}</td>
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
