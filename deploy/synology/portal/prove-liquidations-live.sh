#!/usr/bin/env bash
set -Eeuo pipefail

portal_container="${PORTAL_CONTAINER_NAME:-freqtrade-portal-staging}"
liquidations_host_root="${PORTAL_LIQUIDATIONS_HOST_ROOT:-/volume1/docker/freqtrade-liquidations/data}"
liquidations_container_root="/liquid20-data"
report_path="${PORTAL_LIVE_PROOF_REPORT_PATH:?PORTAL_LIVE_PROOF_REPORT_PATH is required}"
observation_delay="${PORTAL_LIVE_PROOF_DELAY_SECONDS:-12}"
candidate="${PORTAL_LIVE_PROOF_CANDIDATE:-freqtrade-portal-live-proof-${GITHUB_RUN_ID:-manual}-${GITHUB_RUN_ATTEMPT:-1}}"
proof_stage="input_validation"

mkdir -p "$(dirname "$report_path")"
work_dir="$(mktemp -d)"
cleanup() {
  local status=$?
  trap - EXIT
  docker rm -f "$candidate" >/dev/null 2>&1 || true
  if (( status != 0 )) && [[ ! -s "$report_path" ]]; then
    PROOF_EXIT_STATUS="$status" \
    PROOF_FAILURE_STAGE="$proof_stage" \
    GITHUB_SHA_VALUE="${GITHUB_SHA:-unknown}" \
    REPORT_PATH="$report_path" \
    python3 - <<'PY' || true
import json
import os
from pathlib import Path

stage = os.environ["PROOF_FAILURE_STAGE"]
report = {
    "schema_version": 1,
    "report_type": "liquidations_live_portal_synology_proof",
    "commit_sha": os.environ["GITHUB_SHA_VALUE"],
    "result": "failure",
    "rejection_reason": f"proof failed during {stage}",
    "exit_status": int(os.environ["PROOF_EXIT_STATUS"]),
}
Path(os.environ["REPORT_PATH"]).write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
  fi
  rm -rf "$work_dir"
  exit "$status"
}
trap cleanup EXIT

case "$observation_delay" in
  *[!0-9]* | "")
    echo "PORTAL_LIVE_PROOF_DELAY_SECONDS must be a positive integer" >&2
    exit 64
    ;;
esac
if (( observation_delay < 5 || observation_delay > 120 )); then
  echo "PORTAL_LIVE_PROOF_DELAY_SECONDS must be between 5 and 120" >&2
  exit 64
fi

pids_limit_supported=false
pids_limit_args=()

configure_pids_limit() {
  local probe_output=""
  local probe_status=0
  set +e
  probe_output="$(docker run --rm --pids-limit 32 --entrypoint /bin/true "$portal_image" 2>&1)"
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
    pids_limit_args=(--pids-limit 256)
    echo "Docker PID limit supported; applying a 256 process limit."
    return 0
  fi
  printf '%s\n' "$probe_output" >&2
  echo "Docker PID limit capability probe failed for an unexpected reason" >&2
  return 1
}

proof_stage="production_container_preflight"
docker version >/dev/null
test -S /var/run/docker.sock
test "$(docker inspect --format '{{.State.Running}}' "$portal_container")" = "true"

portal_image="$(docker inspect --format '{{.Config.Image}}' "$portal_container")"
portal_image_id="$(docker inspect --format '{{.Image}}' "$portal_container")"
mount_source="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/liquid20-data"}}{{.Source}}{{end}}{{end}}' "$portal_container")"
mount_rw="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/liquid20-data"}}{{.RW}}{{end}}{{end}}' "$portal_container")"
docker_socket_mount="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/run/docker.sock"}}{{.Source}}{{end}}{{end}}' "$portal_container")"
portal_restart="$(docker inspect --format '{{.HostConfig.RestartPolicy.Name}}' "$portal_container")"
portal_uid="$(docker exec "$portal_container" id -u)"
portal_groups="$(docker exec "$portal_container" id -G)"

test -n "$portal_image"
test -n "$portal_image_id"
test "$mount_source" = "$liquidations_host_root"
test "$mount_rw" = "false"
test -z "$docker_socket_mount"
test "$portal_uid" != "0"
test "$portal_restart" = "unless-stopped"
configure_pids_limit

