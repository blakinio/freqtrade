export default function DeniedPage() {
  return (
    <section className="state-page">
      <span className="eyebrow">Access denied</span>
      <h1>You do not have permission to view this resource</h1>
      <p>Authorization is enforced by the portal API. Navigation visibility is not an authorization boundary.</p>
    </section>
  );
}
