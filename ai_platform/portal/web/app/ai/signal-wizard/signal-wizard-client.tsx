"use client";

import { useMemo, useState, type FormEvent } from "react";

import { csrfFetch } from "@/lib/client-fetch";
import type {
  ClosureRequestContext,
  JsonValue,
  PortalSessionView,
  SignalWizardErrorPayload,
  SignalWizardFeature,
  SignalWizardFeatureCatalog,
  SignalWizardParameterConstraint,
  SignalWizardPreviewCommand,
  SignalWizardPreviewResult,
  SignalWizardSubmitCommand,
  SignalWizardSubmitResult,
} from "@/lib/signal-wizard-contracts";

interface RequestFailure {
  status: number;
  message: string;
  reasonCode?: string;
}

interface SignalWizardClientProps {
  initialCatalog: SignalWizardFeatureCatalog | null;
  initialFailure?: RequestFailure;
}

const operators = ["gt", "gte", "lt", "lte", "eq", "neq"] as const;

function normalizeFailure(caught: unknown, fallback: string): RequestFailure {
  const value = caught as Partial<RequestFailure>;
  return {
    status: typeof value.status === "number" ? value.status : 502,
    message: typeof value.message === "string" ? value.message : fallback,
    reasonCode: typeof value.reasonCode === "string" ? value.reasonCode : undefined,
  };
}

async function responseFailure(response: Response): Promise<RequestFailure> {
  let payload: SignalWizardErrorPayload = {};
  try {
    payload = (await response.json()) as SignalWizardErrorPayload;
  } catch {
    payload = {};
  }
  if (typeof payload.detail === "object" && payload.detail !== null) {
    return {
      status: response.status,
      message: payload.detail.message ?? `Signal Wizard request failed with status ${response.status}`,
      reasonCode: payload.detail.reason_code,
    };
  }
  return {
    status: response.status,
    message: payload.detail ?? `Signal Wizard request failed with status ${response.status}`,
    reasonCode: payload.code,
  };
}

async function portalSession(): Promise<PortalSessionView> {
  const response = await fetch("/api/identity/session", {
    cache: "no-store",
    credentials: "same-origin",
  });
  if (!response.ok) throw await responseFailure(response);
  return (await response.json()) as PortalSessionView;
}

function requestContext(session: PortalSessionView, strategyId: string): ClosureRequestContext {
  const createdAt = new Date().toISOString();
  return {
    contract_version: "v2",
    tenant_id: session.tenant_id,
    actor_id: session.principal_id,
    actor_type: "user",
    resource_type: "strategy",
    resource_id: strategyId,
    environment: "research",
    execution_mode: "simulated",
    correlation: {
      contract_version: "v1",
      request_id: crypto.randomUUID(),
      correlation_id: crypto.randomUUID(),
      causation_id: null,
    },
    provenance: {
      contract_version: "v2",
      producer: "portal-signal-wizard",
      artifact_id: `signal-wizard:${strategyId}:${createdAt}`,
      created_at: createdAt,
      source_refs: ["feature-registry:approved_for_ai"],
      metadata: { surface: "portal", workflow: "signal-wizard" },
    },
    authority: "research_only",
  };
}

function initialParameters(features: SignalWizardFeature[]): Record<string, Record<string, JsonValue>> {
  return Object.fromEntries(
    features.map((feature) => [
      feature.feature_id,
      Object.fromEntries(feature.parameters.map((parameter) => [parameter.name, parameter.default])),
    ]),
  );
}

