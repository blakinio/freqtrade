# Staging Secret Rotation Runbook

## Scope

This runbook covers credentials used only by production-like portal staging automation, especially the dedicated Cloudflare Access service token consumed by `Portal Staging External E2E`.

It does not authorize production exchange credentials or live-capital access.

## Rotation procedure

1. Create or rotate a staging-only Cloudflare Access service token through an authorized external administration path.
2. Update the protected GitHub `staging` environment secrets:
   - `PORTAL_STAGING_CF_ACCESS_CLIENT_ID`
   - `PORTAL_STAGING_CF_ACCESS_CLIENT_SECRET`
3. Confirm the service identity remains scoped only to the intended staging Access application and policy.
4. Revoke the superseded token after the new token is stored.
5. Run `Portal Staging External E2E` and require all protected-ingress probes to pass.
6. Record the rotation event and validation run reference in the authorized operational evidence system.

## Safety rules

- Never commit service-token values.
- Never print token values into CI logs or diagnostic evidence.
- Never use a human interactive identity as the permanent machine E2E identity.
- Never reuse production exchange credentials for staging automation.
- Never add a test-only Access bypass to make staging E2E pass.
- Treat a failed post-rotation Access probe as a real staging failure until the external configuration is corrected.

## Emergency rotation

On suspected compromise:

1. revoke the affected staging service token immediately through the authorized external administration path;
2. keep execution simulated and activate the portal risk/kill switch if staging behavior is uncertain;
3. issue a new staging-only token;
4. update protected GitHub staging secrets;
5. rerun the external staging acceptance workflow before restoring automated privileged access.
