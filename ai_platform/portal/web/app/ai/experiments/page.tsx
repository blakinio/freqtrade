import { cookies } from "next/headers";

import {
  compareStrategyLabExperiments,
  getStrategyLabBundle,
  listStrategyLabExperiments,
  listStrategyLabStrategies,
} from "@/lib/strategy-lab-api";
import type { ExperimentComparison } from "@/lib/strategy-lab-contracts";

import { StrategyLabClient } from "./strategy-lab-client";

export default async function ExperimentsPage() {
  const cookieHeader = (await cookies()).toString();
  const [strategies, experiments] = await Promise.all([
    listStrategyLabStrategies(cookieHeader),
    listStrategyLabExperiments(cookieHeader),
  ]);
  const initialBundle = experiments[0]
    ? await getStrategyLabBundle(experiments[0].experiment_id, cookieHeader)
    : null;
  let initialComparison: ExperimentComparison | null = null;
  if (experiments[0] && experiments[1]) {
    try {
      initialComparison = await compareStrategyLabExperiments(
        experiments[0].experiment_id,
        experiments[1].experiment_id,
        cookieHeader,
      );
    } catch {
      // Different strategies or timeranges are valid history but not comparable variants.
    }
  }
  return (
    <StrategyLabClient
      strategies={strategies}
      initialExperiments={experiments}
      initialBundle={initialBundle}
      initialComparison={initialComparison}
    />
  );
}
