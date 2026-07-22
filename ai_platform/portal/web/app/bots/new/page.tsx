import { CreateBotForm } from "@/components/create-bot-form";
import { portalEnvironment } from "@/lib/portal-api";

export default function CreateBotPage() {
  const environment = portalEnvironment();
  return (
    <section className="page-stack">
      <div className="page-heading"><div><span className="eyebrow">Bots</span><h1>Create Bot</h1></div></div>
      <article className="panel form-panel">
        <div className="panel-heading"><div><span className="eyebrow">Immutable revision</span><h2>Dry-run configuration</h2></div></div>
        <CreateBotForm environment={environment} />
      </article>
    </section>
  );
}
