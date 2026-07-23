import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listBots, listOrders } from "@/lib/portal-api";

export default async function OrdersPage() {
  const cookieHeader = (await cookies()).toString();
  const [orders, bots] = await Promise.all([
    listOrders(cookieHeader),
    listBots(cookieHeader),
  ]);
  const botNames = new Map(bots.map((bot) => [bot.bot_id, bot.name]));

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Trading</span><h1>Orders</h1></div>
        <span className="freshness">Attributable normalized evidence</span>
      </div>
      <article className="panel">
        {orders.length === 0 ? (
          <div className="empty-state"><strong>No orders recorded</strong><span>Orders appear only after trusted execution or simulator evidence is normalized into the portal read model.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Order</th><th>Bot</th><th>Pair</th><th>Side</th><th>State</th><th>Amount</th><th>Created</th><th>Runtime</th></tr></thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.order_id}>
                    <td><strong>{order.order_id}</strong><span>{order.execution_intent_id}</span></td>
                    <td><strong>{botNames.get(order.bot_id) ?? order.bot_id}</strong><span>{order.bot_id}</span></td>
                    <td>{order.pair}</td>
                    <td>{order.side}</td>
                    <td><StatusPill value={order.state} /></td>
                    <td>{order.amount}</td>
                    <td>{new Date(order.created_at).toLocaleString()}</td>
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
