"use client";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <section className="state-page" role="alert">
      <span className="eyebrow">Unavailable</span>
      <h1>Portal data could not be loaded</h1>
      <p>The request failed closed. No trading runtime action was attempted.</p>
      <button className="primary-button" onClick={() => reset()} type="button">Try again</button>
    </section>
  );
}
