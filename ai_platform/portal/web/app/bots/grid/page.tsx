import { cookies } from "next/headers";

import { GridBotForm } from "@/components/grid-bot-form";
import { listGridBotConfigs } from "@/lib/product-api";
import { listBots } from "@/lib/portal-api";

export default async function GridBotsPage() {
  const cookieHeader = (await cookies()).toString();
  const [bots, configs] = await Promise.all([listBots(cookieHeader), listGridBotConfigs(cookieHeader)]);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Bots</span><h1>Grid Bots</h1></div>
        <span className="freshness">Dry-run configuration contract</span>
      </div>
      <article className="panel form-panel">
        <div className="panel-heading"><div><span className="eyebrow">Bounded strategy config</span><h2>Configure a grid dry-run bot</h2></div></div>
        <GridBotForm bots={bots} />
      </article>
      <article className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Persisted configs</span><h2>Grid configurations</h2></div></div>
        {configs.length === 0 ? (
          <div className="empty-state"><strong>No grid configurations</strong><span>No canonical dry-run grid config exists for this tenant.</span></div>
        ) : (
          <div className="table-wrap"><table>
            <thead><tr><th>Created</th><th>Bot</th><th>Strategy</th><th>Pair</th><th>Range</th><th>Levels</th><th>Allocation</th><th>Mode</th></tr></thead>
            <tbody>{configs.map((config) => <tr key={config.grid_config_id}>
              <td>{new Date(config.created_at).toLocaleString()}</td>
              <td>{config.bot_id}</td>
              <td>{config.strategy_version}</td>
              <td>{config.pair}</td>
              <td>{config.lower_price} – {config.upper_price}</td>
              <td>{config.levels}</td>
              <td>{config.quote_allocation}</td>
              <td>{config.execution_mode}</td>
            </tr>)}</tbody>
          </table></div>
        )}
      </article>
    </section>
  );
}
