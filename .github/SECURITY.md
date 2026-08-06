# Security Policy

## Supported code

This fork receives security fixes on the current default branch, `develop`.
Historical task, checkpoint, diagnostic and experiment branches are not
supported security-release lines.

Vulnerabilities that affect unchanged upstream Freqtrade code should also be
reported to the upstream Freqtrade project. Vulnerabilities introduced by this
fork, the Quant Platform, deployment automation, the AI Trading Portal or
WickHunter should be reported here.

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, tokens,
private endpoints, exchange identifiers, customer data or production logs.

Preferred reporting path:

1. Use **Security → Report a vulnerability** in this repository when private
   vulnerability reporting is enabled.
2. If that control is unavailable, open a minimal public issue titled
   `[Security] Private contact requested`. Include no technical details. The
   maintainer will establish a private channel before evidence is exchanged.

Include only information required to reproduce and assess the issue:

- affected commit, component and deployment mode;
- impact and prerequisites;
- minimal reproduction;
- whether credentials, orders, trading, withdrawals or live capital could be
  affected;
- proposed mitigation, when known.

Never include real exchange API keys, wallet credentials, access tokens,
private certificates or unredacted production data.

## Response and disclosure

The maintainer will acknowledge a valid private report, assess severity,
prepare a fix on an isolated branch and coordinate disclosure after affected
users have a reasonable remediation path.

Repository merge authority does not authorize production deployment, exchange
credential changes, model promotion, live trading, capital allocation or
withdrawals. Those operations require separate explicit authorization.