data_gid="$(
  docker run --rm \
    --user 0:0 \
    --entrypoint node \
    --mount "type=bind,src=${liquidations_host_root},dst=${liquidations_container_root},readonly" \
    "$portal_image" \
    -e 'const fs=require("node:fs");const s=fs.lstatSync("/liquid20-data");if(!s.isDirectory()||s.isSymbolicLink())process.exit(1);process.stdout.write(String(s.gid));'
)"
[[ "$data_gid" =~ ^[0-9]+$ ]]
[[ " $portal_groups " == *" $data_gid "* ]]

proof_stage="production_authentication_boundary"
production_boundary="$work_dir/production-boundary.json"
docker exec "$portal_container" node -e '
  Promise.all([
    fetch("http://127.0.0.1:3000/market/liquidations", {cache:"no-store"}),
    fetch("http://127.0.0.1:3000/api/market/liquidations/health", {cache:"no-store"}),
  ]).then(async ([page, health]) => {
    const payload = await health.json().catch(() => ({}));
    const result = {
      page_status: page.status,
      health_status: health.status,
      health_code: payload.code ?? null,
      health_cache_control: health.headers.get("cache-control"),
    };
    if (page.status !== 200) process.exit(1);
    if (health.status !== 401 || payload.code !== "SESSION_MISSING") process.exit(1);
    if (!(result.health_cache_control || "").includes("no-store")) process.exit(1);
    process.stdout.write(JSON.stringify(result));
  }).catch((error) => { console.error(error); process.exit(1); });
' > "$production_boundary"

if docker inspect "$candidate" >/dev/null 2>&1; then
  echo "Candidate already exists: $candidate" >&2
  exit 73
fi

proof_stage="candidate_startup"
run_args=(
  docker run -d
  --name "$candidate"
  --restart no
  --read-only
  --tmpfs /tmp:size=64m,mode=1777
  --tmpfs /app/.next/cache:size=64m,mode=0755
  --cap-drop ALL
  --security-opt no-new-privileges:true
  --memory 768m
)
run_args+=("${pids_limit_args[@]}")
run_args+=(
  --group-add "$data_gid"
  --mount "type=bind,src=${liquidations_host_root},dst=${liquidations_container_root},readonly"
  --env PORTAL_WEB_DATA_MODE=fixture
  --env PORTAL_ENVIRONMENT=test
  --env PORTAL_IDENTITY_FIXTURE_MODE=enabled
  --env "PORTAL_LIQUIDATIONS_DATA_ROOT=${liquidations_container_root}"
  --label io.freqtrade.portal.liquidations-live-proof=true
  --label "io.freqtrade.portal.proof-commit=${GITHUB_SHA:-unknown}"
  "$portal_image"
)
"${run_args[@]}" >/dev/null

for _ in $(seq 1 60); do
  status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$candidate" 2>/dev/null || true)"
  if [[ "$status" == "healthy" ]]; then
    break
  fi
  if [[ "$status" == "exited" || "$status" == "dead" ]]; then
    docker logs --tail 120 "$candidate" >&2 || true
    exit 1
  fi
  sleep 2
done
test "$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$candidate")" = "healthy"

proof_stage="candidate_runtime_security"
candidate_image="$(docker inspect --format '{{.Config.Image}}' "$candidate")"
candidate_image_id="$(docker inspect --format '{{.Image}}' "$candidate")"
candidate_restart="$(docker inspect --format '{{.HostConfig.RestartPolicy.Name}}' "$candidate")"
candidate_mount_source="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/liquid20-data"}}{{.Source}}{{end}}{{end}}' "$candidate")"
candidate_mount_rw="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/liquid20-data"}}{{.RW}}{{end}}{{end}}' "$candidate")"
candidate_docker_socket_mount="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/run/docker.sock"}}{{.Source}}{{end}}{{end}}' "$candidate")"
candidate_uid="$(docker exec "$candidate" id -u)"
candidate_groups="$(docker exec "$candidate" id -G)"
candidate_readonly_rootfs="$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' "$candidate")"
candidate_cap_drop_json="$(docker inspect --format '{{json .HostConfig.CapDrop}}' "$candidate")"
candidate_security_opt_json="$(docker inspect --format '{{json .HostConfig.SecurityOpt}}' "$candidate")"
candidate_tmpfs_json="$(docker inspect --format '{{json .HostConfig.Tmpfs}}' "$candidate")"
candidate_memory_limit="$(docker inspect --format '{{.HostConfig.Memory}}' "$candidate")"
candidate_pids_limit_json="$(docker inspect --format '{{json .HostConfig.PidsLimit}}' "$candidate")"

