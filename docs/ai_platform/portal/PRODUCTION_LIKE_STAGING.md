# Production-Like Cloudflare Staging

## Purpose

P11 defines the repository-side contract for a production-like staging deployment that traverses the same intended public security boundary as the future portal without exposing Freqtrade or enabling live capital.

The target request path is:

```text
Internet
  -> Cloudflare edge
  -> Cloudflare Access where the surface is privileged
  -> Cloudflare Tunnel
  -> private staging portal origin
```

The origin has no intended direct public application path. Freqtrade remains behind the private execution-adapter boundary and must not receive a public hostname or direct public route.

## Fail-closed staging contract

`ai_platform/portal/deploy/cloudflare/staging-policy.example.json` is a machine-readable staging policy. Its schema fixes the following invariants:

- staging requires Tunnel-based origin connectivity;
- direct public origin ingress is forbidden;
- direct public Freqtrade ingress is forbidden;
- execution remains simulated;
- the managed WAF baseline is required;
- privileged surfaces require Access coverage;
- sensitive endpoint families require rate-limit/WAF coverage;
- URLs, paths and Cloudflare Access service credentials are referenced only by environment-variable names, not committed values.

The policy validator fails closed when required Access surfaces or rate-limit families are omitted.

## External acceptance probe

`.github/workflows/portal-staging-external-e2e.yml` is a manual, read-only acceptance workflow bound to the protected GitHub `staging` environment. It does not provision or modify Cloudflare resources.

The probe proves five boundaries:

1. the public portal endpoint is reachable through the configured staging hostname;
2. anonymous access to the configured privileged path is denied or redirected to Cloudflare Access;
3. a dedicated staging Access service identity can reach that privileged path;
4. the direct origin probe path is unreachable or explicitly denied;
5. the direct Freqtrade probe path is unreachable or explicitly denied.

Probe output is intentionally bounded to status codes and network exception classes. It does not print endpoint URLs, Access client IDs or Access client secrets.

## Protected GitHub staging configuration

The external workflow expects these staging environment variables:

- `PORTAL_STAGING_BASE_URL`
- `PORTAL_STAGING_PRIVILEGED_PATH`

It expects these staging environment secrets:

- `PORTAL_STAGING_ORIGIN_PROBE_URL`
- `PORTAL_STAGING_FREQTRADE_PROBE_URL`
- `PORTAL_STAGING_CF_ACCESS_CLIENT_ID`
- `PORTAL_STAGING_CF_ACCESS_CLIENT_SECRET`

The direct origin and Freqtrade probe targets are stored as secrets because they may reveal otherwise private addressing information.

## External Cloudflare configuration boundary

Repository code does not create or mutate a real Cloudflare account. Before production-like staging acceptance can be claimed, an authorized owner must configure and review the external resources, including at minimum:

- a dedicated staging Tunnel and connector;
- staging DNS routed through Cloudflare;
- Access applications/policies for privileged surfaces;
- a dedicated staging service token for machine E2E;
- WAF and rate-limit rules for the required endpoint families;
- origin firewall/network rules that prevent direct public ingress;
- no public route to Freqtrade.

Infrastructure mutations that affect a real external account require explicit owner approval under the portal execution plan.

## Acceptance rule

Passing repository unit tests and policy validation is necessary but not sufficient for P11 completion. Production-like staging acceptance requires a successful `Portal Staging External E2E` run against owner-approved real staging resources.

There is no test-only security bypass. Exchange execution remains simulated throughout P11. Live-capital authorization is outside this work package.
