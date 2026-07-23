# Staging Incident and Kill-Switch Runbook

## Incident triggers

Treat any of the following as a staging security incident or release blocker:

- the portal origin is directly reachable from the public Internet when it should be private;
- a Freqtrade runtime or API becomes directly publicly reachable;
- an anonymous request reaches a privileged surface without Cloudflare Access enforcement;
- the dedicated staging Access service token is suspected to be compromised;
- the external staging E2E reports an unexpected ingress or authorization result.

## Immediate response

1. Activate the portal risk/kill-switch boundary when there is any possibility of unintended new exposure.
2. Keep all P11 execution simulated. Do not enable live capital as part of incident handling.
3. Revoke a suspected compromised staging Access service token.
4. Tighten or disable the affected Access application, hostname or route through the authorized external administration path.
5. Block direct origin reachability at the origin firewall/network boundary.
6. Remove any accidental public route to Freqtrade.
7. Preserve the first failure marker, correlation information and relevant bounded CI evidence.
8. Do not introduce a temporary security bypass to restore a green test.

## Recovery gates

Recovery requires all applicable conditions:

- the external Cloudflare/Tunnel/Access configuration is corrected by an authorized owner;
- compromised credentials are rotated;
- static staging policy validation passes;
- `Portal Staging External E2E` passes all public-ingress, Access and direct-denial probes;
- the incident evidence confirms there is still no live-capital authorization.

## Kill-switch release

Release the portal risk/kill switch only after the underlying security failure is corrected and evidence is reviewed. A green unit test alone is not sufficient to release an incident response control.

P11 does not authorize production trading or change the separate production execution-adapter boundary.
