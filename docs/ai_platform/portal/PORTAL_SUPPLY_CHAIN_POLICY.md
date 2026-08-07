# Portal supply-chain policy

## Scope

This policy applies to the final Docker images produced by:

- `deploy/synology/portal/Dockerfile`;
- `deploy/synology/portal-oidc/Dockerfile.control-plane`.

The repository gate builds both images once from the exact source SHA, records their immutable Docker image IDs, evaluates those exact IDs, and uses the same IDs for smoke or protected deployment. A tag is only a build-time convenience and is never deployment approval.

## Tool and database policy

- Syft is checksum-pinned to `1.50.0`.
- Grype is checksum-pinned to `0.116.1`.
- GitHub artifact attestations use `actions/attest` pinned to commit `1e69f48acb82d1966a394da916b4c1698aa569d6`.
- Grype refreshes its vulnerability database during each gate. Failure to download or load the database fails closed.
- The raw Grype report is retained with the gate evidence so the database descriptor and matching inputs remain reviewable.
- Docker builds use `--pull=false`; every `FROM` line must contain an immutable `sha256` digest.

Scanner versions are intentionally stable while vulnerability data remains current. Updating a scanner, its checksum, the policy schema, or an image base digest is a reviewable repository change.

## Vulnerability rule

The gate rejects a `high` or `critical` match when a fixed version is available. Unfixed matches remain visible in the report and must be handled through base or dependency update work when a fix becomes available.

A suppression is valid only when all of these fields exist:

```json
{
  "id": "stable-record-id",
  "vulnerability_id": "anchored regular expression",
  "package": "anchored regular expression",
  "owner": "accountable owner",
  "justification": "risk and remediation explanation",
  "expires_at": "YYYY-MM-DD"
}
```

Expired or incomplete suppressions invalidate the complete policy before scanning. Suppressions are matched against both vulnerability ID and package name.

## License rule

The machine-readable policy contains explicit allowed and denied patterns.

- Denied licenses fail the gate unless a package-specific, owned, justified and expiry-bounded exception matches.
- Unclassified license strings are reported for review. They do not silently become allowed; the policy records the deliberate `warn` action so a new denial or exception can be added without changing tool code.
- `UNKNOWN` and `NOASSERTION` remain visible because final-image operating-system metadata is not uniformly SPDX-normalized.

A license exception uses:

```json
{
  "id": "stable-record-id",
  "package": "anchored regular expression",
  "license_pattern": "regular expression",
  "owner": "accountable owner",
  "justification": "distribution and remediation explanation",
  "expires_at": "YYYY-MM-DD"
}
```

## Evidence and provenance

Each image produces:

- CycloneDX JSON SBOM;
- raw Grype JSON;
- vulnerability policy result;
- license policy result;
- SLSA v1-shaped provenance predicate;
- approval manifest with SHA-256 digests of every evidence file.

Provenance binds:

- exact source commit;
- final immutable image ID;
- Dockerfile digest;
- application manifest and lockfile digests;
- supply-chain policy digest;
- every digest-pinned base image;
- scanner versions and workflow invocation.

The evidence scanner fails closed on credential-shaped keys, private keys, access-key patterns, private IP addresses, Synology host paths and private Portal endpoint names. Evidence uses relative artifact paths; it does not record runner or protected-host filesystem locations.

## Protected deployment

The protected Portal workflow independently builds and evaluates the exact images before touching the deployment. It then invokes `tools/agents/portal_supply_chain.py deploy-approved`, which:

1. verifies the approval schema, source SHA, evidence checksums and live local image IDs;
2. verifies the source revision label on both approved image IDs;
3. replaces the legacy build callback with the two immutable approved IDs;
4. deploys those IDs without another image build;
5. proves in the final report that deployed IDs equal approved IDs and `rebuilt_during_deploy` is `false`.

The supply-chain gate grants no production, credential, restoration, trading or live-capital authority.

## Local validation

Policy logic:

```bash
python3 -m py_compile tools/agents/portal_supply_chain.py
python3 -m pytest -q tests/ci/test_portal_supply_chain.py
```

Full exact-image gate:

```bash
python3 tools/agents/portal_supply_chain.py build-verify \
  --repository . \
  --source-sha "$(git rev-parse HEAD)" \
  --output-dir /tmp/portal-supply-chain \
  --approval /tmp/portal-supply-chain/approval.json
```

The full command requires Docker plus the checksum-pinned Syft and Grype binaries.


## Durable rollback evidence

Protected deployment archives each approved manifest, policy, deployment request, SBOM, vulnerability report, license report, provenance statement, scanner database binding and deployment report under the protected Portal state directory. Atomic `current.json` and `previous.json` pointers bind the deployed and rollback image IDs to their matching evidence. Stable local `approved-current` and `approved-previous` tags prevent Docker garbage collection from silently removing either rollback image. Evidence paths are restricted to regular files in the approval directory and cannot traverse or follow symlinks outside that boundary.
