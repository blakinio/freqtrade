"use server";

import { cookies } from "next/headers";

import {
  compareStrategyLabExperiments,
  createStrategyLabExperiment,
  getStrategyLabBundle,
} from "@/lib/strategy-lab-api";
import type {
  ExperimentBundle,
  ExperimentComparison,
  ExperimentCreateRequest,
} from "@/lib/strategy-lab-contracts";

export async function runStrategyLabExperiment(
  request: ExperimentCreateRequest,
  idempotencyKey: string,
): Promise<ExperimentBundle> {
  return createStrategyLabExperiment(request, idempotencyKey, (await cookies()).toString());
}

export async function loadStrategyLabExperiment(experimentId: string): Promise<ExperimentBundle> {
  return getStrategyLabBundle(experimentId, (await cookies()).toString());
}

export async function compareStrategyLabExperimentVariants(
  baselineId: string,
  variantId: string,
): Promise<ExperimentComparison> {
  return compareStrategyLabExperiments(baselineId, variantId, (await cookies()).toString());
}
