#!/usr/bin/env bash
set -Eeuo pipefail

portal_container="${PORTAL_CONTAINER_NAME:-freqtrade-portal-staging}"
liquidations_host_root="${PORTAL_LIQUIDATIONS_HOST_ROOT:-/volume1/docker/freqtrade-liquidations/data}"
report_path="${PORTAL_LIVE_PROOF_REPORT_PATH:?PORTAL_LIVE_PROOF_REPORT_PATH is required}"
probe_timeout_seconds="${PORTAL_OPERATIONAL_PROBE_TIMEOUT_SECONDS:-15}"
probe_stage="input_validation"

mkdir -p "$(dirname "$report_path")"
rm -f "$report_path"
work_dir="$(mktemp -d)"

write_failure_report() {
  local exit_status="$1"
  PROBE_EXIT_STATUS="$exit_status" \
  PROBE_FAILURE_STAGE="$probe_stage" \
  GITHUB_SHA_VALUE="${GITHUB_SHA:-unknown}" \
  REPORT_PATH="$report_path" \
  python3 - <<'PY' || true
import json
import os
from pathlib import Path

stage = os.environ["PROBE_FAILURE_STAGE"]
report = {
    "schema_version": 1,
    "report_type": "liquidations_live_portal_operational_probe",
    "commit_sha": os.environ["GITHUB_SHA_VALUE"],
    "result": "failure",
    "rejection_reason": f"operational probe failed during {stage}",
    "exit_status": int(os.environ["PROBE_EXIT_STATUS"]),
}
Path(os.environ["REPORT_PATH"]).write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
}

cleanup() {
  local status=$?
  trap - EXIT
  if (( status != 0 )) && [[ ! -s "$report_path" ]]; then
    write_failure_report "$status"
  fi
  rm -rf "$work_dir"
  exit "$status"
}
trap cleanup EXIT

case "$probe_timeout_seconds" in
  *[!0-9]* | "")
    echo "PORTAL_OPERATIONAL_PROBE_TIMEOUT_SECONDS must be a positive integer" >&2
    exit 64
    ;;
esac
if (( probe_timeout_seconds < 5 || probe_timeout_seconds > 60 )); then
  echo "PORTAL_OPERATIONAL_PROBE_TIMEOUT_SECONDS must be between 5 and 60" >&2
  exit 64
fi
command -v timeout >/dev/null

docker_bounded() {
  timeout 10s docker "$@"
}

probe_stage="production_container_preflight"
docker_bounded version >/dev/null
test -S /var/run/docker.sock
test "$(docker_bounded inspect --format '{{.State.Running}}' "$portal_container")" = "true"

portal_image="$(docker_bounded inspect --format '{{.Config.Image}}' "$portal_container")"
portal_image_id="$(docker_bounded inspect --format '{{.Image}}' "$portal_container")"
portal_health="$(docker_bounded inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$portal_container")"
mount_source="$(docker_bounded inspect --format '{{range .Mounts}}{{if eq .Destination "/liquid20-data"}}{{.Source}}{{end}}{{end}}' "$portal_container")"
mount_rw="$(docker_bounded inspect --format '{{range .Mounts}}{{if eq .Destination "/liquid20-data"}}{{.RW}}{{end}}{{end}}' "$portal_container")"
docker_socket_mount="$(docker_bounded inspect --format '{{range .Mounts}}{{if eq .Destination "/var/run/docker.sock"}}{{.Source}}{{end}}{{end}}' "$portal_container")"
portal_restart="$(docker_bounded inspect --format '{{.HostConfig.RestartPolicy.Name}}' "$portal_container")"
portal_uid="$(docker_bounded exec "$portal_container" id -u)"
portal_groups="$(docker_bounded exec "$portal_container" id -G)"

test -n "$portal_image"
test -n "$portal_image_id"
test "$mount_source" = "$liquidations_host_root"
test "$mount_rw" = "false"
test -z "$docker_socket_mount"
test "$portal_uid" != "0"
test "$portal_restart" = "always"

