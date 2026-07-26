import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { BotLifecycleControls } from "@/components/bot-lifecycle-controls";
import { BotRevisionForm } from "@/components/bot-revision-form";
import { StatusPill } from "@/components/status-pill";
import { getBotOperationsDetail, type BotEvidenceState } from "@/lib/bot-operations";

function timestamp(value: string | null | undefined) {
  return value ? new Date(value).toLocaleString() : "Unavailable";
}

function SectionState({ state }: { state: BotEvidenceState }) {
  return <StatusPill value={state} />;
}

function EmptyEvidence({ state, label }: { state: BotEvidenceState; label: string }) {
  return (
    <div className="empty-state">
      <strong>No attributable {label}</strong>
      <span>Evidence state: {state}. An unavailable or degraded source is not represented as a confirmed empty result.</span>
    </div>
  );
}

export default async function BotDetailPage({
  params,
}: {
  params: Promise<{ botId: string }>;
}) {
  const { botId } = await params;
  const cookieHeader = (await cookies()).toString();
  const detail = await getBotOperationsDetail(botId, cookieHeader);
  if (!detail) notFound();
  const { bot } = detail;

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Bot operations</span><h1>{bot.name}</h1></div>
        <div className="status-cluster"><StatusPill value={bot.desired_state} /><StatusPill value={bot.observed_state} /></div>
      </div>
      <div className="status-banner status-info">
        <strong>Tenant- and bot-scoped evidence</strong>
        <span>Every section is filtered to {bot.tenant_id} / {bot.bot_id}. Runtime lifecycle remains separate from trade execution authority; browser code receives no private runtime or observability endpoint.</span>
      </div>

      <div className="detail-grid detail-grid-wide">
        <div><span>Bot ID</span><strong>{bot.bot_id}</strong></div>
        <div><span>Tenant</span><strong>{bot.tenant_id}</strong></div>
        <div><span>Environment</span><strong>{bot.spec.environment}</strong></div>
        <div><span>Execution mode</span><strong>{bot.spec.execution_mode}</strong></div>
        <div><span>Config revision</span><strong>{bot.spec.config_revision}</strong></div>
        <div><span>Runtime version</span><strong>{bot.spec.runtime_version}</strong></div>
        <div><span>Runtime evidence</span><SectionState state={detail.section_states.runtime_evidence} /></div>
        <div><span>Valuation</span><SectionState state={detail.section_states.valuation} /></div>
      </div>

      <div className="surface-grid">
        <BotLifecycleControls
          botId={bot.bot_id}
          desiredState={bot.desired_state}
          observedState={bot.observed_state}
          permissions={detail.permissions}
        />
        <BotRevisionForm botId={bot.bot_id} spec={bot.spec} allowed={detail.permissions.revise} />
      </div>

      <div className="surface-grid">
        <article className="panel surface-card">
          <div className="panel-heading"><div><span className="eyebrow">Decision stack</span><h2>Immutable configuration</h2></div></div>
          <dl className="definition-list">
            <div><dt>Strategy version</dt><dd>{bot.spec.strategy_version}</dd></div>
            <div><dt>Model version</dt><dd>{bot.spec.model_version}</dd></div>
            <div><dt>Risk policy</dt><dd>{bot.spec.risk_policy_version}</dd></div>
            <div><dt>Exchange reference</dt><dd>{bot.spec.exchange_connection_ref}</dd></div>
          </dl>
        </article>
        <article className="panel surface-card">
          <div className="panel-heading"><div><span className="eyebrow">Market scope</span><h2>Capital and markets</h2></div></div>
          <dl className="definition-list">
            <div><dt>Markets</dt><dd>{bot.spec.pair_universe.join(", ")}</dd></div>
            <div><dt>Timeframe</dt><dd>{bot.spec.timeframe}</dd></div>
            <div><dt>Capital allocation</dt><dd>{bot.spec.capital_allocation} {bot.spec.capital_currency}</dd></div>
            <div><dt>Lifecycle separation</dt><dd>Desired-state commands only</dd></div>
          </dl>
        </article>
      </div>

      <article className="panel">
        <div className="panel-heading">
          <div><span className="eyebrow">Private runtime mirror</span><h2>Source status</h2></div>
          <SectionState state={detail.section_states.runtime_evidence} />
        </div>
        {detail.source_statuses.length === 0 ? (
          <EmptyEvidence state={detail.section_states.runtime_evidence} label="runtime source status" />
        ) : (
          <div className="table-wrap"><table>
            <thead><tr><th>Kind</th><th>Runtime</th><th>Freshness</th><th>Reconciliation</th><th>Complete</th><th>Records</th><th>Observed</th><th>Reason</th></tr></thead>
            <tbody>{detail.source_statuses.map((status) => (
              <tr key={`${status.source_runtime_id}:${status.kind}`}>
                <td>{status.kind}</td><td>{status.source_runtime_id}</td><td><StatusPill value={status.freshness} /></td><td><StatusPill value={status.reconciliation_status} /></td><td>{status.complete ? "Yes" : "No"}</td><td>{status.record_count}</td><td>{timestamp(status.source_observed_at)}</td><td>{status.reason_code ?? "—"}</td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
      </article>

      <article className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Open positions</span><h2>Bot-scoped positions</h2></div><SectionState state={detail.section_states.runtime_evidence} /></div>
        {detail.positions.length === 0 ? <EmptyEvidence state={detail.section_states.runtime_evidence} label="positions" /> : (
          <div className="table-wrap"><table>
            <thead><tr><th>Pair</th><th>Side</th><th>Amount</th><th>Runtime</th><th>Freshness</th><th>Reconciliation</th><th>Opened</th></tr></thead>
            <tbody>{detail.positions.map((position) => (
              <tr key={position.position_id}><td>{position.pair}</td><td>{position.side}</td><td>{position.amount}</td><td>{position.source_runtime_id}</td><td><StatusPill value={position.freshness} /></td><td><StatusPill value={position.reconciliation_status} /></td><td>{timestamp(position.opened_at)}</td></tr>
            ))}</tbody>
          </table></div>
        )}
      </article>

      <article className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Orders and trades</span><h2>Attributable execution evidence</h2></div><SectionState state={detail.section_states.runtime_evidence} /></div>
        <div className="surface-grid">
          <div>
            <h3>Orders</h3>
            {detail.orders.length === 0 ? <EmptyEvidence state={detail.section_states.runtime_evidence} label="orders" /> : (
              <div className="table-wrap"><table><thead><tr><th>Pair</th><th>Side</th><th>State</th><th>Amount</th><th>Freshness</th><th>Created</th></tr></thead><tbody>{detail.orders.map((order) => (
                <tr key={order.order_id}><td>{order.pair}</td><td>{order.side}</td><td><StatusPill value={order.state} /></td><td>{order.amount}</td><td><StatusPill value={order.freshness} /></td><td>{timestamp(order.created_at)}</td></tr>
              ))}</tbody></table></div>
            )}
          </div>
          <div>
            <h3>Trades</h3>
            {detail.trades.length === 0 ? <EmptyEvidence state={detail.section_states.runtime_evidence} label="trades" /> : (
              <div className="table-wrap"><table><thead><tr><th>Pair</th><th>State</th><th>Amount</th><th>Realized PNL</th><th>Freshness</th><th>Closed</th></tr></thead><tbody>{detail.trades.map((trade) => (
                <tr key={trade.trade_id}><td>{trade.pair}</td><td><StatusPill value={trade.state} /></td><td>{trade.amount}</td><td>{trade.realized_pnl ?? "—"}</td><td><StatusPill value={trade.freshness} /></td><td>{timestamp(trade.closed_at)}</td></tr>
              ))}</tbody></table></div>
            )}
          </div>
        </div>
      </article>

      <article className="panel">
        <div className="panel-heading"><div><span className="eyebrow">PNL evidence</span><h2>Performance and valuation</h2></div><SectionState state={detail.section_states.valuation} /></div>
        <div className="detail-grid detail-grid-wide">
          <div><span>Realized PNL</span><strong>{detail.performance?.realized_pnl ?? "Unavailable"}</strong></div>
          <div><span>Fees</span><strong>{detail.performance?.fees ?? "Unavailable"}</strong></div>
          <div><span>Net PNL</span><strong>{detail.performance?.net_pnl ?? "Unavailable"}</strong></div>
          <div><span>Trade count</span><strong>{detail.performance?.trade_count ?? "Unavailable"}</strong></div>
        </div>
        {detail.valuations.length === 0 ? <EmptyEvidence state={detail.section_states.valuation} label="open-position valuations" /> : (
          <div className="table-wrap"><table><thead><tr><th>Pair</th><th>State</th><th>Entry</th><th>Mark</th><th>Unrealized PNL</th><th>Currency</th><th>Observed</th><th>Reason</th></tr></thead><tbody>{detail.valuations.map((valuation) => (
            <tr key={valuation.valuation_id}><td>{valuation.pair}</td><td><StatusPill value={valuation.state} /></td><td>{valuation.entry_rate ?? "—"}</td><td>{valuation.mark_rate ?? "—"}</td><td>{valuation.unrealized_pnl ?? "—"}</td><td>{valuation.valuation_currency ?? "—"}</td><td>{timestamp(valuation.source_observed_at)}</td><td>{valuation.reason_code ?? "—"}</td></tr>
          ))}</tbody></table></div>
        )}
      </article>

      <div className="surface-grid">
        <article className="panel surface-card">
          <div className="panel-heading"><div><span className="eyebrow">Deterministic risk</span><h2>Risk decisions</h2></div><SectionState state={detail.section_states.risk} /></div>
          {detail.risk_events.length === 0 ? <EmptyEvidence state={detail.section_states.risk} label="correlated risk decisions" /> : (
            <div className="table-wrap"><table><thead><tr><th>Decision</th><th>Policy</th><th>Reasons</th><th>Occurred</th></tr></thead><tbody>{detail.risk_events.map((event) => (
              <tr key={event.risk_decision_id}><td><StatusPill value={event.decision} /></td><td>{event.risk_policy_version}</td><td>{event.reason_codes.join(", ")}</td><td>{timestamp(event.occurred_at)}</td></tr>
            ))}</tbody></table></div>
          )}
        </article>
        <article className="panel surface-card">
          <div className="panel-heading"><div><span className="eyebrow">Append-only evidence</span><h2>Audit events</h2></div><SectionState state={detail.section_states.audit} /></div>
          {detail.audit_events.length === 0 ? <EmptyEvidence state={detail.section_states.audit} label="audit events" /> : (
            <div className="table-wrap"><table><thead><tr><th>Action</th><th>Result</th><th>Actor</th><th>Occurred</th><th>Correlation</th></tr></thead><tbody>{detail.audit_events.map((event) => (
              <tr key={event.audit_id}><td>{event.action}</td><td><StatusPill value={event.result} /></td><td>{event.actor_id}</td><td>{timestamp(event.occurred_at)}</td><td>{event.correlation_id}</td></tr>
            ))}</tbody></table></div>
          )}
        </article>
      </div>

      <article className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Operational telemetry</span><h2>Runtime logs · last 24 hours</h2></div><SectionState state={detail.section_states.runtime_logs} /></div>
        <p className="freshness">Source: {detail.observability?.source_id ?? "Unavailable"}. Runtime logs are retention-bound operational telemetry and remain separate from append-only audit evidence.</p>
        {detail.runtime_logs.length === 0 ? <EmptyEvidence state={detail.section_states.runtime_logs} label="runtime log records" /> : (
          <div className="table-wrap"><table><thead><tr><th>Time</th><th>Level</th><th>Service</th><th>Component</th><th>Message</th><th>Correlation / trace</th></tr></thead><tbody>{detail.runtime_logs.map((record) => (
            <tr key={record.record_id}><td>{timestamp(record.timestamp)}</td><td><StatusPill value={record.level} /></td><td>{record.service}</td><td>{record.component}</td><td>{record.message}</td><td>{record.correlation_id}<span>{record.trace_id ?? "No trace"}</span></td></tr>
          ))}</tbody></table></div>
        )}
      </article>
    </section>
  );
}
