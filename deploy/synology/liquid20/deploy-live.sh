#!/usr/bin/env bash
set -Eeuo pipefail

image_name="${LIQUID20_IMAGE_NAME:-local/liquid20-collector}"
container_name="${LIQUID20_CONTAINER_NAME:-liquid20-live}"
data_root="${LIQUID20_DATA_ROOT:-/volume1/docker/freqtrade-liquidations/data}"
defaults_file="deploy/synology/liquid20/.env.example"
commit_sha="${GITHUB_SHA:?GITHUB_SHA is required}"
image="${image_name}:sha-${commit_sha}"
prebuilt_image="${LIQUID20_PREBUILT_IMAGE:-}"
candidate_token="${GITHUB_RUN_ID:-manual}-${GITHUB_RUN_ATTEMPT:-1}"
candidate="${container_name}-candidate-${candidate_token}"
candidate_runner_root="${LIQUID20_CANDIDATE_RUNNER_ROOT:-/var/lib/freqtrade-staging-state/liquidations-live-candidates/${candidate_token}}"
candidate_host_root="${LIQUID20_CANDIDATE_HOST_ROOT:-/volume1/docker/freqtrade/state/liquidations-live-candidates/${candidate_token}}"
report_path="${LIQUID20_DEPLOY_REPORT:-${RUNNER_TEMP:-/tmp}/liquidations-live-synology-report.json}"
previous_image=""
previous_commit=""
production_replaced=false
deploy_succeeded=false
puid=""
pgid=""
host_id=""
maximum_symbols=""
cpu_limit_supported=false
cpu_limit_args=()
pids_limit_supported=false
pids_limit_args=()

