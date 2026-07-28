import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import {
  dashboardSnapshot,
  type DashboardEvidenceSource,
} from "@/lib/dashboard-api";

export default async function DashboardPage() {
  const cookieHeader = (await cookies()).toString();
  const snapshot = await dashboardSnapshot(cookieHeader);
  const sourceState = (source: DashboardEvidenceSource) =>
    snapshot.source_statuses.find((status) => status.source === source)?.state ?? "UNAVAILABLE";
  const cards = [
    ["Active bots", String(snapshot.totals.active_bot_count)],
    ["Needs attention", String(snapshot.totals.attention_bot_count)],
    ["Runtime evidence", sourceState("RUNTIME")],
    ["Model evidence", sourceState("MODEL")],
    ["Risk evidence", sourceState("RISK")],
  ];
  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Overview</span>
          <h1>Dashboard</h1>
        </div>
        <span className="freshness">
          Schema v{snapshot.schema_version} · generated {snapshot.generated_at}
        </span>
      </div>
      <div className="metric-grid">
        {cards.map(([label, value]) => (
          <article className="metric-card" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </div>
      <article className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Operations</span>
            <h2>Bot evidence</h2>
          </div>
        </div>
        {snapshot.items.length === 0 ? (
          <div className="empty-state">
            <strong>No bots match this environment</strong>
            <span>The authoritative dashboard returned an empty tenant-scoped result.</span>
          </div>
        ) : (
          <div className="bot-list">
            {snapshot.items.slice(0, 4).map((bot) => (
              <div className="bot-row" key={bot.bot_id}>
                <div>
                  <strong>{bot.name}</strong>
                  <span>
                    {bot.strategy_version} · {bot.model_version} · runtime {bot.evidence.runtime.state}
                  </span>
                </div>
                <StatusPill value={bot.observed_state} />
              </div>
            ))}
          </div>
        )}
      </article>
    </section>
  );
}
