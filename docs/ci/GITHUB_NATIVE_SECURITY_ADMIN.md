# GitHub-native security administration

## Purpose

Repository files enforce contribution policy, vulnerability-reporting guidance, workflow governance, title validation, branch hygiene and explicit CodeQL scanning. The remaining controls in Issue #1272 are GitHub-native administrator settings and cannot be changed by repository content or the connected GitHub mutation surface.

## Verified state on 2026-08-06

- The repository description is still `Free, open source crypto trading bot` and the homepage still points to the upstream Freqtrade documentation.
- Repository topics are empty.
- Private vulnerability reporting is disabled.
- Exactly one direct collaborator exists: `blakinio`, with administrator permission.
- The connected integration receives `403 Resource not accessible by integration` for Dependabot-alert and CodeQL-default-setup inspection.
- Explicit CodeQL analysis for Python and JavaScript/TypeScript is repository-managed by `.github/workflows/codeql.yml`; default setup must not be enabled simultaneously unless the duplicate-analysis impact is deliberately accepted.

## Required owner actions

Open **Settings → Security → Code security and analysis** for `blakinio/freqtrade` and:

1. enable Dependabot alerts;
2. enable Dependabot security updates;
3. enable private vulnerability reporting;
4. enable secret scanning and push protection when offered by the repository plan;
5. leave CodeQL default setup disabled while the explicit repository workflow is active, or remove the explicit workflow before switching to default setup.

Open the repository **About** settings and set:

- description: `Quant Platform — AI-assisted strategy research, validation, execution control and observability built on Freqtrade.`
- topics: `algorithmic-trading`, `ai-trading`, `crypto-trading`, `freqtrade`, `machine-learning`, `quantitative-finance`, `risk-management`, `trading-platform`.

Do not change the homepage until a canonical Quant Platform documentation or portal URL is approved. Retaining the upstream documentation URL is safer than inventing a destination.

## Independent review gate

A second trusted maintainer must be a real named person or service account selected by the repository owner. Do not create a placeholder collaborator and do not enable required approval or required Code Owner review while only one independent reviewer exists.

After the second maintainer has accepted review access, update the protected `develop` ruleset to require:

- one approving review;
- dismissal of stale approvals;
- approval of the most recent reviewable push;
- Code Owner review;
- resolved conversations;
- strict required `CI Gate` on an up-to-date branch;
- blocked force pushes and branch deletion.

## Verification

After each native setting change, re-read the setting from GitHub and update Issue #1272 with exact evidence. The task remains waiting until every applicable checkbox is verified rather than merely clicked.
