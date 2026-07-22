import Link from "next/link";
import type { ReactNode } from "react";

import { portalEnvironment } from "@/lib/portal-api";
import { EnvironmentBadge } from "./environment-badge";

const navigation = [
  { href: "/", label: "Dashboard" },
  { href: "/bots", label: "Bots" },
  { href: "/bots/new", label: "Create Bot" },
  { href: "/terminal", label: "Trading Terminal" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const environment = portalEnvironment();
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">FT</span>
          <div>
            <strong>AI Trading Portal</strong>
            <span>Operations console</span>
          </div>
        </div>
        <nav className="primary-nav">
          {navigation.map((item) => (
            <Link key={item.href} href={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-note">
          <strong>Private execution boundary</strong>
          <span>Trading runtimes are never browser-addressable.</span>
        </div>
      </aside>
      <div className="shell-main">
        <header className="topbar">
          <div>
            <span className="eyebrow">Environment</span>
            <EnvironmentBadge environment={environment} />
          </div>
          <div className="topbar-health" aria-label="System health summary">
            <span className="health-dot" aria-hidden="true" />
            Portal boundary active
          </div>
        </header>
        <main className="page-content">{children}</main>
      </div>
    </div>
  );
}
