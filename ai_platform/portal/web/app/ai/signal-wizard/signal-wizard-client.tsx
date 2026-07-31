"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";

import { csrfFetch } from "@/lib/client-fetch";
import {
  defaultFeatureParameters,
  formatParameterInput,
  parseParameterInput,
  validateFeatureParameters,
  type FeatureParameterReadModel,
  type FeatureRegistryFeature,
  type JsonValue,
  type SignalWizardBootstrap,
  type SignalWizardErrorPayload,
  type SignalWizardFeatureSelection,
  type SignalWizardOperator,
  type SignalWizardParameterConstraint,
  type SignalWizardPreviewRequest,
  type SignalWizardPreviewResult,
  type SignalWizardSubmitRequest,
  type SignalWizardSubmitResult,
} from "@/lib/signal-wizard-contracts";

interface RequestFailure {
  message: string;
  reasonCode: string | null;
  status: number;
}

interface FeatureDraft {
  enabled: boolean;
  timeframe: string;
  parameters: Record<string, string>;
}

interface PreparedPreview {
  request: SignalWizardPreviewRequest;
  issues: string[];
}

export function SignalWizardClient() {
  const [bootstrap, setBootstrap] = useState<SignalWizardBootstrap | null>(null);
  const [drafts, setDrafts] = useState<Record<string, FeatureDraft>>({});
  const [loading, setLoading] = useState(true);
  const [loadFailure, setLoadFailure] = useState<RequestFailure | null>(null);
  const [strategyId, setStrategyId] = useState("research-signal-strategy");
  const [baseStrategyVersion, setBaseStrategyVersion] = useState("");
  const [operator, setOperator] = useState<SignalWizardOperator>("gt");
  const [comparisonValue, setComparisonValue] = useState("0");
  const [preview, setPreview] = useState<SignalWizardPreviewResult | null>(null);
  const [previewSubmitting, setPreviewSubmitting] = useState(false);
  const [previewFailure, setPreviewFailure] = useState<RequestFailure | null>(null);
  const [experimentName, setExperimentName] = useState("Signal Wizard research candidate");
  const [submitResult, setSubmitResult] = useState<SignalWizardSubmitResult | null>(null);
  const [submitSubmitting, setSubmitSubmitting] = useState(false);
  const [submitFailure, setSubmitFailure] = useState<RequestFailure | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function initialize() {
      setLoading(true);
      try {
        const response = await fetch(`/api/ai/signal-wizard/preview${fixtureSuffix()}`, {
          cache: "no-store",
          credentials: "same-origin",
        });
        if (!response.ok) throw await responseFailure(response);
        const payload = (await response.json()) as SignalWizardBootstrap;
        if (cancelled) return;
        setBootstrap(payload);
        setDrafts(initialDrafts(payload.features));
        setLoadFailure(null);
      } catch (caught) {
        if (cancelled) return;
        setBootstrap(null);
        setDrafts({});
        setLoadFailure(normalizeFailure(caught, "Signal Wizard registry request failed closed"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void initialize();
    return () => {
      cancelled = true;
    };
  }, []);

  const prepared = useMemo(
    () => preparePreview(
      bootstrap,
      drafts,
      strategyId,
      baseStrategyVersion,
      operator,
      comparisonValue,
    ),
    [bootstrap, drafts, strategyId, baseStrategyVersion, operator, comparisonValue],
  );
  const selectedCount = Object.values(drafts).filter((draft) => draft.enabled).length;
  const blockingWarning = preview?.leakage_warnings.some((warning) => warning.blocking) ?? false;
  const previewVersion = strategyVersion(preview);

  function invalidatePreview() {
    setPreview(null);
    setPreviewFailure(null);
    setSubmitResult(null);
    setSubmitFailure(null);
  }

  function updateDraft(featureId: string, update: Partial<FeatureDraft>) {
    setDrafts((current) => ({
      ...current,
      [featureId]: { ...current[featureId], ...update },
    }));
    invalidatePreview();
  }

  function updateParameter(featureId: string, name: string, value: string) {
    setDrafts((current) => ({
      ...current,
      [featureId]: {
        ...current[featureId],
        parameters: { ...current[featureId].parameters, [name]: value },
      },
    }));
    invalidatePreview();
  }

  async function refreshRegistry() {
    setLoading(true);
    setLoadFailure(null);
    invalidatePreview();
    try {
      const response = await fetch(`/api/ai/signal-wizard/preview${fixtureSuffix()}`, {
        cache: "no-store",
        credentials: "same-origin",
      });
      if (!response.ok) throw await responseFailure(response);
      const payload = (await response.json()) as SignalWizardBootstrap;
      setBootstrap(payload);
      setDrafts(initialDrafts(payload.features));
    } catch (caught) {
      setBootstrap(null);
      setDrafts({});
      setLoadFailure(normalizeFailure(caught, "Signal Wizard registry request failed closed"));
    } finally {
      setLoading(false);
    }
  }

  async function buildPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!prepared.request || prepared.issues.length > 0) return;
    setPreviewSubmitting(true);
    setPreviewFailure(null);
    setSubmitResult(null);
    setSubmitFailure(null);
    try {
      const response = await csrfFetch(`/api/ai/signal-wizard/preview${fixtureSuffix()}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          ...prepared.request,
          idempotency_key: crypto.randomUUID(),
        }),
      });
      if (!response.ok) throw await responseFailure(response);
      setPreview((await response.json()) as SignalWizardPreviewResult);
    } catch (caught) {
      setPreview(null);
      setPreviewFailure(normalizeFailure(caught, "Signal Wizard preview failed closed"));
    } finally {
      setPreviewSubmitting(false);
    }
  }

  async function createExperiment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!preview || !previewVersion || blockingWarning || experimentName.trim().length < 3) return;
    setSubmitSubmitting(true);
    setSubmitFailure(null);
    setSubmitResult(null);
    const request: SignalWizardSubmitRequest = {
      idempotency_key: crypto.randomUUID(),
      strategy_id: strategyId.trim(),
      preview_hash: preview.preview_hash,
      experiment_name: experimentName.trim(),
      expected_strategy_version: previewVersion,
    };
    try {
      const response = await csrfFetch(`/api/ai/signal-wizard/submit${fixtureSuffix()}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
      });
      if (!response.ok) throw await responseFailure(response);
      setSubmitResult((await response.json()) as SignalWizardSubmitResult);
    } catch (caught) {
      setSubmitFailure(normalizeFailure(caught, "Experiment submission failed closed"));
    } finally {
      setSubmitSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="empty-state" role="status">
        <strong>Loading approved Feature Registry…</strong>
        <span>Reading tenant-scoped registry identities and immutable parameter constraints.</span>
      </div>
    );
  }

  if (loadFailure) {
    const denied = loadFailure.status === 401 || loadFailure.status === 403;
    return (
      <div className={`status-banner ${denied ? "status-danger" : "status-warning"}`} role="alert">
        <strong>{denied ? "Signal Wizard access denied" : "Signal Wizard unavailable"}</strong>
        <span>{failureText(loadFailure)}</span>
        <button type="button" className="secondary-button" onClick={() => void refreshRegistry()}>
          Retry registry request
        </button>
      </div>
    );
  }

  if (!bootstrap || bootstrap.features.length === 0) {
    return (
      <div className="empty-state" role="status">
        <strong>No approved AI features are available</strong>
        <span>The current tenant cannot create a preview until the registry exposes approved entries.</span>
        <button type="button" className="secondary-button" onClick={() => void refreshRegistry()}>
          Refresh registry
        </button>
      </div>
    );
  }

  return (
    <div className="page-stack">
      {bootstrap.stale ? (
        <div className="status-banner status-warning" role="alert">
          <strong>Feature Registry snapshot is stale</strong>
          <span>{bootstrap.reason_codes.join(", ") || "Reload before creating a preview."}</span>
        </div>
      ) : null}

      <article className="panel">
        <div className="page-heading">
          <div>
            <span className="eyebrow">Tenant {bootstrap.tenant_id}</span>
            <h2>Approved registry boundary</h2>
          </div>
          <button type="button" className="secondary-button" onClick={() => void refreshRegistry()}>
            Refresh
          </button>
        </div>
        <div className="metric-grid">
          <div><span>Registry version</span><strong>{bootstrap.registry_version}</strong></div>
          <div><span>Approved features</span><strong>{bootstrap.features.length}</strong></div>
          <div><span>Selected features</span><strong>{selectedCount}</strong></div>
          <div><span>Execution authority</span><strong>No</strong></div>
        </div>
      </article>

      <form className="page-stack" onSubmit={buildPreview}>
        <article className="panel">
          <div className="panel-heading">
            <div><span className="eyebrow">Step 1</span><h2>Strategy identity</h2></div>
          </div>
          <div className="form-grid">
            <label>
              Strategy ID
              <input
                value={strategyId}
                onChange={(event) => {
                  setStrategyId(event.target.value);
                  invalidatePreview();
                }}
                required
              />
            </label>
            <label>
              Base strategy version (optional)
              <input
                value={baseStrategyVersion}
                onChange={(event) => {
                  setBaseStrategyVersion(event.target.value);
                  invalidatePreview();
                }}
                placeholder="Existing immutable version"
              />
            </label>
            <label>
              Condition operator
              <select
                value={operator}
                onChange={(event) => {
                  setOperator(event.target.value as SignalWizardOperator);
                  invalidatePreview();
                }}
              >
                <option value="gt">Greater than</option>
                <option value="gte">Greater than or equal</option>
                <option value="lt">Less than</option>
                <option value="lte">Less than or equal</option>
                <option value="eq">Equal</option>
              </select>
            </label>
            <label>
              Comparison value
              <input
                type="number"
                step="any"
                value={comparisonValue}
                onChange={(event) => {
                  setComparisonValue(event.target.value);
                  invalidatePreview();
                }}
                required
              />
            </label>
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div><span className="eyebrow">Step 2</span><h2>Approved feature selection</h2></div>
          </div>
          <div className="page-stack">
            {bootstrap.features.map((feature) => {
              const draft = drafts[feature.feature_id];
              if (!draft) return null;
              const parsed = parseDraftParameters(feature, draft);
              const issues = draft.enabled ? validateFeatureParameters(feature, parsed) : [];
              return (
                <section className="panel" key={feature.feature_id}>
                  <div className="page-heading">
                    <div>
                      <label>
                        <input
                          type="checkbox"
                          aria-label={`Select ${feature.feature_id}`}
                          checked={draft.enabled}
                          onChange={(event) => updateDraft(feature.feature_id, { enabled: event.target.checked })}
                        />
                        {feature.feature_id}
                      </label>
                      <span>{feature.roles.join(", ")} · {feature.status}</span>
                    </div>
                    <span className="freshness">{feature.timestamp_policy}</span>
                  </div>
                  <p>Warmup: {feature.warmup}. Normalization: {feature.normalization_policy}.</p>
                  {feature.dependencies.length > 0 ? (
                    <div className="status-banner status-info">
                      <strong>Explicit dependencies</strong>
                      <span>{feature.dependencies.join(", ")}</span>
                    </div>
                  ) : null}
                  <div className="form-grid">
                    <label>
                      {feature.feature_id} timeframe
                      <input
                        value={draft.timeframe}
                        disabled={!draft.enabled}
                        onChange={(event) => updateDraft(feature.feature_id, { timeframe: event.target.value })}
                        required={draft.enabled}
                      />
                    </label>
                    {feature.parameters.map((parameter) => (
                      <ParameterEditor
                        key={parameter.name}
                        featureId={feature.feature_id}
                        parameter={parameter}
                        value={draft.parameters[parameter.name] ?? ""}
                        disabled={!draft.enabled}
                        onChange={(value) => updateParameter(feature.feature_id, parameter.name, value)}
                      />
                    ))}
                  </div>
                  {feature.constraints.length > 0 ? (
                    <p>Registry constraints: {feature.constraints.join(", ")}</p>
                  ) : null}
                  {issues.length > 0 ? (
                    <div className="status-banner status-danger" role="alert">
                      <strong>Parameter constraints are not satisfied</strong>
                      <span>{issues.map((issue) => `${issue.reason_code}: ${issue.message}`).join(" · ")}</span>
                    </div>
                  ) : null}
                </section>
              );
            })}
          </div>
        </article>

        {prepared.issues.length > 0 ? (
          <div className="status-banner status-danger" role="alert">
            <strong>Preview validation is incomplete</strong>
            <span>{prepared.issues.join(" · ")}</span>
          </div>
        ) : null}

        <button
          className="primary-button"
          type="submit"
          disabled={previewSubmitting || prepared.issues.length > 0 || bootstrap.stale}
        >
          {previewSubmitting ? "Validating preview…" : "Build strategy preview"}
        </button>
      </form>

      {previewFailure ? (
        <div className="status-banner status-danger" role="alert">
          <strong>Strategy preview blocked</strong>
          <span>{failureText(previewFailure)}</span>
        </div>
      ) : null}

      {preview ? (
        <>
          <article className="panel">
            <div className="page-heading">
              <div><span className="eyebrow">Step 3</span><h2>Preview validated</h2></div>
              <span className="freshness">{shortHash(preview.preview_hash)}</span>
            </div>
            <div className="metric-grid">
              <div><span>Strategy version</span><strong>{previewVersion ?? "Unavailable"}</strong></div>
              <div><span>Reason codes</span><strong>{preview.reason_codes.join(", ")}</strong></div>
              <div><span>Execution authority</span><strong>{preview.execution_authority ? "Yes" : "No"}</strong></div>
              <div><span>Promotion authority</span><strong>{preview.promotion_authority ? "Yes" : "No"}</strong></div>
            </div>
            {preview.leakage_warnings.length === 0 ? (
              <div className="status-banner status-info" role="status">
                <strong>No leakage or repaint warning blocks submission</strong>
                <span>Canonical validation confirmed closed or explicitly confirmed-bar semantics.</span>
              </div>
            ) : (
              <div className="page-stack">
                {preview.leakage_warnings.map((warning) => (
                  <div
                    className={`status-banner ${warning.blocking ? "status-danger" : "status-warning"}`}
                    role={warning.blocking ? "alert" : "status"}
                    key={`${warning.reason_code}:${warning.field_path}`}
                  >
                    <strong>{warning.reason_code}{warning.blocking ? " · Blocking" : ""}</strong>
                    <span>{warning.field_path}: {warning.message}</span>
                  </div>
                ))}
              </div>
            )}
            <details>
              <summary>Canonical StrategyDefinition preview</summary>
              <pre style={{ overflowX: "auto", whiteSpace: "pre-wrap" }}>
                {JSON.stringify(preview.strategy_definition, null, 2)}
              </pre>
            </details>
          </article>

          <form className="panel" onSubmit={createExperiment}>
            <div className="panel-heading">
              <div><span className="eyebrow">Step 4</span><h2>Create research experiment</h2></div>
            </div>
            <div className="form-safety">
              <strong>Experiment intent only</strong>
              <span>Submit creates a candidate experiment. It cannot deploy, execute trades or promote a model.</span>
            </div>
            <label>
              Experiment name
              <input
                value={experimentName}
                minLength={3}
                onChange={(event) => {
                  setExperimentName(event.target.value);
                  setSubmitResult(null);
                  setSubmitFailure(null);
                }}
                required
              />
            </label>
            <button
              className="primary-button"
              type="submit"
              disabled={submitSubmitting || blockingWarning || experimentName.trim().length < 3}
            >
              {submitSubmitting ? "Creating experiment…" : "Create research experiment"}
            </button>
          </form>
        </>
      ) : null}

      {submitFailure ? (
        <div className="status-banner status-danger" role="alert">
          <strong>Experiment submission blocked</strong>
          <span>{failureText(submitFailure)}</span>
        </div>
      ) : null}

      {submitResult ? (
        <article className="panel">
          <div className="page-heading">
            <div><span className="eyebrow">Complete</span><h2>Experiment accepted</h2></div>
            <span className="freshness">{submitResult.experiment_id}</span>
          </div>
          <div className="metric-grid">
            <div><span>Accepted</span><strong>{submitResult.accepted ? "Yes" : "No"}</strong></div>
            <div><span>Reason codes</span><strong>{submitResult.reason_codes.join(", ")}</strong></div>
            <div><span>Execution authority</span><strong>No</strong></div>
            <div><span>Promotion authority</span><strong>No</strong></div>
          </div>
        </article>
      ) : null}
    </div>
  );
}

