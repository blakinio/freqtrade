import Link from "next/link";

import { safeReturnTo } from "@/lib/identity";

const reasonMessages: Record<string, string> = {
  session_missing: "A portal session is required to continue.",
  session_expired: "Your portal session expired. Sign in again to continue.",
  session_revoked: "Your portal session is no longer active. Sign in again to continue.",
  session_required: "A portal session is required to continue.",
  logged_out: "You have been signed out of this portal session.",
  logout_all: "All portal sessions for this identity were revoked.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const parameters = await searchParams;
  const returnTo = safeReturnTo(first(parameters.return_to));
  const reason = first(parameters.reason) ?? "session_required";
  const message = reasonMessages[reason] ?? reasonMessages.session_required;
  const loginUrl = `/api/identity/login?return_to=${encodeURIComponent(returnTo)}`;

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Product identity</span>
          <h1>Sign in to AI Trading Portal</h1>
        </div>
      </div>
      <div className="status-banner status-info">
        <strong>Secure application session required</strong>
        <span>{message}</span>
      </div>
      <article className="panel surface-card">
        <p>
          Authentication and MFA are completed by the configured identity provider. The browser
          receives only an opaque portal session cookie; IdP access, ID and refresh tokens are not
          stored in browser-readable storage.
        </p>
        <Link className="primary-button" href={loginUrl}>
          Continue to identity provider
        </Link>
        <p className="freshness">
          Cloudflare Access may protect privileged ingress, but portal-owned membership and
          capability checks remain authoritative.
        </p>
      </article>
    </section>
  );
}

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}
