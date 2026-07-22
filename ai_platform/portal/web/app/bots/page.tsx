import { cookies } from "next/headers";
import Link from "next/link";

import { StatusPill } from "@/components/status-pill";
import { listBots } from "@/lib/portal-api";

export default async function BotsPage() {
  const cookieHeader = (await cookies()).toString();
  const bots = await listBots(cookieHeader);
  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Bots</span><h1>Bot fleet</h1></div>
        <Link className="primary-button link-button" href="/bots/new">Create Bot</Link>
      </div>
      <article className="panel">
        {bots.length === 0 ? (
          <div className="empty-state"><strong>No bots configured</strong><span>Create an immutable dry-run configuration to begin.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Bot</th><th>Desired</th><th>Observed</th><th>Strategy / model</th><th>Markets</th><th>Mode</th></tr></thead>
              <tbody>
                {bots.map((bot) => (
                  <tr key={bot.bot_id}>
                    <td><strong>{bot.name}</strong><span>{bot.bot_id}</span></td>
                    <td><StatusPill value={bot.desired_state} /></td>
                    <td><StatusPill value={bot.observed_state} /></td>
                    <td><strong>{bot.spec.strategy_version}</strong><span>{bot.spec.model_version}</span></td>
                    <td>{bot.spec.pair_universe.join(", ")}</td>
                    <td><StatusPill value={bot.spec.execution_mode} /></td>
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
