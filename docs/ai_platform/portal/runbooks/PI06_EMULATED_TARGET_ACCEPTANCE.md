# PI-06 Emulated Target Acceptance and Manual TOTP

## 1. Scope

This package starts a separately governed PI-06 acceptance route after repository-side implementation closure.

It automates everything that can be proven safely without owner infrastructure:

- real Authentik and PostgreSQL containers on a temporary Linux runner;
- health, restart persistence, loopback-only ingress and private database networking;
- absence of privileged mode, host networking, Docker socket access and steady-state bootstrap material;
- portal browser policy for anonymous, expired, revoked, MFA-missing, stale-step-up and cross-tenant sessions.

This evidence is non-production emulation. It does not prove real target acceptance.

## 2. Automated emulation

The pull-request workflow `Portal PI-06 Emulated Target Acceptance` creates isolated Docker networks and volumes with a unique prefix, uses a dedicated high loopback port and removes all resources after the run.

The uploaded JSON report contains only bounded status metadata. It contains no passwords, tokens, QR codes, TOTP seed, recovery code, cookie or client secret.

Passing automation proves:

1. the pinned Compose package starts and remains healthy;
2. the database is not published;
3. Authentik is reachable only through the declared loopback listener;
4. storage survives an application restart;
5. the portal denies mutation when MFA or fresh step-up evidence is missing.

Passing automation does not prove:

- login against the owner's Authentik;
- Google Authenticator enrollment or challenge;
- portal OIDC callback on the owner's DNS/TLS route;
- recovery, backup or restore on Synology;
- Cloudflare P11 acceptance;
- live-capital authority.

## 3. Safe Synology start

Use the existing `PI06_AUTHENTIK_SYNOLOGY.md` runbook and keep the service on `127.0.0.1:9000`.

Do not run `emulated_acceptance.sh` against the real Synology project. The emulation script intentionally creates and deletes temporary volumes.

For first access without exposing Authentik on the LAN, use SSH port forwarding from the workstation:

```bash
ssh -L 19000:127.0.0.1:9000 <synology-user>@<synology-host>
```

Open `http://127.0.0.1:19000` in the workstation browser while the SSH session remains active.

## 4. Manual Google Authenticator test

After the restricted administrator bootstrap:

1. sign in through the forwarded Authentik address;
2. open the current user's security or authenticator settings;
3. choose a TOTP authenticator;
4. scan the displayed QR code with Google Authenticator;
5. enter one current six-digit code to finish enrollment;
6. sign out completely;
7. sign in again and complete the TOTP challenge;
8. verify that a wrong code is rejected;
9. verify that the portal still denies mutation before MFA and allows only the capability already granted after MFA.

Do not capture the QR code, TOTP seed, current six-digit code or recovery codes in screenshots, logs, chat, GitHub artifacts or repository files.

Record only:

- UTC enrollment time;
- UTC successful fresh-login challenge time;
- a non-sensitive test-user alias;
- pass/fail for wrong-code rejection;
- pass/fail for post-MFA portal session;
- the exact commit and Authentik image digest.

## 5. Evidence boundary

Manual TOTP evidence may be described as owner-attested only after the owner performs the steps. Until then the durable status remains:

```text
emulated runtime acceptance: automated
real TOTP enrollment/challenge: pending owner action
real Synology target acceptance: not proven
```

Real PI-06 target acceptance additionally requires the exact OIDC callback, logout-all, back-channel and membership revocation, generic recovery behavior, encrypted backup creation and isolated restore.

## 6. Current-code revalidation

The 2026-08-02 revalidation reruns the isolated real-container Authentik checks and Chromium MFA fail-closed policy E2E on current `develop` after the public Portal SQLite login-lock repair. It changes no runtime configuration and does not claim that an owner password or a current TOTP code was exercised automatically.
