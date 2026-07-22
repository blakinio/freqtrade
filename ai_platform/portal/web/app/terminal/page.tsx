import { cookies } from "next/headers";

import { TerminalForm } from "@/components/terminal-form";
import { listBots } from "@/lib/portal-api";

export default async function TerminalPage() {
  const cookieHeader = (await cookies()).toString();
  const bots = await listBots(cookieHeader);
  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Trading Terminal</span>
          <h1>Risk-gated manual intent</h1>
        </div>
      </div>
      <article className="panel">
        <p>
          Manual actions create intent only. The server resolves the bot&apos;s immutable risk policy and trusted runtime snapshot before any approved intent can reach the private execution boundary.
        </p>
        <TerminalForm bots={bots} />
      </article>
    </section>
  );
}
