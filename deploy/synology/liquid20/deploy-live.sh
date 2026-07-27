#!/usr/bin/env bash
set -Eeuo pipefail

image_name="${LIQUID20_IMAGE_NAME:-local/liquid20-collector}"
container_name="${LIQUID20_CONTAINER_NAME:-liquid20-live}"
data_root="${LIQUID20_DATA_ROOT:-/volume1/docker/freqtrade-liquidations/data}"
host_id="${LIQUID20_HOST_ID:-synology-pl-01}"
puid="${LIQUID20_PUID:?LIQUID20_PUID is required}"
pgid="${LIQUID20_PGID:?LIQUID20_PGID is required}"
commit_sha="${GITHUB_SHA:?GITHUB_SHA is required}"
image="${image_name}:sha-${commit_sha}"
candidate="${container_name}-candidate-${GITHUB_RUN_ID:-manual}-${GITHUB_RUN_ATTEMPT:-1}"
candidate_root="${RUNNER_TEMP:-/tmp}/${candidate}"
report_path="${LIQUID20_DEPLOY_REPORT:-${RUNNER_TEMP:-/tmp}/liquidations-live-synology-report.json}"
previous_image=""
production_replaced=false
deploy_succeeded=false

start_container() {
    local name="$1" selected_image="$2" selected_root="$3" restart_policy="$4"
    docker run -d \
        --name "$name" \
        --restart "$restart_policy" \
        --init \
        --user "${puid}:${pgid}" \
        --read-only \
        --tmpfs /tmp:size=64m,mode=1777 \
        --cap-drop ALL \
        --security-opt no-new-privileges:true \
        --pids-limit 128 \
        --memory 512m \
        --cpus 1.0 \
        --stop-timeout 30 \
        --mount "type=bind,src=${selected_root},dst=/data" \
        --env "COLLECTOR_COMMIT=${commit_sha}" \
        --env "LIQUIDATION_STAGING_HOST_ID=${host_id}" \
        --env LIQUID20_DATA_ROOT=/data \
        --env LIQUID20_HEARTBEAT_SECONDS=5 \
        --env LIQUID20_SYMBOL_REFRESH_SECONDS=3600 \
        --env LIQUID20_MAXIMUM_SYMBOLS=500 \
        --label io.freqtrade.liquidations.live=true \
        --label "io.freqtrade.liquidations.commit=${commit_sha}" \
        --entrypoint /usr/local/bin/liquid20-live-entrypoint \
        "$selected_image"
}

cleanup() {
    docker rm -f "$candidate" >/dev/null 2>&1 || true
    rm -rf "$candidate_root"
    if [[ "$production_replaced" == true && "$deploy_succeeded" != true ]]; then
        docker rm -f "$container_name" >/dev/null 2>&1 || true
        if [[ -n "$previous_image" ]] && docker image inspect "$previous_image" >/dev/null 2>&1; then
            echo "Restoring previous live collector image: $previous_image" >&2
            start_container "$container_name" "$previous_image" "$data_root" unless-stopped \
                >/dev/null || true
        fi
    fi
}
trap cleanup EXIT

history_digest() {
    python3 - "$data_root" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
runs = root / "runs"
digest = hashlib.sha256()
if runs.is_dir() and not runs.is_symlink():
    for run in sorted(runs.iterdir(), key=lambda item: item.name):
        if not run.is_dir() or run.is_symlink():
            continue
        report = run / "multi-source-acceptance-report.json"
        if not report.is_file() or report.is_symlink():
            continue
        for path in sorted(run.iterdir(), key=lambda item: item.name):
            if not path.is_file() or path.is_symlink():
                continue
            resolved = path.resolve()
            if os.path.commonpath((str(root), str(resolved))) != str(root):
                raise SystemExit("historical evidence escaped data root")
            digest.update(f"{run.name}/{path.name}\0".encode())
            with path.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
print(digest.hexdigest())
PY
}

observe_state() {
    python3 - "$1" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
pointer = root / "live" / "live-state-v1.json"
if not pointer.is_file() or pointer.is_symlink():
    raise SystemExit(1)
payload = json.loads(pointer.read_text(encoding="utf-8"))
state = payload.get("state")
if not isinstance(state, dict) or state.get("run_state") != "active":
    raise SystemExit(1)
sources = state.get("sources")
if not isinstance(sources, dict):
    raise SystemExit(1)
for source in ("bybit-linear", "binance-usdm"):
    item = sources.get(source)
    if not isinstance(item, dict) or item.get("configured") is not True:
        raise SystemExit(1)
run_root = root / "live" / "runs" / str(state.get("run_id"))
sizes = {}
for name in ("bybit-linear.ndjson", "binance-usdm.ndjson"):
    path = run_root / name
    sizes[name] = path.stat().st_size if path.is_file() and not path.is_symlink() else -1
print(json.dumps({
    "run_id": state.get("run_id"),
    "collector_heartbeat_at_ms": state.get("collector_heartbeat_at_ms"),
    "last_event_at_ms": state.get("last_event_at_ms"),
    "sources": sources,
    "sizes": sizes,
}, separators=(",", ":"), sort_keys=True))
PY
}