function ParameterEditor({
  featureId,
  parameter,
  value,
  disabled,
  onChange,
}: {
  featureId: string;
  parameter: FeatureParameterReadModel;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  const label = `${featureId} ${parameter.name}`;
  const choices = parameter.choices.length > 0
    ? parameter.choices.map(formatParameterInput)
    : parameter.kinds.includes("boolean")
      ? ["true", "false"]
      : [];
  if (choices.length > 0) {
    return (
      <label>
        {label}
        <select value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)}>
          {choices.map((choice) => <option key={choice} value={choice}>{choice}</option>)}
        </select>
      </label>
    );
  }
  const numeric = parameter.kinds.includes("integer") || parameter.kinds.includes("number");
  return (
    <label>
      {label}
      <input
        type={numeric ? "number" : "text"}
        min={parameter.minimum ?? undefined}
        max={parameter.maximum ?? undefined}
        step={parameter.kinds.includes("integer") ? 1 : numeric ? "any" : undefined}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      />
      <span>{constraintText(parameter)}</span>
    </label>
  );
}

function preparePreview(
  bootstrap: SignalWizardBootstrap | null,
  drafts: Record<string, FeatureDraft>,
  strategyId: string,
  baseStrategyVersion: string,
  operator: SignalWizardOperator,
  comparisonValue: string,
): PreparedPreview {
  const issues: string[] = [];
  if (!bootstrap) return { request: null as never, issues: ["Feature Registry is unavailable"] };
  if (!strategyId.trim()) issues.push("Strategy ID is required");
  const numericComparison = Number(comparisonValue);
  if (!Number.isFinite(numericComparison)) issues.push("Comparison value must be a finite number");
  const selections: SignalWizardFeatureSelection[] = [];
  const selectedDefinitions: FeatureRegistryFeature[] = [];
  for (const feature of bootstrap.features) {
    const draft = drafts[feature.feature_id];
    if (!draft?.enabled) continue;
    if (!draft.timeframe.trim()) issues.push(`${feature.feature_id} requires a timeframe`);
    const parameters = parseDraftParameters(feature, draft);
    for (const issue of validateFeatureParameters(feature, parameters)) {
      issues.push(`${issue.reason_code}: ${issue.message}`);
    }
    selections.push({
      contract_version: "v2",
      feature_id: feature.feature_id,
      timeframe: draft.timeframe.trim(),
      parameters,
      enabled: true,
    });
    selectedDefinitions.push(feature);
  }
  if (selections.length === 0) issues.push("Select at least one approved feature");
  const request: SignalWizardPreviewRequest = {
    idempotency_key: "generated-at-submit",
    strategy_id: strategyId.trim(),
    base_strategy_version: baseStrategyVersion.trim() || null,
    registry_version: bootstrap.registry_version,
    snapshot_sha256: bootstrap.snapshot_sha256,
    feature_selections: selections,
    parameter_constraints: requestedConstraints(selectedDefinitions),
    condition_ast: {
      all: selections.map((selection) => ({
        feature: selection.feature_id,
        op: operator,
        value: numericComparison,
      })),
    },
  };
  return { request, issues };
}