test "$candidate_image" = "$portal_image"
test "$candidate_image_id" = "$portal_image_id"
test "$candidate_restart" = "no"
test "$candidate_mount_source" = "$liquidations_host_root"
test "$candidate_mount_rw" = "false"
test -z "$candidate_docker_socket_mount"
test "$candidate_uid" != "0"
[[ " $candidate_groups " == *" $data_gid "* ]]
test "$candidate_readonly_rootfs" = "true"
test "$candidate_cap_drop_json" = '["ALL"]'
[[ "$candidate_security_opt_json" == *'no-new-privileges:true'* ]]
test "$candidate_memory_limit" = "805306368"

CANDIDATE_TMPFS_JSON="$candidate_tmpfs_json" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["CANDIDATE_TMPFS_JSON"])
if set(payload) != {"/tmp", "/app/.next/cache"}:
    raise SystemExit("candidate tmpfs paths do not match the bounded proof contract")
PY

if [[ "$pids_limit_supported" == true ]]; then
  test "$candidate_pids_limit_json" = "256"
else
  case "$candidate_pids_limit_json" in
    null | 0)
      ;;
    *)
      echo "Unexpected unlimited PID representation: $candidate_pids_limit_json" >&2
      exit 1
      ;;
  esac
fi

proof_stage="candidate_fixture_session"
fixture_cookie="$(
  docker exec "$candidate" node -e '
    (async () => {
      const unauthenticated = await fetch(
        "http://127.0.0.1:3000/api/market/liquidations/health",
        {cache:"no-store", headers:{accept:"application/json"}},
      );
      const unauthenticatedPayload = await unauthenticated.json().catch(() => ({}));
      if (unauthenticated.status !== 401 || unauthenticatedPayload.code !== "SESSION_MISSING") {
        throw new Error("isolated candidate did not reject the unauthenticated API request");
      }
      const login = await fetch(
        "http://127.0.0.1:3000/api/identity/login?return_to=%2Fplatform%2Fadmin",
        {redirect:"manual"},
      );
      if (login.status !== 303) throw new Error(`fixture login status ${login.status}`);
      const location = login.headers.get("location");
      if (!location || new URL(location, "http://127.0.0.1:3000").pathname !== "/platform/admin") {
        throw new Error("fixture login redirect mismatch");
      }
      const setCookies = login.headers.getSetCookie?.() ?? [];
      if (!setCookies.some((value) => value.startsWith("portal_fixture_session="))) {
        throw new Error("fixture session cookie missing");
      }
      if (!setCookies.some((value) => value.startsWith("portal_fixture_csrf="))) {
        throw new Error("fixture CSRF cookie missing");
      }
      const cookie = setCookies.map((value) => value.split(";", 1)[0]).join("; ");
      const session = await fetch("http://127.0.0.1:3000/api/identity/session", {
        cache:"no-store",
        headers:{cookie},
      });
      const sessionPayload = await session.json().catch(() => ({}));
      if (session.status !== 200 || sessionPayload.tenant_id !== "tenant-demo") {
        throw new Error("fixture session validation failed");
      }
      process.stdout.write(cookie);
    })().catch((error) => { console.error(error); process.exit(1); });
  '
)"
test -n "$fixture_cookie"
[[ "$fixture_cookie" == *"portal_fixture_session="* ]]
[[ "$fixture_cookie" == *"portal_fixture_csrf="* ]]

