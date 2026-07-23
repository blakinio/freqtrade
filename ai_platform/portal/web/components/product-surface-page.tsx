import type { ProductSurfaceConfig } from "@/lib/product-surfaces";

function integrationMessage(
  surface: ProductSurfaceConfig,
  mode: "api" | "fixture",
): { title: string; detail: string; tone: string } {
  if (surface.availability === "shell") {
    return {
      title: "Interface shell available",
      detail: "This surface is intentionally non-mutating until its server-side capability contract is implemented and authorized.",
      tone: "status-info",
    };
  }
  if (surface.availability === "fixture-preview" || mode === "fixture") {
    return {
      title: "Deterministic preview data",
      detail: "This view is using explicit fixture data for development and E2E only. It is not live trading evidence.",
      tone: "status-preview",
    };
  }
  return {
    title: "Canonical read API not available yet",
    detail: "The UI route is delivered, but API mode fails closed and does not invent records until the owning backend exposes an attributable read model.",
    tone: "status-warning",
  };
}

export function ProductSurfacePage({
  surface,
  mode,
}: {
  surface: ProductSurfaceConfig;
  mode: "api" | "fixture";
}) {
  const message = integrationMessage(surface, mode);
  const showFixtureTable = mode === "fixture" && surface.fixtureTable;

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <span className="eyebrow">{surface.eyebrow}</span>
          <h1>{surface.title}</h1>
        </div>
        <span className="freshness">{surface.phase}</span>
      </div>

      <p className="page-lede">{surface.description}</p>

      <div className={`status-banner ${message.tone}`} role="status">
        <strong>{message.title}</strong>
        <span>{message.detail}</span>
      </div>

      <div className="surface-grid">
        {surface.sections.map((section) => (
          <article className="panel surface-card" key={section.title}>
            <div className="panel-heading">
              <div><h2>{section.title}</h2></div>
            </div>
            <p>{section.description}</p>
            <ul className="capability-list">
              {section.items.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>
        ))}
      </div>

      {showFixtureTable ? (
        <article className="panel">
          <div className="panel-heading">
            <div><span className="eyebrow">Fixture preview</span><h2>Deterministic sample</h2></div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>{surface.fixtureTable?.columns.map((column) => <th key={column}>{column}</th>)}</tr>
              </thead>
              <tbody>
                {surface.fixtureTable?.rows.map((row, rowIndex) => (
                  <tr key={`${surface.path}-${rowIndex}`}>
                    {row.map((cell, cellIndex) => <td key={`${rowIndex}-${cellIndex}`}>{cell}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      ) : null}
    </section>
  );
}
