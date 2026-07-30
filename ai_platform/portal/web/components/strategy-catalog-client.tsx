"use client";

import { useEffect, useState, type FormEvent } from "react";

import { StatusPill } from "@/components/status-pill";
import { csrfFetch } from "@/lib/client-fetch";
import type {
  StrategyCatalogDetail,
  StrategyCatalogErrorPayload,
  StrategyCatalogListResponse,
  StrategyRollbackResult,
} from "@/lib/strategy-catalog-contracts";

interface RequestFailure {
  message: string;
  status: number;
}

function formatDate(value: string | null): string {
  if (!value) return "Pending";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}

function shortHash(value: string): string {
  return value.length > 18 ? `${value.slice(0, 10)}…${value.slice(-6)}` : value;
}

async function responseFailure(response: Response): Promise<RequestFailure> {
  let payload: StrategyCatalogErrorPayload | null = null;
  try {
    payload = (await response.json()) as StrategyCatalogErrorPayload;
  } catch {
    payload = null;
  }
  return {
    message: payload?.detail ?? `Strategy Catalog request failed with status ${response.status}`,
    status: response.status,
  };
}

function normalizeFailure(caught: unknown, fallback: string): RequestFailure {
  const failure = caught as Partial<RequestFailure>;
  return {
    message: failure.message ?? fallback,
    status: failure.status ?? 502,
  };
}

async function requestCatalog(): Promise<StrategyCatalogListResponse> {
  const view = new URLSearchParams(window.location.search).get("catalog_view");
  const suffix = view ? `?view=${encodeURIComponent(view)}` : "";
  const response = await fetch(`/api/strategy-catalog${suffix}`, {
    cache: "no-store",
    credentials: "same-origin",
  });
  if (!response.ok) throw await responseFailure(response);
  return (await response.json()) as StrategyCatalogListResponse;
}

async function requestDetail(strategyVersion: string): Promise<StrategyCatalogDetail> {
  const response = await fetch(
    `/api/strategy-catalog/${encodeURIComponent(strategyVersion)}`,
    { cache: "no-store", credentials: "same-origin" },
  );
  if (!response.ok) throw await responseFailure(response);
  return (await response.json()) as StrategyCatalogDetail;
}

