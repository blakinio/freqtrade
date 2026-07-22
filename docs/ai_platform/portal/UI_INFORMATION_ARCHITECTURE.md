# AI Trading Portal — UI and Information Architecture

## 1. Product goal

Provide a modern trading operations portal with a consistent application shell and clear separation between:

- monitoring;
- execution;
- bot configuration;
- AI/model operations;
- analysis/learning;
- security/account administration.

The information architecture is informed by common modern trading-dashboard patterns and privately reviewed visual references, but the product must use its own branding, component system, assets and interaction design.

No private captured profile data or third-party proprietary binary assets belong in the product repository.

## 2. Global shell

```text
+----------------------+---------------------------------------------------------+
| Sidebar              | Topbar                                                  |
|                      | notifications | environment | exchange | user/account   |
|                      +---------------------------------------------------------+
|                      |                                                         |
|                      | Page content                                            |
|                      |                                                         |
+----------------------+---------------------------------------------------------+
```

Global shell responsibilities:

- current tenant/environment indicator;
- exchange connection selector where contextually useful;
- notification center;
- system health summary;
- user menu;
- emergency kill-switch visibility for authorized roles;
- clear dry-run/shadow/live environment badge.

A live-capital environment must never be visually indistinguishable from dry-run.

## 3. Primary navigation

```text
Overview
├── Dashboard
├── PNL & Performance
└── Open Positions

Trading
├── Trading Terminal
├── Orders
└── Trade History

Bots
├── Create Bot
├── View Bots
├── Signal Wizard
├── Strategy Catalog
└── Grid Bots

AI Intelligence
├── AI Overview
├── Trade Analysis
├── Insights
├── Model Health
├── Experiments
└── Learning History

Operations
├── Execution Logs
├── Signal Logs
├── Risk Events
├── Runtime Health
└── Audit Events (permission-gated)

Platform
├── Exchange Connections
├── Notifications
├── Usage / Subscription (future commercial mode)
├── Profile & Security
└── Administration (permission-gated)
```

The initial MVP can hide not-yet-implemented sections but should preserve route ownership and domain boundaries.

## 4. Dashboard

Purpose: answer "is the platform healthy and what needs attention?"

Recommended widgets:

```text
Portfolio / simulated equity
Daily PNL
Total PNL
Drawdown
Open positions
Active bots
Exchange health
AI model health
Risk status
Recent trades
Recent alerts
Open AI insights
```

Dashboard values must display freshness/reconciliation state when data is delayed.

## 5. PNL & Performance

Capabilities:

- portfolio and bot-level PNL;
- realized/unrealized separation;
- fees/slippage attribution;
- drawdown;
- win/loss statistics;
- performance by strategy/model version;
- performance by market regime;
- comparison of declared validation expectations vs dry-run/live observations.

Historical performance views must identify the model/strategy/config periods to avoid mixing incompatible versions silently.

## 6. Open Positions

Show:

- pair/market;
- side;
- entry/current price;
- exposure;
- unrealized PNL;
- bot/runtime;
- strategy/model version;
- stop/risk state;
- data freshness;
- risk warnings.

Manual exit actions are permission-gated and audited.

## 7. Trading Terminal

Layout target:

```text
+---------------------------+--------------------------------+
| Intent / Order panel      | Market chart / context         |
|                           |                                |
+---------------------------+--------------------------------+
| Positions / Orders / Events                                |
+------------------------------------------------------------+
```

Modes may include:

- manual trade intent;
- open/close position;
- signal submission/test;
- order simulation.

Every high-impact action shows:

- target environment;
- exchange;
- pair;
- estimated exposure;
- applicable risk policy;
- explicit confirmation when policy requires it.

The terminal submits intent to the portal risk/execution boundary; it never calls the exchange or Freqtrade directly from the browser.

## 8. Create Bot

Wizard:

```text
1. Select strategy/template
2. Select exchange connection
3. Select market/pair policy
4. Select model version where AI-enabled
5. Configure strategy parameters
6. Configure DCA/position behavior where supported
7. Configure exits/stop behavior
8. Select risk policy / capital allocation
9. Review immutable revision
10. Deploy in allowed lifecycle environment
```

Bot templates are configuration schemas mapped to versioned strategies, not arbitrary browser-edited Python code.

Example catalog families:

- AI directional bot;
- liquidation-inspired strategy research template where independently implemented;
- manual-entry bot;
- built-in signal bot;
- webhook/signal bot;
- grid bot;
- future RL policy bot after separate validation.

