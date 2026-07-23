import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listBots } from "@/lib/portal-api";

export default async function RuntimeHealthPage() {
  const cookieHeader = (await cookies()).toString();
  const bots = await listBots(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Operations</span><h1>Runtime Health</h1></div>
        <span className="freshness">Desired vs observed state</span>
      </div>
      <div className="status-banner status-info">
        <strong>Private runtime view</strong>
        <span>Only portal-owned runtime identity and health state are rendered. Private hostnames, Freqtrade credentials and container addresses remain server-side.</span>
      </div>
      <article className="panel">
        {bots.length === 0 ? (
          <div className="empty-state"><strong>No runtimes represented</strong><span>Create a dry-run bot before runtime state can be reconciled.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Bot</th><th>Desired</th><th>Observed</th><th>Runtime version</th><th>Config revision</th><th>Environment</th></tr></thead>
              <tbody>
                {bots.map((bot) => (
                  <tr key={bot.bot_id}>
                    <td><strong>{bot.name}</strong><span>{bot.bot_id}</span></td>
                    <td><StatusPill value={bot.desired_state} /></td>
                    <td><StatusPill value={bot.observed_state} /></td>
                    <td>{bot.spec.runtime_version}</td>
                    <td>{bot.spec.config_revision}</td>
                    <td><StatusPill value={bot.spec.environment} /></td>
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