probe_stage="production_authentication_boundary"
production_boundary="$work_dir/production-boundary.json"
timeout "$((probe_timeout_seconds + 10))s" docker exec \
  --env "PORTAL_PROBE_TIMEOUT_MS=$((probe_timeout_seconds * 1000))" \
  "$portal_container" node -e '
  const timeoutMs = Number(process.env.PORTAL_PROBE_TIMEOUT_MS || "15000");
  const request = (url) => fetch(url, {
    cache: "no-store",
    signal: AbortSignal.timeout(timeoutMs),
  });
  Promise.all([
    request("http://127.0.0.1:3000/market/liquidations"),
    request("http://127.0.0.1:3000/api/market/liquidations/health"),
  ]).then(async ([page, health]) => {
    const payload = await health.json().catch(() => ({}));
    const result = {
      page_status: page.status,
      health_status: health.status,
      health_code: payload.code ?? null,
      health_cache_control: health.headers.get("cache-control"),
    };
    if (page.status !== 200) throw new Error(`page status ${page.status}`);
    if (health.status !== 401 || payload.code !== "SESSION_MISSING") {
      throw new Error(`protected health boundary ${health.status}/${payload.code ?? "missing"}`);
    }
    if (!(result.health_cache_control || "").includes("no-store")) {
      throw new Error("protected health response is not no-store");
    }
    process.stdout.write(JSON.stringify(result));
  }).catch((error) => { console.error(error); process.exit(1); });
' > "$production_boundary"

probe_stage="evidence_report_generation"
PRODUCTION_BOUNDARY_PATH="$production_boundary" \
REPORT_PATH="$report_path" \
PORTAL_CONTAINER="$portal_container" \
PORTAL_IMAGE="$portal_image" \
PORTAL_IMAGE_ID="$portal_image_id" \
PORTAL_HEALTH="$portal_health" \
PORTAL_RESTART="$portal_restart" \
PORTAL_UID="$portal_uid" \
PORTAL_GROUPS="$portal_groups" \
MOUNT_SOURCE="$mount_source" \
GITHUB_SHA_VALUE="${GITHUB_SHA:-unknown}" \
python3 - <<'PY'
import json
import os
from pathlib import Path

boundary = json.loads(
    Path(os.environ["PRODUCTION_BOUNDARY_PATH"]).read_text(encoding="utf-8")
)
report = {
    "schema_version": 1,
    "report_type": "liquidations_live_portal_operational_probe",
    "commit_sha": os.environ["GITHUB_SHA_VALUE"],
    "result": "success",
    "rejection_reason": None,
    "production_portal": {
        "container": os.environ["PORTAL_CONTAINER"],
        "image": os.environ["PORTAL_IMAGE"],
        "image_id": os.environ["PORTAL_IMAGE_ID"],
        "running": True,
        "health_status": os.environ["PORTAL_HEALTH"],
        "restart_policy": os.environ["PORTAL_RESTART"],
        "uid": int(os.environ["PORTAL_UID"]),
        "groups": [int(value) for value in os.environ["PORTAL_GROUPS"].split()],
        "mount_source": os.environ["MOUNT_SOURCE"],
        "real_data_mount_read_only": True,
        "docker_socket_mounted": False,
        "unauthenticated_boundary": boundary,
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
assert payload["production_portal"]["running"] is True
assert payload["production_portal"]["restart_policy"] == "always"
assert payload["production_portal"]["uid"] != 0
assert payload["production_portal"]["real_data_mount_read_only"] is True
assert payload["production_portal"]["docker_socket_mounted"] is False
assert payload["production_portal"]["unauthenticated_boundary"]["page_status"] == 200
assert payload["production_portal"]["unauthenticated_boundary"]["health_status"] == 401
assert payload["production_portal"]["unauthenticated_boundary"]["health_code"] == "SESSION_MISSING"
PY

probe_stage="completed"
printf 'Liquidations portal operational probe passed: report=%s container=%s image=%s\n' \
  "$report_path" "$portal_container" "$portal_image"