function parameterText(value: JsonValue): string {
  if (value === null) return "";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

function parsedParameter(raw: string, kinds: string[]): JsonValue {
  if (kinds.includes("boolean")) return raw === "true";
  if (kinds.includes("integer")) return Number.parseInt(raw, 10);
  if (kinds.includes("number")) return Number(raw);
  return raw;
}

function strategyVersion(preview: SignalWizardPreviewResult): string | null {
  const value = preview.strategy_definition.version;
  return typeof value === "string" ? value : null;
}

function bannerClass(status: number): string {
  if (status === 401 || status === 403) return "status-danger";
  if (status === 409 || status === 422) return "status-warning";
  return "status-danger";
}

export function SignalWizardClient({ initialCatalog, initialFailure }: SignalWizardClientProps) {
  const features = initialCatalog?.features ?? [];
  const [selectedIds, setSelectedIds] = useState<string[]>(features[0] ? [features[0].feature_id] : []);
  const [parameters, setParameters] = useState<Record<string, Record<string, JsonValue>>>(() =>
    initialParameters(features),
  );
  const [strategyId, setStrategyId] = useState("signal-wizard-candidate");
  const [timeframe, setTimeframe] = useState("5m");
  const [conditionFeature, setConditionFeature] = useState(features[0]?.feature_id ?? "");
  const [conditionOperator, setConditionOperator] = useState<(typeof operators)[number]>("gt");
  const [conditionValue, setConditionValue] = useState("0");
  const [experimentName, setExperimentName] = useState("Signal Wizard research candidate");
  const [preview, setPreview] = useState<SignalWizardPreviewResult | null>(null);
  const [submission, setSubmission] = useState<SignalWizardSubmitResult | null>(null);
  const [previewSubmitting, setPreviewSubmitting] = useState(false);
  const [submitSubmitting, setSubmitSubmitting] = useState(false);
  const [failure, setFailure] = useState<RequestFailure | null>(initialFailure ?? null);

  const selectedFeatures = useMemo(
    () => features.filter((feature) => selectedIds.includes(feature.feature_id)),
    [features, selectedIds],
  );
  const missingDependencies = useMemo(() => {
    const selected = new Set(selectedIds);
    return [...new Set(selectedFeatures.flatMap((feature) => feature.dependencies))].filter(
      (dependency) => !selected.has(dependency),
    );
  }, [selectedFeatures, selectedIds]);
  const constraints = useMemo<SignalWizardParameterConstraint[]>(() => {
    const byParameter = new Map<string, SignalWizardParameterConstraint>();
    for (const feature of selectedFeatures) {
      for (const parameter of feature.parameters) {
        if (parameter.minimum === null && parameter.maximum === null && parameter.choices.length === 0) {
          continue;
        }
        const existing = byParameter.get(parameter.name);
        byParameter.set(parameter.name, {
          contract_version: "v2",
          parameter: parameter.name,
          minimum:
            existing?.minimum === null || existing?.minimum === undefined
              ? parameter.minimum
              : parameter.minimum === null
                ? existing.minimum
                : Math.max(existing.minimum, parameter.minimum),
          maximum:
            existing?.maximum === null || existing?.maximum === undefined
              ? parameter.maximum
              : parameter.maximum === null
                ? existing.maximum
                : Math.min(existing.maximum, parameter.maximum),
          allowed_values: parameter.choices.length > 0 ? parameter.choices : (existing?.allowed_values ?? []),
          reason_code: "FEATURE_REGISTRY_PARAMETER_CONSTRAINT",
        });
      }
    }
    return [...byParameter.values()];
  }, [selectedFeatures]);

  function invalidatePreview() {
    setPreview(null);
    setSubmission(null);
    setFailure(null);
  }

  function toggleFeature(feature: SignalWizardFeature, checked: boolean) {
    const next = new Set(selectedIds);
    if (checked) {
      next.add(feature.feature_id);
      for (const dependency of feature.dependencies) {
        if (features.some((candidate) => candidate.feature_id === dependency)) next.add(dependency);
      }
    } else {
      next.delete(feature.feature_id);
    }
    const nextIds = [...next];
    setSelectedIds(nextIds);
    if (!next.has(conditionFeature)) setConditionFeature(nextIds[0] ?? "");
    invalidatePreview();
  }

  function updateParameter(
    featureId: string,
    parameterName: string,
    kinds: string[],
    rawValue: string,
  ) {
    setParameters((current) => ({
      ...current,
      [featureId]: {
        ...current[featureId],
        [parameterName]: parsedParameter(rawValue, kinds),
      },
    }));
    invalidatePreview();
  }

  async function requestPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedFeatures.length === 0) {
      setFailure({ status: 422, message: "Select at least one approved Feature Registry entry." });
      return;
    }
    if (missingDependencies.length > 0) {
      setFailure({
        status: 422,
        message: `Select required dependencies: ${missingDependencies.join(", ")}`,
        reasonCode: "FEATURE_DEPENDENCY_MISSING",
      });
      return;
    }
    if (!conditionFeature || !selectedIds.includes(conditionFeature)) {
      setFailure({ status: 422, message: "Condition must reference a selected feature." });
      return;
    }
    setPreviewSubmitting(true);
    setFailure(null);
    setPreview(null);
    setSubmission(null);
    try {
      const session = await portalSession();
      const command: SignalWizardPreviewCommand = {
        contract_version: "v2",
        context: requestContext(session, strategyId.trim()),
        idempotency_key: crypto.randomUUID(),
        strategy_id: strategyId.trim(),
        base_strategy_version: null,
        feature_selections: selectedFeatures.map((feature) => ({
          contract_version: "v2",
          feature_id: feature.feature_id,
          timeframe,
          parameters: parameters[feature.feature_id] ?? {},
          enabled: true,
        })),
        parameter_constraints: constraints,
        condition_ast: {
          all: [
            {
              feature: conditionFeature,
              op: conditionOperator,
              value: Number.isNaN(Number(conditionValue)) ? conditionValue : Number(conditionValue),
            },
          ],
        },
        requested_strategy_schema_version: "2.0.0",
        capability: {
          contract_version: "v2",
          capability: "strategy.research",
          authorization_decision_ref: "portal-session:model.train",
          enforced: true,
        },
      };
      const response = await csrfFetch("/api/ai/signal-wizard/preview", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(command),
      });
      if (!response.ok) throw await responseFailure(response);
      setPreview((await response.json()) as SignalWizardPreviewResult);
    } catch (caught) {
      setFailure(normalizeFailure(caught, "Signal Wizard preview failed closed"));
    } finally {
      setPreviewSubmitting(false);
    }
  }

  async function submitExperiment() {
    if (!preview) return;
    const version = strategyVersion(preview);
    if (!version) {
      setFailure({ status: 409, message: "Preview does not contain a canonical strategy version." });
      return;
    }
    if (preview.leakage_warnings.some((warning) => warning.blocking)) {
      setFailure({
        status: 409,
        message: "Resolve blocking leakage or repaint warnings before submission.",
        reasonCode: "LEAKAGE_WARNING_PRESENT",
      });
      return;
    }
    setSubmitSubmitting(true);
    setFailure(null);
    setSubmission(null);
    try {
      const session = await portalSession();
      const command: SignalWizardSubmitCommand = {
        contract_version: "v2",
        context: requestContext(session, strategyId.trim()),
        idempotency_key: crypto.randomUUID(),
        preview_hash: preview.preview_hash,
        experiment_name: experimentName.trim(),
        expected_strategy_version: version,
        capability: {
          contract_version: "v2",
          capability: "experiment.submit",
          authorization_decision_ref: "portal-session:model.train",
          enforced: true,
        },
      };
      const response = await csrfFetch("/api/ai/signal-wizard/submit", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(command),
      });
      if (!response.ok) throw await responseFailure(response);
      setSubmission((await response.json()) as SignalWizardSubmitResult);
    } catch (caught) {
      setFailure(normalizeFailure(caught, "Signal Wizard submission failed closed"));
    } finally {
      setSubmitSubmitting(false);
    }
  }

  if (failure && !initialCatalog) {
    const denied = failure.status === 401 || failure.status === 403;
    return (
      <div className={`status-banner ${bannerClass(failure.status)}`} role="alert">
        <strong>{denied ? "Signal Wizard access denied" : "Signal Wizard unavailable"}</strong>
        <span>{failure.message}</span>
        {failure.reasonCode ? <span>{failure.reasonCode}</span> : null}
      </div>
    );
  }

  if (!initialCatalog || features.length === 0) {
    return (
      <div className="empty-state" role="status">
        <strong>No approved AI features are available</strong>
        <span>Signal Wizard fails closed until Feature Registry returns approved_for_ai entries.</span>
      </div>
    );
  }

  return (
    <form className="page-stack" onSubmit={requestPreview}>
      {initialCatalog.stale ? (
        <div className="status-banner status-warning" role="status">
          <strong>Feature Registry snapshot is stale</strong>
          <span>{initialCatalog.reason_codes.join(", ")}</span>
        </div>
      ) : null}

      {failure ? (
        <div className={`status-banner ${bannerClass(failure.status)}`} role="alert">
          <strong>
            {failure.status === 409
              ? "Signal Wizard conflict"
              : failure.status === 401 || failure.status === 403
                ? "Signal Wizard access denied"
                : "Signal Wizard validation failed"}
          </strong>
          <span>{failure.message}</span>
          {failure.reasonCode ? <span>{failure.reasonCode}</span> : null}
        </div>
      ) : null}

      <article className="panel">
        <div className="page-heading">
          <div>
            <span className="eyebrow">Step 1</span>
            <h2>Candidate identity</h2>
          </div>
          <span className="freshness">Tenant-scoped · research · simulated</span>
        </div>
        <div className="form-grid">
          <label className="form-field">
            <span>Strategy ID</span>
            <input
              aria-label="Strategy ID"
              value={strategyId}
              required
              onChange={(event) => {
                setStrategyId(event.target.value);
                invalidatePreview();
              }}
            />
          </label>
          <label className="form-field">
            <span>Timeframe</span>
            <select
              aria-label="Timeframe"
              value={timeframe}
              onChange={(event) => {
                setTimeframe(event.target.value);
                invalidatePreview();
              }}
            >
              <option value="1m">1m</option>
              <option value="5m">5m</option>
              <option value="15m">15m</option>
              <option value="1h">1h</option>
              <option value="4h">4h</option>
            </select>
          </label>
        </div>
      </article>

      <article className="panel">
        <div className="page-heading">
          <div>
            <span className="eyebrow">Step 2</span>
            <h2>Approved Feature Registry selection</h2>
          </div>
          <span className="freshness">{initialCatalog.registry_version}</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Use</th>
                <th>Feature</th>
                <th>Roles / dependencies</th>
                <th>Timestamp policy</th>
                <th>Parameters</th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature) => {
                const selected = selectedIds.includes(feature.feature_id);
                return (
                  <tr key={feature.feature_id}>
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Use ${feature.feature_id}`}
                        checked={selected}
                        disabled={!feature.approved_for_ai}
                        onChange={(event) => toggleFeature(feature, event.target.checked)}
                      />
                    </td>
                    <td>
                      <strong>{feature.feature_id}</strong>
                      <span>{feature.status} · approved_for_ai</span>
                    </td>
                    <td>
                      <span>{feature.roles.join(", ") || "Unclassified"}</span>
                      <span>
                        Dependencies: {feature.dependencies.join(", ") || "none"}
                      </span>
                    </td>
                    <td>
                      <span>{feature.timestamp_policy}</span>
                      <span>{feature.warmup}</span>
                    </td>
                    <td>
                      {feature.parameters.length === 0 ? <span>No parameters</span> : null}
                      {feature.parameters.map((parameter) => {
                        const value = parameters[feature.feature_id]?.[parameter.name] ?? parameter.default;
                        const label = `${feature.feature_id} ${parameter.name}`;
                        if (parameter.choices.length > 0) {
                          return (
                            <label className="form-field" key={parameter.name}>
                              <span>{parameter.name}</span>
                              <select
                                aria-label={label}
                                value={JSON.stringify(value)}
                                disabled={!selected}
                                onChange={(event) => {
                                  setParameters((current) => ({
                                    ...current,
                                    [feature.feature_id]: {
                                      ...current[feature.feature_id],
                                      [parameter.name]: JSON.parse(event.target.value) as JsonValue,
                                    },
                                  }));
                                  invalidatePreview();
                                }}
                              >
                                {parameter.choices.map((choice) => (
                                  <option key={JSON.stringify(choice)} value={JSON.stringify(choice)}>
                                    {parameterText(choice)}
                                  </option>
                                ))}
                              </select>
                            </label>
                          );
                        }
                        if (parameter.kinds.includes("boolean")) {
                          return (
                            <label className="form-field" key={parameter.name}>
                              <span>{parameter.name}</span>
                              <select
                                aria-label={label}
                                value={String(value)}
                                disabled={!selected}
                                onChange={(event) =>
                                  updateParameter(feature.feature_id, parameter.name, parameter.kinds, event.target.value)
                                }
                              >
                                <option value="true">true</option>
                                <option value="false">false</option>
                              </select>
                            </label>
                          );
                        }
                        return (
                          <label className="form-field" key={parameter.name}>
                            <span>{parameter.name}</span>
                            <input
                              aria-label={label}
                              type={parameter.kinds.some((kind) => kind === "integer" || kind === "number") ? "number" : "text"}
                              min={parameter.minimum ?? undefined}
                              max={parameter.maximum ?? undefined}
                              step={parameter.kinds.includes("integer") ? 1 : "any"}
                              value={parameterText(value)}
                              disabled={!selected}
                              onChange={(event) =>
                                updateParameter(feature.feature_id, parameter.name, parameter.kinds, event.target.value)
                              }
                            />
                          </label>
                        );
                      })}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </article>

      <article className="panel">
        <div className="page-heading">
          <div>
            <span className="eyebrow">Step 3</span>
            <h2>Closed-bar condition</h2>
          </div>
        </div>
        <div className="form-grid">
          <label className="form-field">
            <span>Feature</span>
            <select
              aria-label="Condition feature"
              value={conditionFeature}
              onChange={(event) => {
                setConditionFeature(event.target.value);
                invalidatePreview();
              }}
            >
              {selectedFeatures.map((feature) => (
                <option key={feature.feature_id} value={feature.feature_id}>
                  {feature.feature_id}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>Operator</span>
            <select
              aria-label="Condition operator"
              value={conditionOperator}
              onChange={(event) => {
                setConditionOperator(event.target.value as (typeof operators)[number]);
                invalidatePreview();
              }}
            >
              {operators.map((operator) => (
                <option key={operator} value={operator}>{operator}</option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>Value</span>
            <input
              aria-label="Condition value"
              value={conditionValue}
              onChange={(event) => {
                setConditionValue(event.target.value);
                invalidatePreview();
              }}
            />
          </label>
        </div>
      </article>

      <article className="panel">
        <div className="page-heading">
          <div>
            <span className="eyebrow">Validation summary</span>
            <h2>Pre-preview gates</h2>
          </div>
        </div>
        <div className="metric-grid">
          <div><span>Approved features</span><strong>{selectedFeatures.length}</strong></div>
          <div><span>Missing dependencies</span><strong>{missingDependencies.length}</strong></div>
          <div><span>Registry constraints</span><strong>{constraints.length}</strong></div>
          <div><span>Live authority</span><strong>No</strong></div>
        </div>
        {missingDependencies.length > 0 ? (
          <div className="status-banner status-warning" role="alert">
            <strong>Dependencies required</strong>
            <span>{missingDependencies.join(", ")}</span>
          </div>
        ) : null}
        <button
          type="submit"
          className="primary-button"
          disabled={previewSubmitting || selectedFeatures.length === 0 || missingDependencies.length > 0}
        >
          {previewSubmitting ? "Validating preview…" : "Generate canonical preview"}
        </button>
      </article>

      {preview ? (
        <article className="panel">
          <div className="page-heading">
            <div>
              <span className="eyebrow">Step 4</span>
              <h2>Strategy preview</h2>
            </div>
            <span className="freshness">{preview.preview_hash.slice(0, 16)}…</span>
          </div>
          <div className="metric-grid">
            <div><span>Version</span><strong>{strategyVersion(preview) ?? "Unavailable"}</strong></div>
            <div><span>Reason codes</span><strong>{preview.reason_codes.length}</strong></div>
            <div><span>Leakage warnings</span><strong>{preview.leakage_warnings.length}</strong></div>
            <div><span>Execution authority</span><strong>No</strong></div>
          </div>
          <div className="status-banner status-info">
            <strong>Validation reason codes</strong>
            <span>{preview.reason_codes.join(", ") || "No reason codes returned"}</span>
          </div>
          {preview.leakage_warnings.map((warning) => (
            <div
              key={`${warning.field_path}:${warning.reason_code}`}
              className={`status-banner ${warning.blocking ? "status-danger" : "status-warning"}`}
              role="alert"
            >
              <strong>{warning.reason_code}</strong>
              <span>{warning.field_path}: {warning.message}</span>
            </div>
          ))}
          <pre>{JSON.stringify(preview.strategy_definition, null, 2)}</pre>

          <div className="form-grid">
            <label className="form-field">
              <span>Experiment name</span>
              <input
                aria-label="Experiment name"
                value={experimentName}
                required
                onChange={(event) => {
                  setExperimentName(event.target.value);
                  setSubmission(null);
                }}
              />
            </label>
          </div>
          <button
            type="button"
            className="primary-button"
            disabled={
              submitSubmitting ||
              experimentName.trim().length === 0 ||
              preview.leakage_warnings.some((warning) => warning.blocking)
            }
            onClick={() => void submitExperiment()}
          >
            {submitSubmitting ? "Submitting experiment…" : "Submit research experiment candidate"}
          </button>
        </article>
      ) : null}

      {submission ? (
        <div className="status-banner status-success" role="status">
          <strong>Experiment candidate accepted</strong>
          <span>Experiment ID: {submission.experiment_id}</span>
          <span>{submission.reason_codes.join(", ")}</span>
          <span>Execution authority: no · promotion authority: no · live capital authority: no</span>
        </div>
      ) : null}
    </form>
  );
}
