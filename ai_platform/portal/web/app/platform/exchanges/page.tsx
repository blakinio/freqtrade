import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import {
  listPublicExchangeConnections,
  type PublicExchangeConnectionView,
} from "@/lib/exchange-connections";

export default async function ExchangeConnectionsPage() {
  const cookieHeader = (await cookies()).toString();
  let connections: PublicExchangeConnectionView[] | null = null;

  try {
    connections = await listPublicExchangeConnections(cookieHeader);
  } catch {
    connections = null;
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Platform</span><h1>Exchange Connections</h1></div>
        <span className="freshness">BM-06 public metadata · credentials excluded</span>
      </div>
      <div className="status-banner status-info">
        <strong>Secret boundary preserved</strong>
        <span>The browser receives connection identity, capability and verification status only. Credential references, account labels, API keys, passphrases and secret-store locations are excluded by the response schema.</span>
      </div>
      <article className="panel">
        {connections === null ? (
          <div className="empty-state" role="alert">
            <strong>Exchange metadata source unavailable</strong>
            <span>The page fails closed and does not reconstruct connection details from bot configurations.</span>
          </div>
        ) : connections.length === 0 ? (
          <div className="empty-state">
            <strong>No exchange connection metadata</strong>
            <span>Credential provisioning remains behind PI-07 and is not available from this browser surface.</span>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Connection</th>
                  <th>Markets</th>
                  <th>Product status</th>
                  <th>Trading</th>
                  <th>Withdrawals</th>
                  <th>Credential material</th>
                </tr>
              </thead>
              <tbody>
                {connections.map((connection) => (
                  <tr key={connection.connection_id}>
                    <td>
                      <strong>{connection.display_name}</strong>
                      <span>{connection.exchange_id} · {connection.connection_id} · revision {connection.metadata_revision}</span>
                    </td>
                    <td>{connection.enabled_market_types.join(", ")}</td>
                    <td><StatusPill value={connection.product_status} /></td>
                    <td><StatusPill value={connection.trading_permission_status} /></td>
                    <td><StatusPill value={connection.withdrawal_permission_status} /></td>
                    <td>{connection.credential_material_exposed ? "Rejected" : "Not exposed"}</td>
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
