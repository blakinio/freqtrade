import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listBots } from "@/lib/portal-api";

export default async function ExchangeConnectionsPage() {
  const cookieHeader = (await cookies()).toString();
  const bots = await listBots(cookieHeader);
  const connections = Array.from(new Set(bots.map((bot) => bot.spec.exchange_connection_ref))).map((ref) => ({
    ref,
    botCount: bots.filter((bot) => bot.spec.exchange_connection_ref === ref).length,
    modes: Array.from(new Set(bots.filter((bot) => bot.spec.exchange_connection_ref === ref).map((bot) => bot.spec.execution_mode))),
  }));

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Platform</span><h1>Exchange Connections</h1></div>
        <span className="freshness">Opaque references only</span>
      </div>
      <div className="status-banner status-info">
        <strong>Secret boundary preserved</strong>
        <span>The browser receives only opaque exchange connection references already attached to bot configurations. API keys, passphrases and secret references are never rendered here.</span>
      </div>
      <article className="panel">
        {connections.length === 0 ? (
          <div className="empty-state"><strong>No exchange metadata in use</strong><span>Credential creation remains behind the dedicated secret-management boundary.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Connection reference</th><th>Bots</th><th>Execution modes</th><th>Credential visibility</th></tr></thead>
              <tbody>
                {connections.map((connection) => (
                  <tr key={connection.ref}>
                    <td><strong>{connection.ref}</strong><span>Opaque tenant-scoped reference</span></td>
                    <td>{connection.botCount}</td>
                    <td>{connection.modes.map((mode) => <StatusPill key={mode} value={mode} />)}</td>
                    <td>Hidden</td>
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
