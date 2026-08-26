#!/usr/bin/env bash
set -Eeuo pipefail

observer_name="${1:-portal-wh09-runtime-observer}"
source_sha="${2:-}"
expected_old_revision="${3:-}"
wh09_runtime_gid="${4:-65531}"

[[ "$observer_name" == "portal-wh09-runtime-observer" ]]
[[ "$source_sha" =~ ^[0-9a-f]{40}$ ]]
[[ "$expected_old_revision" =~ ^[0-9a-f]{40}$ ]]
[[ "$wh09_runtime_gid" =~ ^[0-9]+$ ]]

old_image="$(docker inspect --format '{{.Image}}' "$observer_name")"
[[ "$old_image" =~ ^sha256:[0-9a-f]{64}$ ]]
old_revision="$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$old_image")"
[[ "$old_revision" == "$expected_old_revision" ]]

docker inspect "$observer_name" > "$RUNNER_TEMP/wh09-observer-v10-old.json"
readarray -t observer_binding < <(python3 - "$RUNNER_TEMP/wh09-observer-v10-old.json" <<'PY'
import json
import pathlib
import sys

observer = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))[0]
host = observer["HostConfig"]
config = observer["Config"]
if config.get("User") != "10001:10001":
    raise SystemExit("WH09 observer user mismatch")
if host.get("RestartPolicy", {}).get("Name") != "unless-stopped":
    raise SystemExit("WH09 observer restart policy mismatch")
if host.get("ReadonlyRootfs") is not True or host.get("Privileged") is not False:
    raise SystemExit("WH09 observer hardening mismatch")
if "ALL" not in (host.get("CapDrop") or []):
    raise SystemExit("WH09 observer does not drop all capabilities")
if not any("no-new-privileges" in value for value in (host.get("SecurityOpt") or [])):
    raise SystemExit("WH09 observer no-new-privileges is absent")
if observer.get("NetworkSettings", {}).get("Ports") not in ({}, None):
    raise SystemExit("WH09 observer unexpectedly publishes ports")
networks = observer.get("NetworkSettings", {}).get("Networks") or {}
if set(networks) != {"portal_oidc_public"}:
    raise SystemExit("WH09 observer network binding mismatch")
mounts = {entry.get("Destination"): entry for entry in observer.get("Mounts") or []}
for destination in ("/runtime/journal", "/runtime/operator"):
    mount = mounts.get(destination)
    if not isinstance(mount, dict) or mount.get("Type") != "bind" or mount.get("RW") is not False:
        raise SystemExit(f"WH09 observer read-only mount mismatch: {destination}")
    source = mount.get("Source")
    if not isinstance(source, str) or not source.startswith("/volume1/docker/"):
        raise SystemExit(f"WH09 observer mount source is unsafe: {destination}")
    print(source)
PY
)
[[ ${#observer_binding[@]} -eq 2 ]]
journal_host="${observer_binding[0]}"
operator_host="${observer_binding[1]}"

new_tag="local/freqtrade-wh09-observer-v10:${source_sha}"
docker build \
  --pull=false \
  --label "org.opencontainers.image.revision=${source_sha}" \
  --file deploy/synology/portal-oidc/Dockerfile.control-plane \
  --tag "$new_tag" \
  .
new_image="$(docker image inspect --format '{{.Id}}' "$new_tag")"
[[ "$new_image" =~ ^sha256:[0-9a-f]{64}$ ]]
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$new_image")" == "$source_sha" ]]

run_observer() {
  local image="$1"
  docker run --detach \
    --name "$observer_name" \
    --restart unless-stopped \
    --network portal_oidc_public \
    --network-alias portal-wh09-runtime-observer \
    --user 10001:10001 \
    --group-add "$wh09_runtime_gid" \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,nodev,size=32m \
    --cap-drop ALL \
    --security-opt no-new-privileges:true \
    --env PORTAL_WICKHUNTER_WH09_ROOT=/runtime \
    --mount "type=bind,src=${journal_host},dst=/runtime/journal,readonly" \
    --mount "type=bind,src=${operator_host},dst=/runtime/operator,readonly" \
    --health-cmd "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).read()\"" \
    --health-interval 10s \
    --health-timeout 5s \
    --health-retries 12 \
    --entrypoint python \
    "$image" \
    -m ai_platform.portal.control_plane.wh09_runtime_observer >/dev/null
}

wait_observer() {
  for _ in $(seq 1 60); do
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$observer_name" 2>/dev/null || true)"
    [[ "$health" == "healthy" ]] && return 0
    [[ "$health" =~ ^(unhealthy|exited|dead)$ ]] && break
    sleep 2
  done
  docker logs --tail 120 "$observer_name" >&2 || true
  return 1
}

rollback_needed=0
rollback() {
  local rc=$?
  if [[ "$rollback_needed" -eq 1 ]]; then
    echo "WH09 observer v10 failed; restoring exact previous observer image" >&2
    docker rm -f "$observer_name" >/dev/null 2>&1 || true
    run_observer "$old_image"
    wait_observer
    restored_image="$(docker inspect --format '{{.Image}}' "$observer_name")"
    [[ "$restored_image" == "$old_image" ]]
    [[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$restored_image")" == "$expected_old_revision" ]]
  fi
  exit "$rc"
}
trap rollback ERR

rollback_needed=1
docker rm -f "$observer_name" >/dev/null
run_observer "$new_image"
wait_observer

docker exec -i "$observer_name" python - <<'PY'
from pathlib import Path
from ai_platform.portal.control_plane.wh09_runtime_observer_reader import Wh09ObserverRuntimeEvidenceReader

evidence = Wh09ObserverRuntimeEvidenceReader(Path('/runtime')).read()
if evidence.health != 'HEALTHY':
    raise SystemExit(f'WH09 observer v10 evidence health={evidence.health}')
if evidence.decision_count <= 0 or evidence.no_trade_count <= 0:
    raise SystemExit('WH09 observer v10 has no decision truth')
if (
    evidence.trading_credentials_present is not False
    or evidence.order_adapter_present is not False
    or evidence.execution_enabled is not False
    or evidence.orders_submitted != 0
    or evidence.live_capital_authorized is not False
):
    raise SystemExit('WH09 observer v10 changed zero-authority invariants')
print('WH09_OBSERVER_V10_DIRECT_EVIDENCE_PASS')
PY

docker exec -i "$observer_name" python - <<'PY'
import json
import urllib.request

with urllib.request.urlopen('http://127.0.0.1:8080/evidence', timeout=30) as response:
    payload = json.load(response)
if response.status != 200:
    raise SystemExit(f'WH09 observer v10 HTTP status={response.status}')
if payload.get('live_capital_authorized') is not False or payload.get('execution_enabled') is not False:
    raise SystemExit('WH09 observer v10 HTTP evidence changed zero-authority invariants')
print('WH09_OBSERVER_V10_HTTP_EVIDENCE_PASS')
PY

[[ -z "$(docker port "$observer_name")" ]]
[[ "$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' "$observer_name")" == "true" ]]
[[ "$(docker inspect --format '{{.HostConfig.Privileged}}' "$observer_name")" == "false" ]]
[[ "$(docker inspect --format '{{.HostConfig.RestartPolicy.Name}}' "$observer_name")" == "unless-stopped" ]]
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$(docker inspect --format '{{.Image}}' "$observer_name")")" == "$source_sha" ]]

rollback_needed=0
trap - ERR
echo "WH09_OBSERVER_V10_UPGRADE_PASS revision=${source_sha}"