cleanup() {
    docker rm -f "$candidate" >/dev/null 2>&1 || true
    if [[ "$candidate_runner_root" == /var/lib/freqtrade-staging-state/liquidations-live-candidates/* ]]; then
        rm -rf "$candidate_runner_root"
    fi
    if [[ "$production_replaced" == true && "$deploy_succeeded" != true ]]; then
        docker rm -f "$container_name" >/dev/null 2>&1 || true
        if [[ -n "$previous_image" && "$previous_commit" =~ ^[0-9a-f]{40}$ ]] \
            && docker image inspect "$previous_image" >/dev/null 2>&1; then
            echo "Restoring previous live collector image: $previous_image" >&2
            start_container \
                "$container_name" "$previous_image" "$data_root" unless-stopped "$previous_commit" \
                >/dev/null || true
        fi
    fi
}
trap cleanup EXIT

read_default() {
    local key="$1"
    sed -n "s/^${key}=//p" "$defaults_file" | head -n 1
}

validate_uid() {
    [[ "$1" =~ ^[0-9]+$ ]] && [[ "$1" -gt 0 ]]
}

validate_gid() {
    [[ "$1" =~ ^[0-9]+$ ]]
}

configure_cpu_limit() {
    local probe_output=""
    if probe_output="$(docker run --rm --cpus 0.1 --entrypoint /bin/true "$image" 2>&1)"; then
        cpu_limit_supported=true
        cpu_limit_args=(--cpus 1.0)
        echo "Docker CPU quota supported; applying a 1.0 CPU limit."
        return 0
    fi
    if grep -Eiq \
        'NanoCPUs can not be set|kernel does not support CPU CFS scheduler|cgroup is not mounted' \
        <<< "$probe_output"; then
        cpu_limit_supported=false
        cpu_limit_args=()
        echo "Docker CPU quota is unavailable on this Synology kernel; retaining supported resource limits."
        return 0
    fi
    printf '%s\n' "$probe_output" >&2
    echo "Docker CPU quota capability probe failed for an unexpected reason" >&2
    return 1
}

configure_pids_limit() {
    local probe_output=""
    local probe_status=0
    set +e
    probe_output="$(docker run --rm --pids-limit 32 --entrypoint /bin/true "$image" 2>&1)"
    probe_status=$?
    set -e
    if grep -Eiq \
        'kernel does not support PIDs limit capabilities|PIDs limit discarded|pids cgroup is not mounted' \
        <<< "$probe_output"; then
        pids_limit_supported=false
        pids_limit_args=()
        echo "Docker PID limit is unavailable on this Synology kernel; retaining the memory limit."
        return 0
    fi
    if [[ "$probe_status" -eq 0 ]]; then
        pids_limit_supported=true
        pids_limit_args=(--pids-limit 128)
        echo "Docker PID limit supported; applying a 128 process limit."
        return 0
    fi
    printf '%s\n' "$probe_output" >&2
    echo "Docker PID limit capability probe failed for an unexpected reason" >&2
    return 1
}

inspect_data_root() {
    docker run --rm --interactive \
        --read-only \
        --entrypoint python \
        --mount "type=bind,src=${data_root},dst=/data,readonly" \
        "$image" - <<'PY'
from pathlib import Path

root = Path("/data")
runs = root / "runs"
for path in (root, runs):
    item = path.lstat()
    if not path.is_dir() or path.is_symlink():
        raise SystemExit(f"invalid directory: {path}")
    if item.st_mode & 0o050 != 0o050:
        raise SystemExit(f"directory is not group-readable/traversable: {path}")
if root.stat().st_gid != runs.stat().st_gid:
    raise SystemExit("data root and accepted-runs root use different groups")
print(f"{root.stat().st_gid}|{root.stat().st_mode & 0o777:o}")
PY
}

history_digest() {
    docker run --rm --interactive \
        --read-only \
        --entrypoint python \
        --mount "type=bind,src=${data_root},dst=/data,readonly" \
        "$image" - <<'PY'
import hashlib
import os
from pathlib import Path

root = Path("/data").resolve()
runs = root / "runs"
if not runs.is_dir() or runs.is_symlink():
    print(hashlib.sha256(b"").hexdigest())
    raise SystemExit(0)
aggregate = hashlib.sha256()
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
        aggregate.update(f"{run.name}/{path.name}\0".encode())
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                aggregate.update(chunk)
print(aggregate.hexdigest())
PY
}

bootstrap_live_root() {
    docker run --rm --interactive \
        --user 0:0 \
        --read-only \
        --entrypoint python \
        --mount "type=bind,src=${data_root},dst=/data" \
        "$image" - "$puid" "$pgid" <<'PY'
import os
import stat
import sys
from pathlib import Path

uid = int(sys.argv[1])
gid = int(sys.argv[2])
root = Path("/data")
accepted = root / "runs"
if not accepted.is_dir() or accepted.is_symlink():
    raise SystemExit("accepted-runs root is invalid")
live = root / "live"
live_runs = live / "runs"
created: list[Path] = []
for path in (live, live_runs):
    if path.exists():
        if not path.is_dir() or path.is_symlink():
            raise SystemExit(f"live path is invalid: {path}")
    else:
        path.mkdir(mode=0o750)
        created.append(path)
for path in created:
    os.chown(path, uid, gid)
    os.chmod(path, 0o750)
for path in (live, live_runs):
    item = path.lstat()
    mode = stat.S_IMODE(item.st_mode)
    if item.st_uid != uid or item.st_gid != gid:
        raise SystemExit(f"live path identity mismatch: {path}")
    if mode & 0o700 != 0o700 or mode & 0o050 != 0o050 or mode & 0o022:
        raise SystemExit(f"live path mode is unsafe: {path} mode={mode:o}")
print(f"live_root_ready uid={uid} gid={gid}")
PY
}

state_observation() {
    local selected_container="$1"
    local observation_timeout_seconds="${2:-10}"
    timeout "${observation_timeout_seconds}s" docker exec --interactive "$selected_container" python - <<'PY'
import json
from pathlib import Path

root = Path("/data")
pointer = root / "live" / "live-state-v1.json"
if not pointer.is_file() or pointer.is_symlink():
    raise SystemExit(1)
payload = json.loads(pointer.read_text(encoding="utf-8"))
state = payload.get("state")
if not isinstance(state, dict):
    raise SystemExit(1)
sources = state.get("sources")
if not isinstance(sources, dict):
    raise SystemExit(1)
run_id = state.get("run_id")
run_root = root / "live" / "runs" / str(run_id)
sizes = {}
for name in ("bybit-linear.ndjson", "binance-usdm.ndjson", "okx-swap.ndjson"):
    path = run_root / name
    sizes[name] = path.stat().st_size if path.is_file() and not path.is_symlink() else -1
print(json.dumps({
    "run_id": run_id,
    "run_state": state.get("run_state"),
    "collector_heartbeat_at_ms": state.get("collector_heartbeat_at_ms"),
    "last_event_at_ms": state.get("last_event_at_ms"),
    "sources": sources,
    "sizes": sizes,
}, separators=(",", ":"), sort_keys=True))
PY
}

wait_for_state() {
    local selected_container="$1"
    local minimum_heartbeat="$2"
    local observation=""
    local container_state=""
    for _ in $(seq 1 60); do
        container_state="$(docker inspect --format '{{.State.Status}}' "$selected_container" 2>/dev/null || true)"
        if [[ "$container_state" == "exited" || "$container_state" == "dead" ]]; then
            docker logs --tail 200 "$selected_container" >&2 2>&1 || true
            echo "Live collector container exited before becoming ready: ${selected_container}" >&2
            return 1
        fi
        observation="$(state_observation "$selected_container" 2>/dev/null || true)"
        if [[ -n "$observation" ]] && python3 - "$observation" "$minimum_heartbeat" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
minimum = int(sys.argv[2])
if payload.get("run_state") != "active":
    raise SystemExit(1)
heartbeat = payload.get("collector_heartbeat_at_ms")
if not isinstance(heartbeat, int) or heartbeat <= minimum:
    raise SystemExit(1)
sources = payload.get("sources", {})
for source in ("bybit-linear", "binance-usdm", "okx-swap"):
    item = sources.get(source)
    if not isinstance(item, dict) or item.get("configured") is not True:
        raise SystemExit(1)
    if item.get("connected") is not True:
        raise SystemExit(1)
    count = item.get("subscription_symbol_count")
    if not isinstance(count, int) or count < 1:
        raise SystemExit(1)
PY
        then
            printf '%s' "$observation"
            return 0
        fi
        sleep 2
    done
    printf 'Last collector observation: %s\n' "${observation:-unavailable}" >&2
    docker logs --tail 200 "$selected_container" >&2 2>&1 || true
    echo "Live collector state did not become connected with dynamic subscriptions" >&2
    return 1
}

wait_for_heartbeat_advance() {
    local selected_container="$1"
    local first_observation="$2"
    local observation=""
    local first_heartbeat=""
    local deadline=0
    local remaining=0
    first_heartbeat="$(python3 - "$first_observation" <<'PY'
import json
import sys

heartbeat = json.loads(sys.argv[1]).get("collector_heartbeat_at_ms")
if not isinstance(heartbeat, int):
    raise SystemExit("initial collector heartbeat is invalid")
print(heartbeat)
PY
)"
    deadline=$((SECONDS + 30))
    while (( SECONDS < deadline )); do
        remaining=$((deadline - SECONDS))
        if (( remaining > 10 )); then
            remaining=10
        fi
        observation="$(state_observation "$selected_container" "$remaining" 2>/dev/null || true)"
        if [[ -n "$observation" ]] && python3 - "$observation" "$first_heartbeat" <<'PY'
import json
import sys

heartbeat = json.loads(sys.argv[1]).get("collector_heartbeat_at_ms")
if not isinstance(heartbeat, int) or heartbeat <= int(sys.argv[2]):
    raise SystemExit(1)
PY
        then
            printf '%s' "$observation"
            return 0
        fi
        remaining=$((deadline - SECONDS))
        if (( remaining > 0 )); then
            sleep "$(( remaining < 2 ? remaining : 2 ))"
        fi
    done
    printf 'Last collector observation while waiting for heartbeat advance: %s\n' \
        "${observation:-unavailable}" >&2
    echo "Collector heartbeat did not advance within 30 seconds" >&2
    return 1
}

start_container() {
    local name="$1"
    local selected_image="$2"
    local selected_root="$3"
    local restart_policy="$4"
    local selected_commit="$5"
    local -a run_args=(
        --name "$name"
        --restart "$restart_policy"
        --init
        --user "${puid}:${pgid}"
        --read-only
        --tmpfs /tmp:size=64m,mode=1777
        --cap-drop ALL
        --security-opt no-new-privileges:true
        --memory 512m
    )
    [[ "$selected_commit" =~ ^[0-9a-f]{40}$ ]]
    run_args+=("${cpu_limit_args[@]}")
    run_args+=("${pids_limit_args[@]}")
    run_args+=(
        --stop-timeout 30
        --mount "type=bind,src=${selected_root},dst=/data"
        --env "COLLECTOR_COMMIT=${selected_commit}"
        --env "LIQUIDATION_STAGING_HOST_ID=${host_id}"
        --env LIQUID20_DATA_ROOT=/data
        --env LIQUID20_HEARTBEAT_SECONDS=5
        --env LIQUID20_SYMBOL_REFRESH_SECONDS=3600
        --env "LIQUID20_MAXIMUM_SYMBOLS=${maximum_symbols}"
        --label io.freqtrade.liquidations.live=true
        --label "io.freqtrade.liquidations.commit=${selected_commit}"
        --entrypoint /usr/local/bin/liquid20-live-entrypoint
    )
    docker run -d "${run_args[@]}" "$selected_image"
}

[[ "$commit_sha" =~ ^[0-9a-f]{40}$ ]]
[[ "$candidate_runner_root" == /var/lib/freqtrade-staging-state/liquidations-live-candidates/* ]]
[[ "$candidate_host_root" == /volume1/docker/freqtrade/state/liquidations-live-candidates/* ]]
if [[ "${GITHUB_ACTIONS:-}" == "true" && "${GITHUB_REF:-}" != "refs/heads/develop" ]]; then
    echo "Production live deployment is allowed only from refs/heads/develop" >&2
    exit 64
fi

docker version >/dev/null
docker compose version >/dev/null
test -S /var/run/docker.sock
test -f "$defaults_file"

if [[ -n "$prebuilt_image" ]]; then
    if [[ ! "$prebuilt_image" =~ ^ghcr\.io/blakinio/liquid20-collector@sha256:[0-9a-f]{64}$ ]]; then
        echo "LIQUID20_PREBUILT_IMAGE must be an immutable approved GHCR digest reference" >&2
        exit 64
    fi
    docker image inspect "$prebuilt_image" >/dev/null
    prebuilt_id="$(docker image inspect --format '{{.Id}}' "$prebuilt_image")"
    [[ "$prebuilt_id" =~ ^sha256:[0-9a-f]{64}$ ]]
    prebuilt_revision="$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$prebuilt_image")"
    if [[ "$prebuilt_revision" != "$commit_sha" ]]; then
        echo "Prebuilt Liquid20 image revision does not match GITHUB_SHA" >&2
        exit 64
    fi
    docker tag "$prebuilt_image" "$image"
    [[ "$(docker image inspect --format '{{.Id}}' "$image")" == "$prebuilt_id" ]]
    echo "Using exact prebuilt live collector image: $prebuilt_image -> $image"
elif [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    echo "GitHub Actions deployment requires LIQUID20_PREBUILT_IMAGE; refusing Synology build fallback" >&2
    exit 64
else
    echo "Building exact live collector image: $image"
    docker build \
        --pull \
        --file deploy/synology/liquid20/Dockerfile \
        --build-arg "COLLECTOR_COMMIT=${commit_sha}" \
        --label "org.opencontainers.image.source=${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-blakinio/freqtrade}" \
        --label "org.opencontainers.image.revision=${commit_sha}" \
        --tag "$image" \
        .
fi

configure_cpu_limit
configure_pids_limit

data_identity="$(inspect_data_root)"
IFS='|' read -r data_gid data_mode <<< "$data_identity"
validate_gid "$data_gid"
puid="${LIQUID20_PUID:-$(read_default PUID)}"
validate_uid "$puid"
if [[ -n "${LIQUID20_PGID:-}" && "${LIQUID20_PGID}" != "$data_gid" ]]; then
    echo "LIQUID20_PGID must match the existing data-root group (${data_gid})" >&2
    exit 64
fi
pgid="$data_gid"
host_id="${LIQUID20_HOST_ID:-$(read_default HOST_ID)}"
[[ "$host_id" =~ ^[A-Za-z0-9._-]+$ ]]
maximum_symbols="${LIQUID20_MAXIMUM_SYMBOLS:-$(read_default MAXIMUM_SYMBOLS)}"
[[ "$maximum_symbols" =~ ^[0-9]+$ ]]
(( maximum_symbols >= 1 && maximum_symbols <= 1000 ))
printf 'Resolved collector identity: uid=%s gid=%s data_mode=%s host_id=%s maximum_symbols=%s\n' \
    "$puid" "$pgid" "$data_mode" "$host_id" "$maximum_symbols"

history_before="$(history_digest)"
install -d -m 0750 -o "$puid" -g "$pgid" "$candidate_runner_root"
candidate_started_ms="$(date +%s%3N)"
start_container "$candidate" "$image" "$candidate_host_root" no "$commit_sha" >/dev/null
candidate_first="$(wait_for_state "$candidate" "$candidate_started_ms")"
candidate_second="$(wait_for_heartbeat_advance "$candidate" "$candidate_first")"
docker rm -f "$candidate" >/dev/null

bootstrap_live_root

if docker inspect "$container_name" >/dev/null 2>&1; then
    previous_image="$(docker inspect --format '{{.Config.Image}}' "$container_name")"
    previous_commit="$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$previous_image" 2>/dev/null || true)"
    if [[ ! "$previous_commit" =~ ^[0-9a-f]{40}$ ]]; then
        previous_commit="$(docker run --rm --entrypoint cat "$previous_image" /app/COLLECTOR_COMMIT 2>/dev/null || true)"
    fi
    if [[ ! "$previous_commit" =~ ^[0-9a-f]{40}$ ]]; then
        echo "Previous live collector commit cannot be verified; refusing unsafe replacement" >&2
        exit 1
    fi
    docker rm -f "$container_name" >/dev/null
fi
production_replaced=true
production_started_ms="$(date +%s%3N)"
start_container "$container_name" "$image" "$data_root" unless-stopped "$commit_sha" >/dev/null
production_first="$(wait_for_state "$container_name" "$production_started_ms")"
sleep 30
production_second="$(state_observation "$container_name")"

running_image="$(docker inspect --format '{{.Config.Image}}' "$container_name")"
running_uid="$(docker exec "$container_name" id -u)"
running_gid="$(docker exec "$container_name" id -g)"
restart_policy="$(docker inspect --format '{{.HostConfig.RestartPolicy.Name}}' "$container_name")"
data_mount_rw="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.RW}}{{end}}{{end}}' "$container_name")"
docker_socket_mount="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/run/docker.sock"}}{{.Source}}{{end}}{{end}}' "$container_name")"
running_nano_cpus="$(docker inspect --format '{{.HostConfig.NanoCpus}}' "$container_name")"
running_pids_limit="$(docker inspect --format '{{if .HostConfig.PidsLimit}}{{.HostConfig.PidsLimit}}{{else}}0{{end}}' "$container_name")"
running_memory_limit="$(docker inspect --format '{{.HostConfig.Memory}}' "$container_name")"
history_after="$(history_digest)"

test "$running_image" = "$image"
test "$running_uid" = "$puid"
test "$running_uid" != "0"
test "$running_gid" = "$pgid"
test "$restart_policy" = "unless-stopped"
test "$data_mount_rw" = "true"
test -z "$docker_socket_mount"
test "$history_before" = "$history_after"
test "$running_memory_limit" = "536870912"
if [[ "$cpu_limit_supported" == true ]]; then
    test "$running_nano_cpus" = "1000000000"
else
    test "$running_nano_cpus" = "0"
fi
if [[ "$pids_limit_supported" == true ]]; then
    test "$running_pids_limit" = "128"
else
    test "$running_pids_limit" = "0"
fi

python3 - \
    "$candidate_first" "$candidate_second" \
    "$production_first" "$production_second" \
    "$history_before" "$history_after" \
    "$running_uid" "$running_gid" "$restart_policy" "$data_mount_rw" \
    "$commit_sha" "$report_path" "$host_id" \
    "$cpu_limit_supported" "$running_nano_cpus" \
    "$pids_limit_supported" "$running_pids_limit" "$running_memory_limit" \
    "$maximum_symbols" <<'PY'
import json
import sys
from pathlib import Path

candidate_first = json.loads(sys.argv[1])
candidate_second = json.loads(sys.argv[2])
first = json.loads(sys.argv[3])
second = json.loads(sys.argv[4])
if second["collector_heartbeat_at_ms"] <= first["collector_heartbeat_at_ms"]:
    raise SystemExit("production heartbeat did not advance")
real_event_observed = second.get("last_event_at_ms") != first.get("last_event_at_ms")
file_growth_observed = any(
    second["sizes"].get(name, -1) > first["sizes"].get(name, -1)
    for name in ("bybit-linear.ndjson", "binance-usdm.ndjson", "okx-swap.ndjson")
)
cpu_quota_supported = sys.argv[14] == "true"
nano_cpus = int(sys.argv[15])
pids_limit_supported = sys.argv[16] == "true"
pids_limit = int(sys.argv[17])
memory_limit = int(sys.argv[18])
maximum_symbols = int(sys.argv[19])
report = {
    "schema_version": 1,
    "commit_sha": sys.argv[11],
    "host_id": sys.argv[13],
    "candidate": {"first": candidate_first, "second": candidate_second},
    "production": {"first": first, "second": second},
    "runtime": {
        "uid": int(sys.argv[7]),
        "gid": int(sys.argv[8]),
        "restart_policy": sys.argv[9],
        "data_mount_rw": sys.argv[10] == "true",
        "portal_mount_expected_read_only": True,
        "memory_limit_bytes": memory_limit,
        "pids_limit_supported": pids_limit_supported,
        "pids_limit_applied": pids_limit == 128,
        "pids_limit": pids_limit,
        "cpu_quota_supported": cpu_quota_supported,
        "cpu_quota_applied": nano_cpus == 1_000_000_000,
        "nano_cpus": nano_cpus,
        "maximum_symbols": maximum_symbols,
    },
    "historical_evidence": {
        "digest_before": sys.argv[5],
        "digest_after": sys.argv[6],
        "unchanged": sys.argv[5] == sys.argv[6],
    },
    "real_event_observed_during_window": real_event_observed,
    "source_file_growth_observed_during_window": file_growth_observed,
    "real_event_note": (
        "A real exchange event advanced during the observation window."
        if real_event_observed or file_growth_observed
        else "No real liquidation was published during the bounded observation window; heartbeat and subscriptions advanced."
    ),
    "trading_authorized": False,
}
path = Path(sys.argv[12])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

deploy_succeeded=true
printf 'Live collector deployed: image=%s container=%s uid=%s gid=%s restart=%s report=%s\n' \
    "$image" "$container_name" "$running_uid" "$running_gid" "$restart_policy" "$report_path"
