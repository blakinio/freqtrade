import { cookies } from "next/headers";

import { StatusPill } from "@/components/status-pill";
import { listStrategies } from "@/lib/product-api";

export default async function StrategyCatalogPage() {
  const cookieHeader = (await cookies()).toString();
  const strategies = await listStrategies(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Bots</span><h1>Strategy Catalog</h1></div>
        <span className="freshness">Immutable portal strategy metadata</span>
      </div>
      <div className="status-banner status-info">
        <strong>Catalog boundary</strong>
        <span>The catalog describes approved portal configuration references. It does not promote research candidates or grant live-capital execution.</span>
      </div>
      <article className="panel">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Strategy</th><th>Version</th><th>Kind</th><th>Modes</th><th>Runtime status</th><th>Immutable</th></tr></thead>
            <tbody>{strategies.map((strategy) => (
              <tr key={strategy.strategy_version}>
                <td><strong>{strategy.display_name}</strong><span>{strategy.description}</span></td>
                <td>{strategy.strategy_version}</td>
                <td>{strategy.kind}</td>
                <td>{strategy.allowed_execution_modes.join(", ")}</td>
                <td><StatusPill value={strategy.runtime_status} /></td>
                <td>{strategy.immutable ? "Yes" : "No"}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