probe() {
  docker exec --env "PORTAL_FIXTURE_COOKIE=$fixture_cookie" "$candidate" node -e '
    const fs = require("node:fs");
    const path = require("node:path");
    const fixtureCookie = process.env.PORTAL_FIXTURE_COOKIE ?? "";
    if (!fixtureCookie.includes("portal_fixture_session=")) throw new Error("fixture session is unavailable");
    async function requestJson(route) {
      const response = await fetch(`http://127.0.0.1:3000${route}`, {
        cache:"no-store",
        headers:{accept:"application/json",cookie:fixtureCookie},
      });
      const payload = await response.json().catch(() => ({}));
      if (response.status !== 200) throw new Error(`${route} status ${response.status}: ${JSON.stringify(payload)}`);
      const cacheControl = response.headers.get("cache-control") || "";
      if (!cacheControl.includes("no-store")) throw new Error(`${route} is not no-store`);
      return {payload, cache_control: cacheControl};
    }
    function containsLabels(root) {
      const required = ["Ostatnie zdarzenie", "Ostatni heartbeat collectora", "Ostatnie sprawdzenie przez portal"];
      const found = new Set();
      const stack = [root];
      while (stack.length) {
        const current = stack.pop();
        for (const entry of fs.readdirSync(current, {withFileTypes:true})) {
          const child = path.join(current, entry.name);
          if (entry.isDirectory()) stack.push(child);
          else if (entry.isFile() && entry.name.endsWith(".js")) {
            const content = fs.readFileSync(child, "utf8");
            for (const label of required) if (content.includes(label)) found.add(label);
          }
        }
      }
      return required.every((label) => found.has(label));
    }
    Promise.all([
      requestJson("/api/market/liquidations/health"),
      requestJson("/api/market/liquidations?limit=20"),
      requestJson("/api/market/liquidations/summary"),
      fetch("http://127.0.0.1:3000/market/liquidations", {
        cache:"no-store",
        headers:{cookie:fixtureCookie},
      }),
    ]).then(([healthResult, listResult, summaryResult, page]) => {
      const health = healthResult.payload;
      const list = listResult.payload;
      const summary = summaryResult.payload;
      if (page.status !== 200) throw new Error(`page status ${page.status}`);
      if (health.contract !== "portal-liquidations-health-v2") throw new Error("health contract mismatch");
      if (health.mode !== "live" || health.run_state !== "active") throw new Error(`health is not live: ${health.mode}/${health.run_state}`);
      if (!Number.isSafeInteger(health.collector_heartbeat_at_ms)) throw new Error("collector heartbeat missing");
      if (!Number.isSafeInteger(health.portal_checked_at_ms)) throw new Error("portal checked timestamp missing");
      if (health.research_preview !== true || health.trading_authorized !== false) throw new Error("safety contract mismatch");
      for (const source of ["bybit-linear", "binance-usdm"]) {
        const state = health.sources?.[source];
        if (!state?.configured || !state?.connected) throw new Error(`${source} is not connected`);
        if (!Number.isSafeInteger(state.subscription_symbol_count) || state.subscription_symbol_count < 1) throw new Error(`${source} subscriptions missing`);
        if (!Number.isSafeInteger(state.last_heartbeat_at_ms)) throw new Error(`${source} heartbeat missing`);
        if (!Number.isSafeInteger(state.events) || state.events < 0) throw new Error(`${source} event count missing`);
      }
      if (list.mode !== "live" || !Array.isArray(list.events)) throw new Error("list is not live");
      if (summary.mode !== "live" || !Array.isArray(summary.windows)) throw new Error("summary is not live");
      const labelsPresent = containsLabels("/app/.next/static");
      if (!labelsPresent) throw new Error("truthful timestamp labels missing from production bundle");
      process.stdout.write(JSON.stringify({
        observed_at_ms: Date.now(),
        health,
        event_ids: list.events.map((event) => `${event.source}:${event.source_event_id}`),
        event_count: list.events.length,
        source_event_count: health.sources["bybit-linear"].events + health.sources["binance-usdm"].events,
        summary_anchor_at_ms: summary.anchor_at_ms,
        page_status: page.status,
        labels_present: labelsPresent,
        cache_control: {
          health: healthResult.cache_control,
          list: listResult.cache_control,
          summary: summaryResult.cache_control,
        },
      }));
    }).catch((error) => { console.error(error); process.exit(1); });
  '
}

