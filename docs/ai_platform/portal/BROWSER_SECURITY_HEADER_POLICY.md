# AI Trading Portal — Browser Security Header Policy

## Purpose

This document assigns one explicit owner to each browser-security boundary and records the exact
repository policy. It does not claim that protected Cloudflare, Synology or public-origin behavior
has been accepted.

## Ownership

| Boundary | Authority | Status |
|---|---|---|
| Per-request CSP nonce and enforced CSP | Next.js Proxy (`proxy.ts`) | Repository-enforced by #1303 |
| Invariant framing, MIME, referrer, permissions and cross-origin headers | Next.js application (`next.config.ts` plus Proxy) | Repository-enforced by #1303 |
| Authenticated downstream cache directives | Portal response-cache helper through Next.js Proxy and final response configuration | Repository-enforced by #1304 |
| HSTS and public HTTPS edge behavior | Approved public edge (Cloudflare/Synology boundary) | `EXTERNAL_ACCEPTANCE_REQUIRED` in #1305 |
| Direct-origin bypass denial | Protected deployment/edge acceptance | `EXTERNAL_ACCEPTANCE_REQUIRED` in #1305 |

The application deliberately does not emit HSTS. HSTS is meaningful only on the approved HTTPS
public origin and requires an owner-reviewed `max-age`, subdomain and preload decision. Local,
fixture and repository tests cannot satisfy that evidence.

## Enforced Content Security Policy

A fresh cryptographically unpredictable nonce is generated for every request handled by the
Next.js Proxy. The exact CSP and `x-nonce` are forwarded to Next.js rendering; the same CSP is
returned to the browser. Next.js applies that nonce to framework and page scripts.

Production directives:

```text
default-src 'self'
script-src 'self' 'nonce-<per-request>' 'strict-dynamic'
style-src 'self' 'nonce-<per-request>'
img-src 'self' data: blob:
font-src 'self' data:
connect-src 'self'
worker-src 'self' blob:
manifest-src 'self'
media-src 'none'
object-src 'none'
base-uri 'self'
form-action 'self'
frame-src 'none'
frame-ancestors 'none'
upgrade-insecure-requests
```

The production policy contains no wildcard source, no `unsafe-eval`, no private control-plane,
Vault, Freqtrade or exchange origin, and no CSP reporting endpoint that could collect secret-bearing
URLs.

## Development differences

Next.js development tooling requires narrowly scoped local exceptions:

- `script-src` adds `unsafe-eval` only when `NODE_ENV=development`;
- `style-src` adds `unsafe-inline` only when `NODE_ENV=development` for hot-reload style injection;
- `connect-src` adds only localhost/127.0.0.1 HTTP and WebSocket development endpoints;
- `upgrade-insecure-requests` is omitted in development.

These exceptions are generated from the runtime environment and cannot appear in a production
policy. Test coverage evaluates the production builder independently from the development server.

## Invariant headers

The application applies the following values to document, redirect and API/error responses through
the Proxy and to static Next.js resources through `next.config.ts`:

```text
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
Permissions-Policy: camera=(), geolocation=(), microphone=(), payment=(), usb=()
Referrer-Policy: strict-origin-when-cross-origin
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

`frame-ancestors 'none'` is the primary framing control; `X-Frame-Options: DENY` is retained as a
compatible defense for older clients.

## OIDC and application compatibility

- OIDC login uses full-page navigation; it does not require an external script, frame or browser
  connection source.
- The callback and BFF remain same-origin.
- Private services remain server-only and are never added to `connect-src`.
- Local Next assets, data/blob images, local fonts, workers and approved same-origin downloads remain
  allowed.
- COOP/CORP are set to `same-origin`; any future cross-origin popup, embed or download requirement
  must receive a separate scoped security decision rather than weakening the policy globally.

## Cache boundary

The canonical application-owned downstream response policy is:

```text
Cache-Control: private, no-store
```

The single value authority is `lib/response-cache-policy.ts`. `proxy.ts` applies it together with the
CSP and invariant browser headers, while `next.config.ts` applies the same value to final dynamic
responses because Next.js rendering can replace headers placed only on `NextResponse.next()`.

Application-controlled documents, redirects and direct Proxy/API responses are required to preserve
the exact normalized `private, no-store` policy. Framework-generated terminal responses may append
additional strictly non-cacheable directives after the application header. Next.js production
not-found handling currently adds `no-cache`, `max-age=0` and `must-revalidate`; this is accepted only
when the final response still contains both `private` and `no-store` and contains no `public`,
`immutable`, `s-maxage` or positive `max-age` directive. Framework augmentation must never make a
response shared-cacheable.

The policy covers:

- authenticated and anonymous dynamic HTML documents;
- protected redirects and denied responses;
- same-origin BFF/API success, validation, unauthorized, forbidden, not-found, conflict and 5xx
  responses;
- login, callback, session, logout and fixture/test identity responses.

Applying the policy to anonymous login and error documents prevents identity transaction or failure
state from becoming shared-cacheable. Public immutable Next.js static/image assets are excluded from
the Proxy matcher and retain their framework-owned cache behavior.

An upstream `fetch(..., { cache: "no-store" })` controls only the server-side fetch cache and is not
accepted as browser/CDN response policy. A route or helper must not replace the downstream policy
with a public or shared-cache directive.

Browser-history verification proves that the real fixture logout route clears the session and a
subsequent back navigation revalidates the protected page and redirects to login. A separate tenant
change scenario proves that back navigation cannot restore the prior workspace and is redirected to
the cross-tenant denial boundary. Chromium BFCache restores are forced through a network reload so
the Proxy revalidates current session and tenant state before protected content is shown again.

## Verification

Repository verification includes:

- production-policy unit assertions inside the Playwright security suite;
- fresh nonce comparison across independent requests;
- rendered Next script nonce equality with the response CSP;
- document, protected redirect, API success/error and static asset header assertions;
- exact canonical cache-policy assertions for application-controlled responses;
- fail-closed compatibility assertions for framework-generated not-found responses: `private` and
  `no-store` must remain present and no shared-cache-enabling directive may appear;
- status-independent cache-policy assertions for representative 200, 401, 403, 404, 409 and 5xx
  response paths;
- direct-origin cache assertions for login documents, protected redirects, unauthorized/forbidden
  API responses, authenticated session success and authenticated not-found responses;
- explicit logout-response and browser back/forward verification after session clearing;
- tenant-change and browser back/forward verification against prior-workspace replay;
- proof that static Next assets are not assigned the authenticated `private, no-store` policy;
- lint, typecheck, production build, direct-origin Playwright security tests and required exact-head
  CI/security scanning.

Protected verification in #1305 must separately prove the real public origin, edge-owned HSTS and
direct-origin denial without recording credentials, cookies, tokens or tenant response bodies.

## Safety boundary

This policy grants no protected infrastructure mutation, credential access, deployment promotion,
strategy/model promotion, order submission, withdrawal or live-capital authority.