Names and behavior must describe our implementation, not imply compatibility with or copying of a third-party product.

## 9. View Bots

Table/card capabilities:

- status;
- desired vs observed state;
- exchange;
- strategy/model;
- pairs;
- open positions;
- PNL;
- risk state;
- runtime health;
- last decision/trade;
- start/pause/stop actions according to permission.

Filters:

- environment;
- status;
- exchange;
- strategy;
- model;
- market;
- risk state.

## 10. Signal Wizard

Purpose: safely configure external signal integrations.

Show:

- integration type;
- target bot/template;
- signal schema;
- endpoint identity;
- signed-auth requirements;
- example payload;
- replay/idempotency behavior;
- test signal capability against simulator/dry-run.

Secrets are never rendered after initial creation.

## 11. Strategy Catalog

Initial scope is an internal catalog, not necessarily a commercial marketplace.

Each strategy card:

```text
name
version
status
supported markets
model requirement
risk class
validation summary
OOS/walk-forward evidence links
dry-run status
Create Bot action
```

A commercial marketplace can be a later program without changing the core strategy-version contract.

## 12. Grid Bots

Grid strategies may use a specialized visual configuration surface because their setup is inherently price-range/grid oriented.

UI may include:

- chart;
- grid range;
- grid count/spacing;
- side/mode;
- investment size;
- quick setup;
- manual adjustments;
- take profit/stop loss/trailing behavior;
- strategy-specific volatility/ATR controls where independently implemented.

All generated configuration is normalized into an immutable BotConfigRevision before deployment.

## 13. AI Intelligence

This is a differentiating first-class product area.

### AI Overview

- active model versions;
- model lifecycle state;
- model age;
- drift status;
- inference health;
- live/dry-run divergence;
- open insights;
- candidate training status.

### Trade Analysis

Per trade:

- decision timeline;
- model prediction;
- strategy signal;
- risk decision;
- execution outcome;
- market regime;
- MFE/MAE;
- diagnosis;
- evidence references;
- counterfactual scenarios labeled hypothetical.

### Insights

Prioritized observations/hypotheses with:

- confidence;
- evidence count/window;
- affected bots/models;
- suggested next action;
- create experiment action;
- dismiss/acknowledge state.

### Model Health

- data/feature drift;
- prediction distribution;
- inference rejections;
- stale model warnings;
- training age;
- validation vs observed behavior.

### Experiments

- requested/running/completed experiments;
- exact versions;
- validation gates;
- negative results preserved;
- candidate lifecycle state;
- explicit promotion action only when authorized.

### Learning History

Chronological record of validated findings, superseded hypotheses and promotion decisions.

## 14. Logs and operations

Separate views:

- signal logs;
- execution/order logs;
- risk decisions;
- runtime lifecycle;
- exchange connectivity;
- model/inference events;
- post-trade analysis events;
- audit events for privileged users.

Logs support correlation-ID drill-down from UI action to execution and analysis.

## 15. Profile & Security

Tabs/surfaces:

```text
Profile
Security
MFA
Sessions
Notification Channels
Notification Rules
API / Integration Credentials (where allowed)
```

Exchange credentials are managed under Exchange Connections rather than mixed with ordinary profile fields.

## 16. Notifications

Channels may include:

- in-app;
- email;
- Telegram or similar external channel where independently integrated;
- webhook.

Rule families:

```text
security
execution
trading
risk
AI/model health
training/experiment
system degradation
```

Users choose subscriptions within role/policy limits. Critical security/capital alerts may be mandatory.

## 17. Administration

Permission-gated surfaces:

- users/organizations;
- roles/capabilities;
- environment controls;
- model promotion policy;
- risk-policy management;
- exchange/runtime health;
- audit;
- autonomous-agent runs;
- E2E quality status.

## 18. UX safety principles

1. Environment is always visible (`DRY RUN`, `SHADOW`, `LIVE SMALL`, `PRODUCTION`).
2. Destructive/high-capital actions are distinct from ordinary navigation.
3. Degraded/stale data is shown explicitly.
4. AI hypotheses are visually distinct from validated findings.
5. A losing trade is not automatically labeled an AI mistake.
6. Promotion is distinct from training.
7. Kill switches are discoverable to authorized users.
8. Empty/error/denied/loading states are designed, not accidental.
9. Responsive design is validated by E2E and visual acceptance.
10. Accessibility is part of component acceptance.
