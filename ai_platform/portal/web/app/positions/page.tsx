import { cookies } from "next/headers";

import { listBots, listPositions } from "@/lib/portal-api";

export default async function PositionsPage() {
  const cookieHeader = (await cookies()).toString();
  const [positions, bots] = await Promise.all([
    listPositions(cookieHeader),
    listBots(cookieHeader),
  ]);
  const botNames = new Map(bots.map((bot) => [bot.bot_id, bot.name]));

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Overview</span><h1>Open Positions</h1></div>
        <span className="freshness">Normalized operational evidence</span>
      </div>
      <div className="status-banner status-info">
        <strong>Private execution boundary preserved</strong>
        <span>This view reads the portal operational mirror. It does not query Freqtrade directly from the browser or weaken the fail-closed runtime adapter.</span>
      </div>
      <article className="panel">
        {positions.length === 0 ? (
          <div className="empty-state"><strong>No open positions</strong><span>No normalized open-position evidence exists for this tenant.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Position</th><th>Bot</th><th>Pair</th><th>Side</th><th>Amount</th><th>Opened</th><th>Runtime</th></tr></thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={position.position_id}>
                    <td><strong>{position.position_id}</strong></td>
                    <td><strong>{botNames.get(position.bot_id) ?? position.bot_id}</strong><span>{position.bot_id}</span></td>
                    <td>{position.pair}</td>
                    <td>{position.side}</td>
                    <td>{position.amount}</td>
                    <td>{new Date(position.opened_at).toLocaleString()}</td>
                    <td>{position.source_runtime_id}</td>
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