proof_stage="candidate_first_authenticated_observation"
probe > "$work_dir/first.json"
sleep "$observation_delay"
proof_stage="candidate_second_authenticated_observation"
probe > "$work_dir/second.json"

proof_stage="evidence_report_generation"
PRODUCTION_BOUNDARY_PATH="$production_boundary" \
FIRST_PATH="$work_dir/first.json" \
SECOND_PATH="$work_dir/second.json" \
REPORT_PATH="$report_path" \
PORTAL_IMAGE="$portal_image" \
PORTAL_IMAGE_ID="$portal_image_id" \
PORTAL_CONTAINER="$portal_container" \
PORTAL_UID="$portal_uid" \
PORTAL_GROUPS="$portal_groups" \
DATA_GID="$data_gid" \
PIDS_LIMIT_SUPPORTED="$pids_limit_supported" \
CANDIDATE_PIDS_LIMIT_JSON="$candidate_pids_limit_json" \
CANDIDATE_IMAGE="$candidate_image" \
CANDIDATE_IMAGE_ID="$candidate_image_id" \
CANDIDATE_UID="$candidate_uid" \
CANDIDATE_GROUPS="$candidate_groups" \
CANDIDATE_RESTART="$candidate_restart" \
CANDIDATE_READONLY_ROOTFS="$candidate_readonly_rootfs" \
CANDIDATE_CAP_DROP_JSON="$candidate_cap_drop_json" \
CANDIDATE_SECURITY_OPT_JSON="$candidate_security_opt_json" \
CANDIDATE_TMPFS_JSON="$candidate_tmpfs_json" \
CANDIDATE_MEMORY_LIMIT="$candidate_memory_limit" \
MOUNT_SOURCE="$mount_source" \
CANDIDATE="$candidate" \
GITHUB_SHA_VALUE="${GITHUB_SHA:-unknown}" \
python3 - <<'PY'
import json
import os
from pathlib import Path

production = json.loads(Path(os.environ["PRODUCTION_BOUNDARY_PATH"]).read_text(encoding="utf-8"))
first = json.loads(Path(os.environ["FIRST_PATH"]).read_text(encoding="utf-8"))
second = json.loads(Path(os.environ["SECOND_PATH"]).read_text(encoding="utf-8"))

first_health = first["health"]
second_health = second["health"]
if second_health["run_id"] != first_health["run_id"]:
    raise SystemExit("live run rotated during the bounded observation")
if second_health["collector_heartbeat_at_ms"] <= first_health["collector_heartbeat_at_ms"]:
    raise SystemExit("collector heartbeat did not advance")
if second_health["portal_checked_at_ms"] <= first_health["portal_checked_at_ms"]:
    raise SystemExit("portal read timestamp did not advance")
for source in ("bybit-linear", "binance-usdm"):
    first_source = first_health["sources"][source]
    second_source = second_health["sources"][source]
    if second_source["last_heartbeat_at_ms"] < first_source["last_heartbeat_at_ms"]:
        raise SystemExit(f"{source} heartbeat moved backwards")
    if second_source["events"] < first_source["events"]:
        raise SystemExit(f"{source} event count moved backwards")

first_ids = set(first["event_ids"])
second_ids = set(second["event_ids"])
new_event_ids = sorted(second_ids - first_ids)
last_event_advanced = (
    second_health.get("last_event_at_ms") is not None
    and first_health.get("last_event_at_ms") is not None
    and second_health["last_event_at_ms"] > first_health["last_event_at_ms"]
)
real_event_present = bool(
    first["source_event_count"] > 0
    or second["source_event_count"] > 0
    or first_ids
    or second_ids
)
event_count_advanced = second["source_event_count"] > first["source_event_count"]
real_event_observed = bool(new_event_ids or last_event_advanced or event_count_advanced)

cap_drop = json.loads(os.environ["CANDIDATE_CAP_DROP_JSON"])
security_opt = json.loads(os.environ["CANDIDATE_SECURITY_OPT_JSON"])
tmpfs = json.loads(os.environ["CANDIDATE_TMPFS_JSON"])
if cap_drop != ["ALL"]:
    raise SystemExit("candidate capability drop evidence mismatch")
