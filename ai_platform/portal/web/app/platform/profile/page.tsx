import { cookies } from "next/headers";

import { getProfileSecurity } from "@/lib/product-api";

export default async function ProfileSecurityPage() {
  const cookieHeader = (await cookies()).toString();
  const profile = await getProfileSecurity(cookieHeader);

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><span className="eyebrow">Platform</span><h1>Profile & Security</h1></div>
        <span className="freshness">Trusted authenticated identity context</span>
      </div>
      <div className="status-banner status-info">
        <strong>Identity-provider boundary</strong>
        <span>MFA enrollment, credential changes and session revocation remain owned by the external identity provider. The portal exposes no passwords, tokens or secret values.</span>
      </div>
      <div className="metric-grid">
        <article className="metric-card"><span>Actor</span><strong>{profile.actor_id}</strong><small>{profile.actor_type}</small></article>
        <article className="metric-card"><span>Tenant</span><strong>{profile.tenant_id}</strong><small>Tenant scoped</small></article>
        <article className="metric-card"><span>MFA</span><strong>External</strong><small>{profile.mfa_status}</small></article>
        <article className="metric-card"><span>Secrets exposed</span><strong>{profile.secrets_exposed ? "Yes" : "No"}</strong><small>Application contract</small></article>
      </div>
      <article className="panel">
        <div className="panel-heading"><div><span className="eyebrow">Authorization</span><h2>Granted portal permissions</h2></div></div>
        {profile.permissions.length === 0 ? (
          <div className="empty-state"><strong>No portal permissions</strong><span>The authenticated identity currently has no granted product permissions.</span></div>
        ) : (
          <div className="table-wrap"><table>
            <thead><tr><th>Permission</th><th>Boundary</th></tr></thead>
            <tbody>{profile.permissions.map((permission) => <tr key={permission}><td>{permission}</td><td>{profile.authentication_boundary}</td></tr>)}</tbody>
          </table></div>
        )}
      </article>
    </section>
  );
}