function requestedConstraints(features: FeatureRegistryFeature[]): SignalWizardParameterConstraint[] {
  const counts = new Map<string, number>();
  for (const feature of features) {
    for (const parameter of feature.parameters) {
      counts.set(parameter.name, (counts.get(parameter.name) ?? 0) + 1);
    }
  }
  return features.flatMap((feature) =>
    feature.parameters
      .filter((parameter) => counts.get(parameter.name) === 1)
      .filter(
        (parameter) =>
          parameter.minimum !== null || parameter.maximum !== null || parameter.choices.length > 0,
      )
      .map((parameter) => ({
        contract_version: "v2" as const,
        parameter: parameter.name,
        minimum: parameter.minimum,
        maximum: parameter.maximum,
        allowed_values: parameter.choices,
        reason_code: "FEATURE_PARAMETER_REGISTRY_CONSTRAINT",
      })),
  );
}

function initialDrafts(features: FeatureRegistryFeature[]): Record<string, FeatureDraft> {
  return Object.fromEntries(
    features.map((feature) => [
      feature.feature_id,
      {
        enabled: false,
        timeframe: "5m",
        parameters: Object.fromEntries(
          Object.entries(defaultFeatureParameters(feature)).map(([name, value]) => [
            name,
            formatParameterInput(value),
          ]),
        ),
      },
    ]),
  );
}