wait_for_active_state() {
    local root="$1" minimum_heartbeat="$2" observation=""
    for _ in $(seq 1 90); do
        observation="$(observe_state "$root" 2>/dev/null || true)"
        if [[ -n "$observation" ]] && python3 - "$observation" "$minimum_heartbeat" <<'PY'
import json
import sys
payload = json.loads(sys.argv[1])
heartbeat = payload.get("collector_heartbeat_at_ms")
if not isinstance(heartbeat, int) or heartbeat <= int(sys.argv[2]):
    raise SystemExit(1)
for source in ("bybit-linear", "binance-usdm"):
    item = payload["sources"][source]
    if not isinstance(item.get("subscription_symbol_count"), int):
        raise SystemExit(1)
    if item["subscription_symbol_count"] < 1:
        raise SystemExit(1)
PY
        then
            printf '%s' "$observation"
            return 0
        fi
        sleep 2
    done
    echo "Collector did not expose active state and dynamic subscriptions" >&2
    return 1
}

[[ "$puid" =~ ^[1-9][0-9]*$ ]]
[[ "$pgid" =~ ^[1-9][0-9]*$ ]]
[[ "$commit_sha" =~ ^[0-9a-f]{40}$ ]]
docker version >/dev/null
docker compose version >/dev/null
test -S /var/run/docker.sock
test -d "$data_root"
test ! -L "$data_root"

history_before="$(history_digest)"
echo "Building exact live collector image: $image"
docker build \
    --pull \
    --file deploy/synology/liquid20/Dockerfile \
    --build-arg "COLLECTOR_COMMIT=${commit_sha}" \
    --label "org.opencontainers.image.revision=${commit_sha}" \
    --tag "$image" \
    .

install -d -m 0750 -o "$puid" -g "$pgid" "$candidate_root"
candidate_started_ms="$(date +%s%3N)"
start_container "$candidate" "$image" "$candidate_root" no >/dev/null
candidate_first="$(wait_for_active_state "$candidate_root" "$candidate_started_ms")"
sleep 6
candidate_second="$(observe_state "$candidate_root")"
python3 - "$candidate_first" "$candidate_second" <<'PY'
import json
import sys
first, second = map(json.loads, sys.argv[1:3])
if second["collector_heartbeat_at_ms"] <= first["collector_heartbeat_at_ms"]:
    raise SystemExit("candidate heartbeat did not advance")
PY
docker rm -f "$candidate" >/dev/null

if docker inspect "$container_name" >/dev/null 2>&1; then
    previous_image="$(docker inspect --format '{{.Config.Image}}' "$container_name")"
    docker rm -f "$container_name" >/dev/null
fi
production_replaced=true
production_started_ms="$(date +%s%3N)"
start_container "$container_name" "$image" "$data_root" unless-stopped >/dev/null
production_first="$(wait_for_active_state "$data_root" "$production_started_ms")"
sleep 30
production_second="$(observe_state "$data_root")"

running_image="$(docker inspect --format '{{.Config.Image}}' "$container_name")"
running_uid="$(docker exec "$container_name" id -u)"
restart_policy="$(docker inspect --format '{{.HostConfig.RestartPolicy.Name}}' "$container_name")"
data_mount_rw="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.RW}}{{end}}{{end}}' "$container_name")"
docker_socket_mount="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/run/docker.sock"}}{{.Source}}{{end}}{{end}}' "$container_name")"
history_after="$(history_digest)"

test "$running_image" = "$image"
test "$running_uid" = "$puid"
test "$running_uid" != "0"
test "$restart_policy" = "unless-stopped"
test "$data_mount_rw" = "true"
test -z "$docker_socket_mount"
test "$history_before" = "$history_after"

python3 - \
    "$candidate_first" "$candidate_second" \
    "$production_first" "$production_second" \
    "$history_before" "$history_after" \
    "$running_uid" "$restart_policy" "$commit_sha" "$report_path" <<'PY'
import json
import sys
from pathlib import Path

candidate_first, candidate_second, production_first, production_second = map(
    json.loads, sys.argv[1:5]
)
if production_second["collector_heartbeat_at_ms"] <= production_first["collector_heartbeat_at_ms"]:
    raise SystemExit("production heartbeat did not advance")
file_growth = any(
    production_second["sizes"].get(name, -1) > production_first["sizes"].get(name, -1)
    for name in ("bybit-linear.ndjson", "binance-usdm.ndjson")
)
real_event = production_second.get("last_event_at_ms") != production_first.get("last_event_at_ms")
report = {
    "schema_version": 1,
    "commit_sha": sys.argv[9],
    "candidate": {"first": candidate_first, "second": candidate_second},
    "production": {"first": production_first, "second": production_second},
    "runtime": {"uid": int(sys.argv[7]), "restart_policy": sys.argv[8]},
    "historical_evidence": {
        "digest_before": sys.argv[5],
        "digest_after": sys.argv[6],
        "unchanged": sys.argv[5] == sys.argv[6],
    },
    "real_event_observed_during_window": real_event,
    "source_file_growth_observed_during_window": file_growth,
    "real_event_note": (
        "A real exchange event advanced during the observation window."
        if real_event or file_growth
        else "No real liquidation was observed; heartbeat and subscriptions advanced."
    ),
    "portal_mount_expected_read_only": True,
    "trading_authorized": False,
}
path = Path(sys.argv[10])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

deploy_succeeded=true
printf 'Live collector deployed: image=%s container=%s uid=%s restart=%s report=%s\n' \
    "$image" "$container_name" "$running_uid" "$restart_policy" "$report_path"