export function StrategyCatalogClient() {
  const [catalog, setCatalog] = useState<StrategyCatalogListResponse | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);
  const [detail, setDetail] = useState<StrategyCatalogDetail | null>(null);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [catalogFailure, setCatalogFailure] = useState<RequestFailure | null>(null);
  const [detailFailure, setDetailFailure] = useState<RequestFailure | null>(null);
  const [rollbackSubmitting, setRollbackSubmitting] = useState(false);
  const [rollbackFailure, setRollbackFailure] = useState<RequestFailure | null>(null);
  const [rollbackResult, setRollbackResult] = useState<StrategyRollbackResult | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const payload = await requestCatalog();
        if (cancelled) return;
        const initialVersion = payload.entries[0]?.strategy_version ?? null;
        setCatalog(payload);
        setSelectedVersion(initialVersion);
        setCatalogFailure(null);
        setCatalogLoading(false);
        if (!initialVersion) {
          setDetail(null);
          return;
        }

        setDetailLoading(true);
        try {
          const initialDetail = await requestDetail(initialVersion);
          if (cancelled) return;
          setDetail(initialDetail);
          setDetailFailure(null);
        } catch (caught) {
          if (cancelled) return;
          setDetail(null);
          setDetailFailure(normalizeFailure(caught, "Strategy detail request failed closed"));
        } finally {
          if (!cancelled) setDetailLoading(false);
        }
      } catch (caught) {
        if (cancelled) return;
        setCatalog(null);
        setDetail(null);
        setSelectedVersion(null);
        setCatalogFailure(normalizeFailure(caught, "Strategy Catalog request failed closed"));
        setCatalogLoading(false);
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, []);

  async function loadSelectedDetail(strategyVersion: string) {
    setSelectedVersion(strategyVersion);
    setDetailLoading(true);
    setDetailFailure(null);
    setRollbackFailure(null);
    setRollbackResult(null);
    try {
      setDetail(await requestDetail(strategyVersion));
    } catch (caught) {
      setDetail(null);
      setDetailFailure(normalizeFailure(caught, "Strategy detail request failed closed"));
    } finally {
      setDetailLoading(false);
    }
  }

  async function refreshCatalog() {
    setCatalogLoading(true);
    setCatalogFailure(null);
    setRollbackFailure(null);
    setRollbackResult(null);
    try {
      const payload = await requestCatalog();
      const retainedVersion =
        selectedVersion && payload.entries.some((entry) => entry.strategy_version === selectedVersion)
          ? selectedVersion
          : (payload.entries[0]?.strategy_version ?? null);
      setCatalog(payload);
      setSelectedVersion(retainedVersion);
      if (retainedVersion) {
        await loadSelectedDetail(retainedVersion);
      } else {
        setDetail(null);
        setDetailFailure(null);
      }
    } catch (caught) {
      setCatalog(null);
      setDetail(null);
      setSelectedVersion(null);
      setCatalogFailure(normalizeFailure(caught, "Strategy Catalog request failed closed"));
    } finally {
      setCatalogLoading(false);
    }
  }

  async function submitRollback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    setRollbackSubmitting(true);
    setRollbackFailure(null);
    setRollbackResult(null);
    const form = new FormData(event.currentTarget);
    const target = String(form.get("target_version") ?? "").trim();
    const reason = String(form.get("reason") ?? "").trim();
    try {
      const response = await csrfFetch(
        `/api/strategy-catalog/${encodeURIComponent(detail.entry.strategy_version)}/rollback`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            to_strategy_version: target,
            reason,
            idempotency_key: crypto.randomUUID(),
          }),
        },
      );
      if (!response.ok) throw await responseFailure(response);
      setRollbackResult((await response.json()) as StrategyRollbackResult);
    } catch (caught) {
      setRollbackFailure(normalizeFailure(caught, "Rollback request failed closed"));
    } finally {
      setRollbackSubmitting(false);
    }
  }

  if (catalogLoading) {
    return (
      <div className="empty-state" role="status">
        <strong>Loading Strategy Catalog…</strong>
        <span>Reading tenant-scoped lifecycle and evidence records.</span>
      </div>
    );
  }

  if (catalogFailure) {
    const denied = catalogFailure.status === 401 || catalogFailure.status === 403;
    return (
      <div className={`status-banner ${denied ? "status-danger" : "status-warning"}`} role="alert">
        <strong>{denied ? "Strategy Catalog access denied" : "Strategy Catalog unavailable"}</strong>
        <span>{catalogFailure.message}</span>
        <button type="button" className="secondary-button" onClick={() => void refreshCatalog()}>
          Retry catalog request
        </button>
      </div>
    );
  }

  if (!catalog || catalog.entries.length === 0) {
    return (
      <div className="empty-state" role="status">
        <strong>No strategy versions are available</strong>
        <span>The tenant has no catalog entries that the current session may read.</span>
        <button type="button" className="secondary-button" onClick={() => void refreshCatalog()}>
          Refresh catalog
        </button>
      </div>
    );
  }

  return (
    <div className="page-stack">
      {catalog.stale ? (
        <div className="status-banner status-warning" role="status">
          <strong>Catalog snapshot is stale</strong>
          <span>{catalog.reason_codes.join(", ") || "Refresh before making a lifecycle decision."}</span>
        </div>
      ) : null}

      <article className="panel">
        <div className="page-heading">
          <div>
            <span className="eyebrow">Tenant {catalog.tenant_id}</span>
            <h2>Immutable strategy versions</h2>
          </div>
          <button type="button" className="secondary-button" onClick={() => void refreshCatalog()}>
            Refresh
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Version</th>
                <th>Lifecycle</th>
                <th>Revision</th>
                <th>Modes</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {catalog.entries.map((entry) => (
                <tr key={entry.strategy_version}>
                  <td>
                    <button
                      type="button"
                      className="link-button"
                      aria-pressed={selectedVersion === entry.strategy_version}
                      onClick={() => void loadSelectedDetail(entry.strategy_version)}
                    >
                      {entry.display_name}
                    </button>
                    <span>{entry.description}</span>
                  </td>
                  <td>{entry.strategy_version}</td>
                  <td><StatusPill value={entry.lifecycle_state} /></td>
                  <td>{entry.current_revision}</td>
                  <td>{entry.allowed_execution_modes.join(", ")}</td>
                  <td>{entry.provenance_ref ?? "Unavailable"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>

      {detailLoading ? (
        <div className="empty-state" role="status">
          <strong>Loading version evidence…</strong>
          <span>Resolving history, approvals, deployments and rollback targets.</span>
        </div>
      ) : null}

      {detailFailure ? (
        <div className="status-banner status-danger" role="alert">
          <strong>Strategy detail unavailable</strong>
          <span>{detailFailure.message}</span>
          {selectedVersion ? (
            <button
              type="button"
              className="secondary-button"
              onClick={() => void loadSelectedDetail(selectedVersion)}
            >
              Retry detail request
            </button>
          ) : null}
        </div>
      ) : null}

      {detail ? (
        <>
          <article className="panel">
            <div className="page-heading">
              <div>
                <span className="eyebrow">Selected immutable identity</span>
                <h2>{detail.entry.display_name} · {detail.entry.strategy_version}</h2>
              </div>
              <StatusPill value={detail.entry.lifecycle_state} />
            </div>
            <div className="metric-grid">
              <div><span>Tenant</span><strong>{detail.tenant_id}</strong></div>
              <div><span>Immutable</span><strong>{detail.entry.immutable ? "Yes" : "No"}</strong></div>
              <div><span>Approval required</span><strong>{detail.entry.approval_required ? "Yes" : "No"}</strong></div>
              <div><span>Live capital authority</span><strong>No</strong></div>
            </div>
            <div className="status-banner status-info">
              <strong>Capabilities remain backend-authoritative</strong>
              <span>{detail.required_capabilities.join(", ")}</span>
            </div>
          </article>

          <article className="panel">
            <h2>Version history</h2>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Revision</th><th>Version</th><th>State</th><th>Immutable hash</th><th>Created</th><th>Actor</th></tr></thead>
                <tbody>
                  {[...detail.history].sort((a, b) => b.revision - a.revision).map((item) => (
                    <tr key={item.strategy_version}>
                      <td>{item.revision}</td>
                      <td>{item.strategy_version}</td>
                      <td><StatusPill value={item.lifecycle_state} /></td>
                      <td title={item.immutable_hash}>{shortHash(item.immutable_hash)}</td>
                      <td>{formatDate(item.created_at)}</td>
                      <td>{item.created_by_actor_id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="panel">
            <h2>Approval evidence</h2>
            {detail.approvals.length === 0 ? (
              <div className="empty-state" role="status">
                <strong>No approval record</strong>
                <span>Deployment remains unavailable until canonical approval evidence exists.</span>
              </div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Decision</th><th>Approval ID</th><th>Reason codes</th><th>Decision actor</th><th>Decided</th></tr></thead>
                  <tbody>{detail.approvals.map((approval) => (
                    <tr key={approval.approval_id}>
                      <td><StatusPill value={approval.decision} /></td>
                      <td>{approval.approval_id}</td>
                      <td>{approval.reason_codes.join(", ") || "None"}</td>
                      <td>{approval.decided_by_actor_id ?? "Pending"}</td>
                      <td>{formatDate(approval.decided_at)}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            )}
          </article>

          <article className="panel">
            <h2>Paper and shadow deployments</h2>
            {detail.deployments.length === 0 ? (
              <div className="empty-state" role="status">
                <strong>No paper or shadow deployment</strong>
                <span>This strategy version has not entered a permitted deployment lifecycle.</span>
              </div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Mode</th><th>State</th><th>Version</th><th>Environment</th><th>Deployed</th><th>Live capital</th></tr></thead>
                  <tbody>{detail.deployments.map((deployment) => (
                    <tr key={deployment.deployment_id}>
                      <td><StatusPill value={deployment.mode} /></td>
                      <td><StatusPill value={deployment.state} /></td>
                      <td>{deployment.strategy_version}</td>
                      <td>{deployment.environment}</td>
                      <td>{formatDate(deployment.deployed_at)}</td>
                      <td>{deployment.live_capital_authority ? "Yes" : "No"}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            )}
          </article>

          <article className="panel">
            <h2>Provenance</h2>
            <div className="metric-grid">
              <div><span>Producer</span><strong>{detail.provenance.producer}</strong></div>
              <div><span>Artifact</span><strong>{detail.provenance.artifact_id}</strong></div>
              <div><span>Created</span><strong>{formatDate(detail.provenance.created_at)}</strong></div>
              <div><span>Contract</span><strong>{detail.provenance.contract_version}</strong></div>
            </div>
            <p>Source references: {detail.provenance.source_refs.join(", ") || "None"}</p>
          </article>

          <article className="panel">
            <h2>Rollback evidence action</h2>
            {detail.rollback_targets.length === 0 || !detail.required_capabilities.includes("strategy.rollback_dry_run") ? (
              <div className="empty-state" role="status">
                <strong>Rollback unavailable</strong>
                <span>No canonical rollback target and capability are available for this version.</span>
              </div>
            ) : (
              <form className="bot-form" onSubmit={submitRollback}>
                <div className="form-grid">
                  <label>
                    Target version
                    <select name="target_version" required defaultValue={detail.rollback_targets[0]}>
                      {detail.rollback_targets.map((target) => (
                        <option key={target} value={target}>{target}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Evidence reason
                    <textarea
                      name="reason"
                      defaultValue="Restore the last reviewed dry-run version after shadow evidence review."
                      minLength={8}
                      required
                    />
                  </label>
                </div>
                <div className="form-safety">
                  <strong>Dry-run and shadow rollback only</strong>
                  <span>The server rechecks tenant, capability, source version, target version and audit evidence. This action grants no execution or live-capital authority.</span>
                </div>
                <button className="primary-button" type="submit" disabled={rollbackSubmitting}>
                  {rollbackSubmitting ? "Recording rollback…" : "Request evidence-backed rollback"}
                </button>
              </form>
            )}
            {rollbackResult ? (
              <div className="success-message" role="status">
                <strong>Rollback evidence {rollbackResult.evidence_state}</strong>
                <span>Source: {rollbackResult.source_strategy_version}</span>
                <span>Target: {rollbackResult.target_strategy_version}</span>
                <span>Audit reference: {rollbackResult.audit_evidence_ref}</span>
                <span>Result: {rollbackResult.reason_codes.join(", ")}</span>
                <span>Live capital authority: no</span>
              </div>
            ) : null}
            {rollbackFailure ? (
              <p className="error-message" role="alert">
                Rollback conflict or denial: {rollbackFailure.message}
              </p>
            ) : null}
          </article>
        </>
      ) : null}
    </div>
  );
}
