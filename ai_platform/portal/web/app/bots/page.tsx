import { cookies } from "next/headers";
import Link from "next/link";

import { StatusPill } from "@/components/status-pill";
import { listBotFleetOperations, type BotFleetRecord } from "@/lib/bot-operations";

function value(
  searchParams: Record<string, string | string[] | undefined>,
  key: string,
): string {
  const candidate = searchParams[key];
  return Array.isArray(candidate) ? candidate[0] ?? "" : candidate ?? "";
}

function matches(record: BotFleetRecord, filters: Record<string, string>) {
  const { bot } = record;
  return (
    (!filters.environment || bot.spec.environment === filters.environment) &&
    (!filters.status ||
      bot.desired_state === filters.status ||
      bot.observed_state === filters.status) &&
    (!filters.exchange ||
      bot.spec.exchange_connection_ref.toLowerCase().includes(filters.exchange.toLowerCase())) &&
    (!filters.strategy ||
      bot.spec.strategy_version.toLowerCase().includes(filters.strategy.toLowerCase())) &&
    (!filters.model || bot.spec.model_version.toLowerCase().includes(filters.model.toLowerCase())) &&
    (!filters.market ||
      bot.spec.pair_universe.some((pair) =>
        pair.toLowerCase().includes(filters.market.toLowerCase()),
      )) &&
    (!filters.risk || record.risk_state === filters.risk)
  );
}

function pnl(valueToRender: string | null, currency: string) {
  return valueToRender === null ? "—" : `${valueToRender} ${currency}`;
}

export default async function BotsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const cookieHeader = (await cookies()).toString();
  const fleet = await listBotFleetOperations(cookieHeader);
  const query = await searchParams;
  const filters = {
    environment: value(query, "environment"),
    status: value(query, "status"),
    exchange: value(query, "exchange"),
    strategy: value(query, "strategy"),
    model: value(query, "model"),
    market: value(query, "market"),
    risk: value(query, "risk"),
  };
  const bots = fleet.filter((record) => matches(record, filters));

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Bot operations</span><h1>Bot fleet</h1></div>
        <Link className="primary-button link-button" href="/bots/new">Create Bot</Link>
      </div>
      <div className="status-banner status-info">
        <strong>Canonical operational convergence</strong>
        <span>Fleet rows compose bounded server-side bot, runtime-evidence, valuation, risk and audit reads. Degraded evidence remains explicit and the browser receives no private runtime endpoint or credential.</span>
      </div>
      <article className="panel">
        <form className="bot-form" method="get">
          <div className="form-grid">
            <label>Environment
              <select defaultValue={filters.environment} name="environment">
                <option value="">All</option>
                <option value="research">Research</option>
                <option value="test">Test</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
              </select>
            </label>
            <label>Status<input defaultValue={filters.status} name="status" placeholder="RUNNING, PAUSED…" /></label>
            <label>Exchange<input defaultValue={filters.exchange} name="exchange" placeholder="Connection ref" /></label>
            <label>Strategy<input defaultValue={filters.strategy} name="strategy" /></label>
            <label>Model<input defaultValue={filters.model} name="model" /></label>
            <label>Market<input defaultValue={filters.market} name="market" placeholder="BTC/USDT" /></label>
            <label>Risk
              <select defaultValue={filters.risk} name="risk">
                <option value="">All</option>
                <option value="NORMAL">Normal</option>
                <option value="ATTENTION">Attention</option>
                <option value="UNKNOWN">Unknown</option>
                <option value="UNAVAILABLE">Unavailable</option>
              </select>
            </label>
          </div>
          <div className="status-cluster">
            <button className="primary-button" type="submit">Apply filters</button>
            <Link className="primary-button link-button" href="/bots">Clear</Link>
          </div>
        </form>
      </article>
      <article className="panel">
        {bots.length === 0 ? (
          <div className="empty-state"><strong>No bots match the current filters</strong><span>Clear filters or create an immutable dry-run configuration.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Bot</th><th>Lifecycle</th><th>Positions</th><th>PNL</th><th>Risk</th><th>Runtime</th><th>Strategy / model</th><th>Market</th><th>Last activity</th><th>Details</th>
                </tr>
              </thead>
              <tbody>
                {bots.map((record) => (
                  <tr key={record.bot.bot_id}>
                    <td><strong>{record.bot.name}</strong><span>{record.bot.bot_id}</span><span>{record.bot.spec.environment}</span></td>
                    <td><StatusPill value={record.bot.desired_state} /><span>Observed: {record.bot.observed_state}</span></td>
                    <td><strong>{record.open_position_count}</strong><span><StatusPill value={record.position_state} /></span></td>
                    <td>
                      <strong>R {pnl(record.realized_net_pnl, record.bot.spec.capital_currency)}</strong>
                      <span>U {pnl(record.unrealized_pnl, record.bot.spec.capital_currency)}</span>
                      <span><StatusPill value={record.valuation_state} /></span>
                    </td>
                    <td><StatusPill value={record.risk_state} /></td>
                    <td><StatusPill value={record.runtime_health} /></td>
                    <td><strong>{record.bot.spec.strategy_version}</strong><span>{record.bot.spec.model_version}</span><span>rev {record.bot.spec.config_revision}</span></td>
                    <td><strong>{record.bot.spec.pair_universe.join(", ")}</strong><span>{record.bot.spec.exchange_connection_ref}</span></td>
                    <td>{record.last_activity_at ? new Date(record.last_activity_at).toLocaleString() : "Unavailable"}</td>
                    <td><Link className="text-link" href={`/bots/detail/${encodeURIComponent(record.bot.bot_id)}`}>Open</Link></td>
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
