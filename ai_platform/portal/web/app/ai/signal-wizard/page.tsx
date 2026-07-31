import { cookies } from "next/headers";

import { listSignalWizardFeatures } from "@/lib/signal-wizard-api";
import type { SignalWizardFeatureCatalog } from "@/lib/signal-wizard-contracts";

import { SignalWizardClient } from "./signal-wizard-client";

interface SignalWizardPageProps {
  searchParams: Promise<{ wizard_view?: string }>;
}

interface SignalWizardFailure {
  status: number;
  message: string;
}

export default async function SignalWizardPage({ searchParams }: SignalWizardPageProps) {
  const cookieHeader = (await cookies()).toString();
  const view = (await searchParams).wizard_view;
  let catalog: SignalWizardFeatureCatalog | null = null;
  let failure: SignalWizardFailure | undefined;

  try {
    catalog = await listSignalWizardFeatures(cookieHeader);
    if (process.env.PORTAL_WEB_DATA_MODE === "fixture") {
      if (view === "failure") throw new Error("Fixture Feature Registry request failed closed");
      if (view === "empty") catalog.features = [];
      if (view === "stale") {
        catalog.stale = true;
        catalog.reason_codes = ["FEATURE_REGISTRY_SNAPSHOT_STALE", "REFRESH_REQUIRED"];
      }
    }
  } catch (error) {
    failure = {
      status:
        typeof error === "object" && error !== null && "status" in error
          ? Number((error as { status: unknown }).status)
          : 502,
      message: error instanceof Error ? error.message : "Feature Registry request failed closed",
    };
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <span className="eyebrow">AI Intelligence</span>
          <h1>Signal Wizard</h1>
        </div>
        {catalog ? (
          <span className="freshness">Approved Feature Registry · research-only candidate</span>
        ) : null}
      </div>
      {catalog ? (
        <div className="status-banner status-info">
          <strong>Experiment intent only</strong>
          <span>
            Preview validates closed-bar features, constraints and leakage evidence. Submit persists a
            research experiment candidate; it cannot deploy, promote, trade or authorize live capital.
          </span>
        </div>
      ) : null}
      <SignalWizardClient initialCatalog={catalog} initialFailure={failure} />
    </section>
  );
}
