import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { dashboardSnapshot } from "@/lib/portal-api";

export default async function DashboardPage() {
  const cookieHeader = (await cookies()).toString();
  const snapshot = await dashboardSnapshot(cookieHeader);
  const cards = [
    ["Active bots", String(snapshot.activeBots)],
    ["Needs attention", String(snapshot.attentionBots)],
    ["Runtime health", snapshot.runtimeHealth],
    ["Model health", snapshot.modelHealth],
    ["Risk status", snapshot.riskStatus],
  ];
  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Overview</span><h1>Dashboard</h1></div>
        <span className="freshness">{snapshot.freshnessLabel}</span>
      </div>
      <div className="metric-grid">
        {cards.map(([label, value]) => (
          <article className="metric-card" key={label}><span>{label}</span><strong>{value}</strong></article>
        ))}
      </div>
      <article className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Operations</span><h2>Bot status</h2></div></div>
        {snapshot.bots.length === 0 ? (
          <div className="empty-state"><strong>No bots yet</strong><span>Create a dry-run bot to start validating the platform.</span></div>
        ) : (
          <div className="bot-list">
            {snapshot.bots.slice(0, 4).map((bot) => (
              <div className="bot-row" key={bot.bot_id}>
                <div><strong>{bot.name}</strong><span>{bot.spec.strategy_version} · {bot.spec.model_version}</span></div>
                <StatusPill value={bot.observed_state} />
              </div>
            ))}
          </div>
        )}
      </article>
    </section>
  );
}
