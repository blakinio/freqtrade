import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listBots } from "@/lib/portal-api";
import { aggregateFreshness, runtimeEvidence, sourceStatusFor } from "@/lib/runtime-evidence";

export default async function PositionsPage() {
  const cookieHeader = (await cookies()).toString();
  const [evidence, bots] = await Promise.all([
    runtimeEvidence(cookieHeader),
    listBots(cookieHeader),
  ]);
  const positions = evidence.positions;
  const statuses = sourceStatusFor(evidence, "OPEN_POSITIONS");
  const freshness = aggregateFreshness(statuses);
  const botNames = new Map(bots.map((bot) => [bot.bot_id, bot.name]));
  const unavailable = freshness === "SOURCE_UNAVAILABLE" || freshness === "UNAVAILABLE";

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Overview</span><h1>Open Positions</h1></div>
        <span className="freshness">Runtime evidence · {freshness}</span>
      </div>
      <div className={`status-banner ${freshness === "CURRENT" ? "status-info" : "status-warning"}`}>
        <strong>Private execution boundary preserved</strong>
        <span>
          This view reads the portal operational mirror. Runtime freshness and reconciliation are
          explicit; the browser never receives a Freqtrade endpoint or credential.
        </span>
      </div>
      <article className="panel">
        {positions.length === 0 ? (
          <div className="empty-state">
            <strong>{unavailable ? "Position source unavailable" : "No open positions"}</strong>
            <span>
              {unavailable
                ? "The private runtime source is unavailable or has not reconciled; this is not presented as a confirmed empty portfolio."
                : "A complete authoritative runtime read found no open positions for this tenant."}
            </span>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Position</th><th>Bot</th><th>Pair</th><th>Side</th><th>Amount</th><th>Opened</th><th>Freshness</th><th>Reconciliation</th><th>Runtime</th></tr></thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={position.position_id}>
                    <td><strong>{position.source_position_id ?? position.position_id}</strong><span>{position.position_id}</span></td>
                    <td><strong>{botNames.get(position.bot_id) ?? position.bot_id}</strong><span>{position.bot_id}</span></td>
                    <td>{position.pair}</td>
                    <td>{position.side}</td>
                    <td>{position.amount}</td>
                    <td>{new Date(position.opened_at).toLocaleString()}</td>
                    <td><StatusPill value={position.freshness} /></td>
                    <td><StatusPill value={position.reconciliation_status} /></td>
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
