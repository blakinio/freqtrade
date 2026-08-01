# Playwright evidence

No Playwright execution was possible in the primary audit session because a repository checkout and browser dependencies were unavailable.

Historical CI at PR #836 head included successful Portal Universal E2E and dedicated Market Evidence CI. Those runs are not evidence for the exact audited head.

Required independent-validation command:

```bash
cd ai_platform/portal/web
npm ci
npx playwright test e2e/specs/market-evidence.spec.ts e2e/specs/market-evidence-states.spec.ts --project=chromium-desktop
```
