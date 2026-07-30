import { StrategyCatalogClient } from "@/components/strategy-catalog-client";

export default function StrategyCatalogPage() {
  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Bots</span>
          <h1>Strategy Catalog</h1>
        </div>
        <span className="freshness">Tenant-scoped immutable lifecycle evidence</span>
      </div>
      <div className="status-banner status-info">
        <strong>Research-only catalog boundary</strong>
        <span>
          Strategy versions, approvals, paper or shadow deployments and rollback evidence remain behind the same-origin Portal boundary. The catalog cannot promote a model, contact Freqtrade directly or grant live-capital authority.
        </span>
      </div>
      <StrategyCatalogClient />
    </section>
  );
}
