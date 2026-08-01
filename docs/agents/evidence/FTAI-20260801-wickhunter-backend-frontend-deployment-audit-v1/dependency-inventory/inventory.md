# Dependency and supply-chain inventory

| Component | Repository declaration | Audit result |
|---|---|---|
| Python CI | setup-uv, Python `3.13` | Major/minor pinned, patch floats. |
| Collector runtime v1/v2 | `python:3.13-slim-bookworm` | Tag-only, no digest. |
| Node CI | setup-node `22` | Major pinned, patch floats. |
| Portal runtime | `node:22.23.1-bookworm-slim@sha256:6c7479...` | Version and digest pinned. |
| Next.js | `16.2.11` | Exact direct dependency; lockfile used by `npm ci`. |
| React / React DOM | `19.2.7` | Exact direct dependencies. |
| Playwright | `1.61.0` | Exact direct dev dependency. |
| TypeScript | `^6.0.0` | Range in manifest; lockfile resolves exact version. |
| GitHub Actions | checkout/setup-uv/setup-node/upload-artifact | Full commit SHA pins in dedicated workflow. |

Finding: `WH-ME-AUD-009`.
