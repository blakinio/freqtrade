export type ProductSurfaceAvailability = "shell" | "backend-gap" | "fixture-preview";

export interface ProductSurfaceSection {
  title: string;
  description: string;
  items: string[];
}

export interface ProductSurfaceTable {
  columns: string[];
  rows: string[][];
}

export interface ProductSurfaceConfig {
  path: string;
  eyebrow: string;
  title: string;
  description: string;
  phase: string;
  availability: ProductSurfaceAvailability;
  sections: ProductSurfaceSection[];
  fixtureTable?: ProductSurfaceTable;
}

const surfaces: ProductSurfaceConfig[] = [
  {
    path: "/performance",
    eyebrow: "Overview",
    title: "PNL & Performance",
    description: "Portfolio and bot-level performance with explicit version and reconciliation boundaries.",
    phase: "UI information architecture",
    availability: "backend-gap",
    sections: [
      {
        title: "Performance attribution",
        description: "The production view will separate realized and unrealized PNL and preserve model, strategy and configuration periods.",
        items: ["Realized vs unrealized PNL", "Fees and slippage", "Drawdown", "Win/loss statistics"],
      },
      {
        title: "Version-aware comparisons",
        description: "Historical periods must not silently combine incompatible strategy or model revisions.",
        items: ["Strategy version", "Model version", "Config revision", "Validation vs observed behavior"],
      },
    ],
    fixtureTable: {
      columns: ["Bot", "Period", "Realized PNL", "Drawdown", "Version"],
      rows: [["BTC AI Dry Run", "Fixture window", "+12.40 USDT", "1.2%", "model-validated-2026-07"]],
    },
  },
  {
    path: "/positions",
    eyebrow: "Overview",
    title: "Open Positions",
    description: "Tenant-scoped position monitoring with freshness, risk and immutable runtime attribution.",
    phase: "UI information architecture",
    availability: "backend-gap",
    sections: [
      {
        title: "Position state",
        description: "The final read model requires normalized position data from private execution runtimes.",
        items: ["Pair and side", "Entry/current price", "Exposure", "Unrealized PNL"],
      },
      {
        title: "Safety context",
        description: "Any future manual exit remains permission-gated and audited through the risk/execution boundary.",
        items: ["Risk warnings", "Data freshness", "Bot/runtime identity", "Strategy/model version"],
      },
    ],
    fixtureTable: {
      columns: ["Pair", "Side", "Exposure", "Unrealized PNL", "Risk"],
      rows: [["BTC/USDT", "LONG", "250 USDT", "+3.10 USDT", "Normal"]],
    },
  },
  {
    path: "/orders",
    eyebrow: "Trading",
    title: "Orders",
    description: "Order lifecycle visibility without exposing direct browser-to-exchange or browser-to-Freqtrade control paths.",
    phase: "Execution read-model follow-up",
    availability: "backend-gap",
    sections: [
      {
        title: "Order lifecycle",
        description: "Canonical order reads are intentionally deferred until the private execution transport exposes attributable order evidence.",
        items: ["Submitted", "Open", "Filled", "Cancelled / rejected"],
      },
    ],
    fixtureTable: {
      columns: ["Order", "Pair", "Side", "State", "Source"],
      rows: [["fixture-order-1", "BTC/USDT", "BUY", "SIMULATED_FILLED", "Deterministic simulator"]],
    },
  },
  {
    path: "/trades",
    eyebrow: "Trading",
    title: "Trade History",
    description: "Normalized trade history designed to link execution evidence with post-trade intelligence.",
    phase: "Execution read-model follow-up",
    availability: "backend-gap",
    sections: [
      {
        title: "Attributable history",
        description: "Trades will retain bot, runtime, strategy, model and risk-policy identity rather than presenting anonymous exchange rows.",
        items: ["Trade identity", "Bot/runtime", "Realized PNL", "Analysis link"],
      },
    ],
    fixtureTable: {
      columns: ["Trade", "Pair", "Bot", "Realized PNL", "Analysis"],
      rows: [["trade-fixture-1", "BTC/USDT", "BTC AI Dry Run", "+12.40 USDT", "Available"]],
    },
  },
  {
    path: "/bots/signals",
    eyebrow: "Bots",
    title: "Signal Wizard",
    description: "Safe configuration surface for signed external signals and deterministic dry-run testing.",
    phase: "Product UI completion",
    availability: "shell",
    sections: [
      {
        title: "Integration contract",
        description: "Signal endpoints must use explicit schemas, authentication and replay/idempotency protection.",
        items: ["Integration type", "Target bot", "Signal schema", "Signed authentication"],
      },
      {
        title: "Test before activation",
        description: "The wizard is intentionally presentation-only until the signal ingestion contract is implemented.",
        items: ["Example payload", "Replay behavior", "Simulator test", "No secret re-display"],
      },
    ],
  },
  {
    path: "/bots/strategies",
    eyebrow: "Bots",
    title: "Strategy Catalog",
    description: "Internal catalog of versioned strategy templates and their validation evidence.",
    phase: "Product UI completion",
    availability: "fixture-preview",
    sections: [
      {
        title: "AI directional bot",
        description: "Versioned AI strategy template with immutable model assignment and deterministic risk policy.",
        items: ["Supported markets: spot", "Model required", "Risk class: bounded", "Dry-run eligible"],
      },
      {
        title: "Manual-entry bot",
        description: "Manual intent enters through the same risk-gated terminal boundary and private execution adapter.",
        items: ["No browser execution path", "Audited intents", "Dry-run only in current lifecycle"],
      },
    ],
  },
  {
    path: "/bots/grid",
    eyebrow: "Bots",
    title: "Grid Bots",
    description: "Specialized configuration shell for future versioned grid strategies.",
    phase: "Product UI completion",
    availability: "shell",
    sections: [
      {
        title: "Grid configuration",
        description: "Any generated setup must normalize into an immutable BotConfigRevision before deployment.",
        items: ["Price range", "Grid count / spacing", "Investment size", "Take profit / stop loss"],
      },
    ],
  },
  {
    path: "/operations/execution-logs",
    eyebrow: "Operations",
    title: "Execution Logs",
    description: "Correlation-aware execution and order evidence without leaking runtime credentials or private addresses.",
    phase: "Observability UI",
    availability: "backend-gap",
    sections: [
      {
        title: "Correlation drill-down",
        description: "The UI contract is ready for centralized log queries once an attributable query API is exposed.",
        items: ["Correlation ID", "Bot/runtime", "Order lifecycle", "Redacted structured fields"],
      },
    ],
  },
  {
    path: "/operations/signal-logs",
    eyebrow: "Operations",
    title: "Signal Logs",
    description: "Signal ingestion and strategy decision visibility with tenant and correlation boundaries.",
    phase: "Observability UI",
    availability: "backend-gap",
    sections: [
      {
        title: "Signal evidence",
        description: "No synthetic API-mode records are rendered before a canonical signal query model exists.",
        items: ["Signal source", "Schema version", "Bot", "Decision correlation"],
      },
    ],
  },
  {
    path: "/operations/risk-events",
    eyebrow: "Operations",
    title: "Risk Events",
    description: "Deterministic approve/reject evidence and kill-switch decisions.",
    phase: "Risk observability UI",
    availability: "backend-gap",
    sections: [
      {
        title: "Risk decision evidence",
        description: "Terminal decisions are already risk-gated; durable cross-event querying remains a separate read-model integration.",
        items: ["Reason codes", "Policy version", "Intent correlation", "Kill-switch state"],
      },
    ],
  },
  {
    path: "/operations/audit",
    eyebrow: "Operations",
    title: "Audit Events",
    description: "Permission-gated audit surface for privileged actions across portal modules.",
    phase: "Audit UI",
    availability: "backend-gap",
    sections: [
      {
        title: "Privileged evidence",
        description: "The surface never substitutes client-side visibility for server-side authorization.",
        items: ["Actor", "Action", "Resource", "Result and correlation"],
      },
    ],
  },
  {
    path: "/platform/notifications",
    eyebrow: "Platform",
    title: "Notifications",
    description: "Notification channel and rule shell for security, trading, risk, AI and system events.",
    phase: "P6 core operations shell",
    availability: "shell",
    sections: [
      {
        title: "Channels",
        description: "Channel configuration remains inactive until the notification service contract is implemented.",
        items: ["In-app", "Email", "External channel", "Webhook"],
      },
      {
        title: "Rule families",
        description: "Critical security or capital alerts may become mandatory regardless of user preferences.",
        items: ["Security", "Execution", "Risk", "AI/model health", "System degradation"],
      },
    ],
  },
  {
    path: "/platform/profile",
    eyebrow: "Platform",
    title: "Profile & Security",
    description: "Account-security shell separated from exchange credential management.",
    phase: "P6 core operations shell",
    availability: "shell",
    sections: [
      {
        title: "Account",
        description: "Identity issuance is owned by the authentication boundary; this UI does not invent an auth bypass.",
        items: ["Profile", "Security", "MFA", "Sessions"],
      },
      {
        title: "Integrations",
        description: "Exchange secrets remain under Exchange Connections and are never rendered after storage.",
        items: ["Notification channels", "Notification rules", "Integration credentials"],
      },
    ],
  },
  {
    path: "/platform/admin",
    eyebrow: "Platform",
    title: "Administration",
    description: "Permission-gated administration shell for platform policy and operational status.",
    phase: "P6 core operations shell",
    availability: "shell",
    sections: [
      {
        title: "Administrative domains",
        description: "All actions remain server-authorized; this route provides no privilege escalation path.",
        items: ["Users / organizations", "Roles / capabilities", "Risk policy", "Model promotion policy"],
      },
      {
        title: "Quality and operations",
        description: "Operational evidence surfaces remain read-only until their canonical APIs are available.",
        items: ["Exchange/runtime health", "Audit", "Autonomous-agent runs", "E2E quality status"],
      },
    ],
  },
];

export function findProductSurface(path: string): ProductSurfaceConfig | undefined {
  return surfaces.find((surface) => surface.path === path);
}
