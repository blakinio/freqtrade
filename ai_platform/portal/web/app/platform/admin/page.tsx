import { cookies } from "next/headers";

import { getAdministrationOverview } from "@/lib/product-api";
import { PortalApiResponseError } from "@/lib/portal-api";

export default async function AdministrationPage() {
  const cookieHeader = (await cookies()).toString();
  try {
    const overview = await getAdministrationOverview(cookieHeader);
    return (
      <section className="page-stack">
        <div className="page-heading">
          <div><span className="eyebrow">Platform</span><h1>Administration</h1></div>
          <span className="freshness">Permission-gated authorization overview</span>
        </div>
        <div className="status-banner status-info">
          <strong>Membership boundary</strong>
          <span>Tenant membership remains sourced from the external identity provider. This surface exposes portal role definitions and effective permissions, not credentials.</span>
        </div>
        <article className="panel">
          <div className="panel-heading"><div><span className="eyebrow">Built-in RBAC</span><h2>Roles and permissions</h2></div></div>
          <div className="table-wrap"><table>
            <thead><tr><th>Role</th><th>Role ID</th><th>Permissions</th></tr></thead>
            <tbody>{overview.builtin_roles.map((role) => <tr key={role.role_id}>
              <td><strong>{role.name}</strong></td>
              <td>{role.role_id}</td>
              <td>{role.permissions.join(", ")}</td>
            </tr>)}</tbody>
          </table></div>
        </article>
      </section>
    );
  } catch (error) {
    if (error instanceof PortalApiResponseError && error.status === 403) {
      return (
        <section className="page-stack">
          <div className="page-heading"><div><span className="eyebrow">Platform</span><h1>Administration</h1></div></div>
          <div className="status-banner status-warning">
            <strong>Authorization denied</strong>
            <span>This identity does not have admin.manage. Administration data remains inaccessible.</span>
          </div>
        </section>
      );
    }
    throw error;
  }
}
