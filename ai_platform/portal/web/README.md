# AI Trading Portal Web

P6 introduces the first isolated Next.js/React portal surface for dry-run operations.

## Runtime modes

`PORTAL_WEB_DATA_MODE=api` is the default. In API mode the server requires:

- `PORTAL_CONTROL_PLANE_URL` — private server-side portal/control-plane origin;
- `PORTAL_ENVIRONMENT` — one of `research`, `test`, `staging`, `production`.

The browser never receives or calls `PORTAL_CONTROL_PLANE_URL`; browser mutations use same-origin BFF routes.

`PORTAL_WEB_DATA_MODE=fixture` is an explicit development/E2E mode with deterministic test-only data. It is never selected implicitly.

## Commands

```bash
npm ci
npm run typecheck
npm run lint
PORTAL_WEB_DATA_MODE=fixture PORTAL_ENVIRONMENT=test npm run build
npx playwright install chromium
npm run test:e2e
```

All P6 bot creation is constrained to `dry_run`. Freqtrade REST/WebSocket endpoints and exchange-direct calls are outside the browser boundary.
