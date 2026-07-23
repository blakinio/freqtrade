# AI Trading Portal Web

The portal web application is the browser-facing Next.js/React layer above the private portal control plane. It is not a public Freqtrade frontend.

## Delivery scope

Historical PR #135 delivered the P6.1 web-shell foundation. The current UI completion work expands that foundation to the target information architecture with:

- grouped full-product navigation;
- Dashboard, bot fleet, Bot Detail and structured dry-run Create Bot wizard;
- Trading Terminal;
- Runtime Health and opaque Exchange Connection metadata;
- AI Overview, Trade Analysis, Insights, Model Health, Experiments and Learning History;
- intentional shell/read-model-gap routes for product surfaces whose canonical backend query API is not yet available;
- wide-display and responsive layouts with explicit environment visibility.

`docs/ai_platform/portal/UI_DELIVERY_STATUS.md` is the authoritative per-surface delivery matrix.

## Runtime modes

`PORTAL_WEB_DATA_MODE=api` is the default. In API mode the server requires:

- `PORTAL_CONTROL_PLANE_URL` — private server-side portal/control-plane origin;
- `PORTAL_ENVIRONMENT` — one of `research`, `test`, `staging`, `production`.

The browser never receives or calls `PORTAL_CONTROL_PLANE_URL`; browser mutations use same-origin BFF routes or server-rendered reads.

API mode does not invent unavailable PNL, position, order, log or audit records. A route with no canonical backend read model renders an explicit unavailable state.

`PORTAL_WEB_DATA_MODE=fixture` is an explicit development/E2E mode with deterministic test-only data and previews. It is never selected implicitly and is not evidence of live execution or production data.

## Commands

```bash
npm ci
npm run typecheck
npm run lint
PORTAL_WEB_DATA_MODE=fixture PORTAL_ENVIRONMENT=test npm run build
npx playwright install chromium
npm run test:e2e
```

All portal bot creation remains constrained to `dry_run`. Freqtrade REST/WebSocket endpoints, exchange-direct calls, secret-store access and live-capital authorization are outside the browser boundary.
