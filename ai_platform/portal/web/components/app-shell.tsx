import Link from "next/link";
import type { ReactNode } from "react";

import { portalEnvironment } from "@/lib/portal-api";
import { EnvironmentBadge } from "./environment-badge";

const navigationGroups = [
  {
    label: "Overview",
    items: [
      { href: "/", label: "Dashboard" },
      { href: "/performance", label: "PNL & Performance" },
      { href: "/positions", label: "Open Positions" },
    ],
  },
  {
    label: "Market Data",
    items: [{ href: "/market/liquidations", label: "Likwidacje" }],
  },
  {
    label: "Trading",
    items: [
      { href: "/terminal", label: "Trading Terminal" },
      { href: "/orders", label: "Orders" },
      { href: "/trades", label: "Trade History" },
    ],
  },
  {
    label: "Bots",
    items: [
      { href: "/bots", label: "View Bots" },
      { href: "/bots/new", label: "Create Bot" },
      { href: "/bots/signals", label: "Signal Wizard" },
      { href: "/bots/strategies", label: "Strategy Catalog" },
      { href: "/bots/grid", label: "Grid Bots" },
    ],
  },
  {
    label: "AI Intelligence",
    items: [
      { href: "/ai", label: "AI Overview" },
      { href: "/ai/trade-analysis", label: "Trade Analysis" },
      { href: "/ai/insights", label: "Insights" },
      { href: "/ai/model-health", label: "Model Health" },
      { href: "/ai/experiments", label: "Experiments" },
      { href: "/ai/learning", label: "Learning History" },
    ],
  },
  {
    label: "Operations",
    items: [
      { href: "/operations/execution-logs", label: "Execution Logs" },
      { href: "/operations/signal-logs", label: "Signal Logs" },
      { href: "/operations/risk-events", label: "Risk Events" },
      { href: "/operations/runtime-health", label: "Runtime Health" },
      { href: "/operations/audit", label: "Audit Events" },
    ],
  },
  {
    label: "Platform",
    items: [
      { href: "/platform/exchanges", label: "Exchange Connections" },
      { href: "/platform/notifications", label: "Notifications" },
      { href: "/platform/profile", label: "Profile & Security" },
      { href: "/platform/admin", label: "Administration" },
    ],
  },
];

const shellStyle = { minWidth: 0, width: "100%" } as const;
const navigationStyle = { minWidth: 0, maxWidth: "100%" } as const;

export function AppShell({ children }: { children: ReactNode }) {
  const environment = portalEnvironment();
  return (
    <div className="app-shell" style={shellStyle}>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar" style={navigationStyle}>
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">
            FT
          </span>
          <div>
            <strong>AI Trading Portal</strong>
            <span>Operations console</span>
          </div>
        </div>
        <nav className="primary-nav" aria-label="Primary navigation" style={navigationStyle}>
          {navigationGroups.map((group) => (
            <div className="nav-group" key={group.label}>
              <span className="nav-group-title">{group.label}</span>
              <div className="nav-group-links">
                {group.items.map((item) => (
                  <Link key={item.href} href={item.href}>
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </nav>
        <div className="sidebar-note">
          <strong>Private execution boundary</strong>
          <span>Trading runtimes and exchange credentials are never browser-addressable.</span>
        </div>
      </aside>
      <div className="shell-main">
        <header className="topbar">
          <div className="topbar-context">
            <span className="eyebrow">Environment</span>
            <EnvironmentBadge environment={environment} />
          </div>
          <div className="topbar-health" aria-label="System health summary">
            <span className="health-dot" aria-hidden="true" />
            Protected portal boundary active
          </div>
        </header>
        <main className="page-content" id="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}