function parseDraftParameters(
  feature: FeatureRegistryFeature,
  draft: FeatureDraft,
): Record<string, JsonValue> {
  return Object.fromEntries(
    feature.parameters.map((parameter) => [
      parameter.name,
      parseParameterInput(parameter, draft.parameters[parameter.name] ?? ""),
    ]),
  );
}

async function responseFailure(response: Response): Promise<RequestFailure> {
  let payload: SignalWizardErrorPayload | null = null;
  try {
    payload = (await response.json()) as SignalWizardErrorPayload;
  } catch {
    payload = null;
  }
  return {
    message: payload?.detail ?? `Signal Wizard request failed with status ${response.status}`,
    reasonCode: payload?.reason_code ?? payload?.code ?? null,
    status: response.status,
  };
}

function normalizeFailure(caught: unknown, fallback: string): RequestFailure {
  const value = caught as Partial<RequestFailure>;
  return {
    message: value.message ?? fallback,
    reasonCode: value.reasonCode ?? null,
    status: value.status ?? 502,
  };
}

function failureText(failure: RequestFailure): string {
  return failure.reasonCode ? `${failure.reasonCode}: ${failure.message}` : failure.message;
}

function fixtureSuffix(): string {
  if (typeof window === "undefined") return "";
  const value = new URLSearchParams(window.location.search).get("wizard_view");
  return value ? `?view=${encodeURIComponent(value)}` : "";
}

function strategyVersion(preview: SignalWizardPreviewResult | null): string | null {
  const value = preview?.strategy_definition.version;
  return typeof value === "string" && value ? value : null;
}

function shortHash(value: string): string {
  return value.length > 20 ? `${value.slice(0, 12)}…${value.slice(-6)}` : value;
}

function constraintText(parameter: FeatureParameterReadModel): string {
  const parts: string[] = [];
  if (parameter.minimum !== null) parts.push(`min ${parameter.minimum}`);
  if (parameter.maximum !== null) parts.push(`max ${parameter.maximum}`);
  return parts.join(" · ") || "Registry-typed value";
}
