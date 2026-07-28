import { cookies } from "next/headers";

import { CreateBotConfigurationForm } from "@/components/bot-builder/create-bot-configuration-form";
import type { BotCatalogSnapshot } from "@/lib/bot-management-contracts";
import { loadApprovedBotCatalog } from "@/lib/bot-management-api";
import { portalEnvironment } from "@/lib/portal-api";

export default async function CreateBotPage() {
  const environment = portalEnvironment();
  const cookieHeader = (await cookies()).toString();
  let catalog: BotCatalogSnapshot | null = null;

  try {
    catalog = await loadApprovedBotCatalog(cookieHeader);
  } catch {
    catalog = null;
  }

  if (catalog === null) {
    return (
      <section className="page-stack">
        <div className="page-heading">
          <div><span className="eyebrow">Bots</span><h1>Create Bot Configuration</h1></div>
        </div>
        <div className="status-banner status-warning" role="alert">
          <strong>Approved catalog unavailable</strong>
          <span>The builder fails closed and does not fall back to browser-supplied strategy, model, risk or runtime versions.</span>
        </div>
      </section>
    );
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Bots</span><h1>Create Bot Configuration</h1></div>
        <span className="freshness">Catalog {catalog.catalog_id} · revision {catalog.revision}</span>
      </div>
      <div className="status-banner status-info">
        <strong>Immutable configuration workflow</strong>
        <span>Finalization validates a server-owned catalog revision. It does not start Freqtrade or submit an order.</span>
      </div>
      <article className="panel form-panel">
        <div className="panel-heading">
          <div><span className="eyebrow">BMW-01</span><h2>Approved dry-run builder</h2></div>
        </div>
        <CreateBotConfigurationForm catalog={catalog} environment={environment} />
      </article>
    </section>
  );
}
