export default function Loading() {
  return (
    <section className="page-stack" aria-busy="true">
      <div className="skeleton skeleton-title" />
      <div className="metric-grid">
        {Array.from({ length: 5 }, (_, index) => <div className="metric-card skeleton" key={index} />)}
      </div>
      <div className="panel skeleton skeleton-panel" />
    </section>
  );
}
