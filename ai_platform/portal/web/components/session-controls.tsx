"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { csrfFetch } from "@/lib/client-fetch";
import type { PortalSessionView } from "@/lib/identity";

export function SessionControls() {
  const [session, setSession] = useState<PortalSessionView | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<"logout" | "logout-all" | null>(null);

  useEffect(() => {
    let active = true;
    void fetch("/api/identity/session", { cache: "no-store" })
      .then(async (response) => (response.ok ? ((await response.json()) as PortalSessionView) : null))
      .then((value) => {
        if (active) setSession(value);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function revoke(endpoint: "/api/identity/logout" | "/api/identity/logout-all") {
    const mode = endpoint.endsWith("logout-all") ? "logout-all" : "logout";
    setPending(mode);
    try {
      const response = await csrfFetch(endpoint, { method: "POST" });
      if (!response.ok) return;
      window.location.assign(`/login?reason=${mode === "logout-all" ? "logout_all" : "logged_out"}`);
    } finally {
      setPending(null);
    }
  }

  if (loading) return <span className="freshness">Checking portal session…</span>;
  if (!session) {
    return (
      <Link className="primary-button" href="/login">
        Sign in
      </Link>
    );
  }

  return (
    <div className="session-controls" aria-label="Portal session">
      <span>
        Tenant <strong>{session.tenant_id}</strong> · MFA {session.mfa_satisfied ? "verified" : "required"}
      </span>
      <button
        type="button"
        disabled={pending !== null}
        onClick={() => revoke("/api/identity/logout")}
      >
        {pending === "logout" ? "Signing out…" : "Sign out"}
      </button>
      <button
        type="button"
        disabled={pending !== null}
        onClick={() => revoke("/api/identity/logout-all")}
      >
        {pending === "logout-all" ? "Revoking…" : "Sign out all"}
      </button>
    </div>
  );
}
