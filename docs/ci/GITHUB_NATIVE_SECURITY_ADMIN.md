# GitHub-native security administration

## Purpose

Repository files enforce contribution policy, vulnerability-reporting guidance, workflow governance, title validation, branch hygiene and explicit CodeQL scanning. Some controls remain GitHub-native administrator settings and cannot be changed by repository content or the connected GitHub mutation surface.

## Verified state on 2026-08-06

- The repository description identifies Quant Platform.
- Private vulnerability reporting is enabled.
- The repository owner confirmed through the GitHub Advanced Security UI that Dependabot alerts, Dependabot security updates, Secret Protection and push protection are enabled.
- Explicit CodeQL analysis for Python and JavaScript/TypeScript is repository-managed by `.github/workflows/codeql.yml`; default setup must not be enabled simultaneously unless the duplicate-analysis impact is deliberately accepted.
- The repository is intentionally maintained by one person.

## Required owner actions

Open **Settings → Security → Advanced Security** for `blakinio/freqtrade` and keep the following enabled when offered by the repository plan:

1. Dependabot alerts;
2. Dependabot security updates;
3. private vulnerability reporting;
4. Secret Protection or secret scanning;
5. push protection.

Leave CodeQL default setup disabled while the explicit repository workflow is active, or remove the explicit workflow before switching to default setup.

Open the repository **About** settings and keep a description and topics that identify Quant Platform and its trading, AI, quantitative-finance and risk-management scope.

Do not invent a homepage destination. Leave the field empty until a canonical Quant Platform documentation or portal URL is approved.

## Review model

### Solo-maintainer mode

When the repository has only one maintainer, do not require an approving review or Code Owner review. GitHub does not permit an author to approve their own pull request, so either requirement would make normal owner-authored pull requests impossible to merge without bypassing governance.

In solo-maintainer mode, retain the controls that can be enforced without an independent reviewer:

- pull-request delivery rather than routine direct changes to `develop`;
- required strict `CI Gate` on the current pull-request head where the repository ruleset supports it;
- CodeQL, workflow-security analysis and relevant component or E2E validation;
- resolved conversations before merge;
- squash-only merge and linear history;
- blocked force pushes and protected-branch deletion;
- no administrative bypass merely to merge a failing pull request.

The repository owner accepted solo-maintainer mode for `blakinio/freqtrade` on 2026-08-06. Adding a second maintainer is not a completion requirement for Issue #1272.

### Multi-maintainer mode

If a real second trusted maintainer is added later and accepts review access, the repository owner may strengthen the `develop` ruleset to require:

- one approving review;
- dismissal of stale approvals;
- approval of the most recent reviewable push;
- Code Owner review.

Do not create a placeholder collaborator or service account solely to satisfy a review checkbox.

## Verification

After a native setting change, re-read the setting from GitHub where the integration permits it. When the API denies access, retain exact owner-provided UI evidence and record that limitation rather than claiming API verification.