if "no-new-privileges:true" not in security_opt:
    raise SystemExit("candidate no-new-privileges evidence mismatch")
if set(tmpfs) != {"/tmp", "/app/.next/cache"}:
    raise SystemExit("candidate tmpfs evidence mismatch")

report = {
    "schema_version": 1,
    "report_type": "liquidations_live_portal_synology_proof",
    "commit_sha": os.environ["GITHUB_SHA_VALUE"],
    "result": "success",
    "rejection_reason": None,
    "production_portal": {
        "container": os.environ["PORTAL_CONTAINER"],
        "image": os.environ["PORTAL_IMAGE"],
        "image_id": os.environ["PORTAL_IMAGE_ID"],
        "uid": int(os.environ["PORTAL_UID"]),
        "groups": [int(value) for value in os.environ["PORTAL_GROUPS"].split()],
        "data_gid": int(os.environ["DATA_GID"]),
        "mount_source": os.environ["MOUNT_SOURCE"],
        "mount_read_only": True,
        "docker_socket_mounted": False,
        "restart_policy": "unless-stopped",
        "unauthenticated_boundary": production,
    },
    "isolated_candidate": {
        "container": os.environ["CANDIDATE"],
        "image": os.environ["CANDIDATE_IMAGE"],
        "image_id": os.environ["CANDIDATE_IMAGE_ID"],
        "uid": int(os.environ["CANDIDATE_UID"]),
        "groups": [int(value) for value in os.environ["CANDIDATE_GROUPS"].split()],
        "restart_policy": os.environ["CANDIDATE_RESTART"],
        "fixture_identity": True,
        "fixture_session_validated": True,
        "unauthenticated_api_rejected": True,
        "read_only_root_filesystem": os.environ["CANDIDATE_READONLY_ROOTFS"] == "true",
        "tmpfs": tmpfs,
        "cap_drop": cap_drop,
        "no_new_privileges": "no-new-privileges:true" in security_opt,
        "memory_limit_bytes": int(os.environ["CANDIDATE_MEMORY_LIMIT"]),
        "real_data_mount_read_only": True,
        "docker_socket_mounted": False,
        "pids_limit_supported": os.environ["PIDS_LIMIT_SUPPORTED"] == "true",
        "pids_limit": json.loads(os.environ["CANDIDATE_PIDS_LIMIT_JSON"]),
        "first": first,
        "second": second,
    },
    "proof": {
        "collector_heartbeat_advanced": True,
        "portal_checked_at_advanced": True,
        "same_portal_process": True,
        "source_heartbeats_non_decreasing": True,
        "no_store_api": True,
        "truthful_timestamp_labels": True,
        "event_counts": {
            "list_first": first["event_count"],
            "list_second": second["event_count"],
            "source_total_first": first["source_event_count"],
            "source_total_second": second["source_event_count"],
        },
        "real_exchange_event_present": real_event_present,
        "event_count_advanced_during_observation": event_count_advanced,
        "real_exchange_event_observed": real_event_observed,
        "new_event_ids": new_event_ids,
        "quiet_window_note": None if real_event_observed else "No new exchange liquidation was observed during the bounded proof window; heartbeat, subscriptions and live API reads were proven without fabricating an event.",
        "research_preview": True,
        "trading_authorized": False,
    },
}
Path(os.environ["REPORT_PATH"]).write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

python3 - "$report_path" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
assert payload["result"] == "success"
assert payload["rejection_reason"] is None
assert payload["isolated_candidate"]["uid"] != 0
assert payload["isolated_candidate"]["read_only_root_filesystem"] is True
assert payload["isolated_candidate"]["cap_drop"] == ["ALL"]
assert payload["isolated_candidate"]["no_new_privileges"] is True
assert payload["proof"]["collector_heartbeat_advanced"] is True
assert payload["proof"]["portal_checked_at_advanced"] is True
assert payload["proof"]["trading_authorized"] is False
PY

proof_stage="completed"
printf 'Liquidations live portal proof passed: report=%s image=%s candidate=%s\n' \
  "$report_path" "$portal_image" "$candidate"
