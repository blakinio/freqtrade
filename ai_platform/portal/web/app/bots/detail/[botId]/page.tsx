import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { StatusPill } from "@/components/status-pill";
import { getBot } from "@/lib/portal-api";

export default async function BotDetailPage({
  params,
}: {
  params: Promise<{ botId: string }>;
}) {
  const { botId } = await params;
  const cookieHeader = (await cookies()).toString();
  const bot = await getBot(botId, cookieHeader);
  if (!bot) {
    notFound();
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Bot detail</span><h1>{bot.name}</h1></div>
        <div className="status-cluster"><StatusPill value={bot.desired_state} /><StatusPill value={bot.observed_state} /></div>
      </div>
      <div className="status-banner status-info">
        <strong>Immutable revision context</strong>
        <span>This view shows the exact strategy, model, risk policy and runtime configuration currently attributed to the bot resource.</span>
      </div>
      <div className="detail-grid detail-grid-wide">
        <div><span>Bot ID</span><strong>{bot.bot_id}</strong></div>
        <div><span>Tenant</span><strong>{bot.tenant_id}</strong></div>
        <div><span>Environment</span><strong>{bot.spec.environment}</strong></div>
        <div><span>Execution mode</span><strong>{bot.spec.execution_mode}</strong></div>
        <div><span>Config revision</span><strong>{bot.spec.config_revision}</strong></div>
        <div><span>Runtime version</span><strong>{bot.spec.runtime_version}</strong></div>
      </div>
      <div className="surface-grid">
        <article className="panel surface-card">
          <div className="panel-heading"><div><span className="eyebrow">Decision stack</span><h2>Strategy and AI</h2></div></div>
          <dl className="definition-list">
            <div><dt>Strategy version</dt><dd>{bot.spec.strategy_version}</dd></div>
            <div><dt>Model version</dt><dd>{bot.spec.model_version}</dd></div>
            <div><dt>Risk policy</dt><dd>{bot.spec.risk_policy_version}</dd></div>
          </dl>
        </article>
        <article className="panel surface-card">
          <div className="panel-heading"><div><span className="eyebrow">Market scope</span><h2>Execution configuration</h2></div></div>
          <dl className="definition-list">
            <div><dt>Markets</dt><dd>{bot.spec.pair_universe.join(", ")}</dd></div>
            <div><dt>Timeframe</dt><dd>{bot.spec.timeframe}</dd></div>
            <div><dt>Capital allocation</dt><dd>{bot.spec.capital_allocation} {bot.spec.capital_currency}</dd></div>
            <div><dt>Exchange connection</dt><dd>{bot.spec.exchange_connection_ref}</dd></div>
          </dl>
        </article>
      </div>
    </section>
  );
}
