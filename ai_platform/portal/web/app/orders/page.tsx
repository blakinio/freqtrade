import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listBots } from "@/lib/portal-api";
import { aggregateFreshness, runtimeEvidence, sourceStatusFor } from "@/lib/runtime-evidence";

export default async function OrdersPage() {
  const cookieHeader = (await cookies()).toString();
  const [evidence, bots] = await Promise.all([
    runtimeEvidence(cookieHeader),
    listBots(cookieHeader),
  ]);
  const orders = evidence.orders;
  const statuses = sourceStatusFor(evidence, "ORDERS");
  const freshness = aggregateFreshness(statuses);
  const unavailable = freshness === "SOURCE_UNAVAILABLE" || freshness === "UNAVAILABLE";
  const botNames = new Map(bots.map((bot) => [bot.bot_id, bot.name]));

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Trading</span><h1>Orders</h1></div>
        <span className="freshness">Runtime evidence · {freshness}</span>
      </div>
      <article className="panel">
        {orders.length === 0 ? (
          <div className="empty-state">
            <strong>{unavailable ? "Order source unavailable" : "No orders recorded"}</strong>
            <span>
              {unavailable
                ? "The private runtime source is unavailable or incomplete; the portal does not fabricate an empty current order history."
                : "A complete authoritative runtime read found no orders for this tenant."}
            </span>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Order</th><th>Bot</th><th>Pair</th><th>Side</th><th>State</th><th>Amount</th><th>Created</th><th>Freshness</th><th>Reconciliation</th><th>Runtime</th></tr></thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.order_id}>
                    <td><strong>{order.source_order_id ?? order.order_id}</strong><span>{order.execution_intent_id ?? "unattributed runtime order"}</span></td>
                    <td><strong>{botNames.get(order.bot_id) ?? order.bot_id}</strong><span>{order.bot_id}</span></td>
                    <td>{order.pair}</td>
                    <td>{order.side}</td>
                    <td><StatusPill value={order.state} /></td>
                    <td>{order.amount}</td>
                    <td>{new Date(order.created_at).toLocaleString()}</td>
                    <td><StatusPill value={order.freshness} /></td>
                    <td><StatusPill value={order.reconciliation_status} /></td>
                    <td>{order.source_runtime_id}</td>
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
