import { SignalWizardClient } from "./signal-wizard-client";

export default function SignalWizardPage() {
  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <span className="eyebrow">AI Intelligence</span>
          <h1>Signal Wizard</h1>
        </div>
        <span className="freshness">Approved features · research-only</span>
      </div>
      <div className="status-banner status-info">
        <strong>Same-origin research boundary</strong>
        <span>
          The browser can select only approved Feature Registry identities and submits through the
          Portal BFF. Preview creates no trade, deployment or promotion authority; submit persists a
          research experiment candidate only.
        </span>
      </div>
      <SignalWizardClient />
    </section>
  );
}
