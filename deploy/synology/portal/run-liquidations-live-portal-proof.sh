#!/usr/bin/env bash
set -Eeuo pipefail

source_script="${PORTAL_LIVE_PROOF_SOURCE_SCRIPT:-deploy/synology/portal/prove-liquidations-live.sh}"
report_path="${PORTAL_LIVE_PROOF_REPORT_PATH:?PORTAL_LIVE_PROOF_REPORT_PATH is required}"
patched_script="$(mktemp)"
cleanup() {
  rm -f "$patched_script"
}
trap cleanup EXIT

python3 - "$source_script" "$patched_script" <<'PY'
from pathlib import Path
import sys

source_path = Path(sys.argv[1])
target_path = Path(sys.argv[2])
text = source_path.read_text(encoding="utf-8")

old = '''for _ in $(seq 1 60); do
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
'''

new = '''candidate_ready=false
candidate_healthcheck_present="$(docker inspect --format '{{if .Config.Healthcheck}}true{{else}}false{{end}}' "$candidate")"
for _ in $(seq 1 60); do
  status="$(docker inspect --format '{{.State.Status}}' "$candidate" 2>/dev/null || true)"
  if [[ "$status" == "exited" || "$status" == "dead" ]]; then
    docker logs --tail 120 "$candidate" >&2 || true
    exit 1
  fi
  if [[ "$status" == "running" ]] && docker exec "$candidate" node -e '\''
    fetch("http://127.0.0.1:3000/login", {cache:"no-store"})
      .then((response) => process.exit(response.status === 200 ? 0 : 1))
      .catch(() => process.exit(1));
  '\'' >/dev/null 2>&1; then
    candidate_ready=true
    break
  fi
  sleep 2
done
if [[ "$candidate_ready" != "true" ]]; then
  docker logs --tail 120 "$candidate" >&2 || true
  echo "Candidate did not pass explicit HTTP readiness probe" >&2
  exit 1
fi
echo "Candidate readiness passed via HTTP /login; image_healthcheck_present=${candidate_healthcheck_present}"
'''

if text.count(old) != 1:
    raise SystemExit("expected exactly one legacy Docker health wait block")
text = text.replace(old, new)

needle = "set -Eeuo pipefail\n"
diagnostic = '''set -Eeuo pipefail

proof_error() {
  local status="$?"
  printf 'Liquidations proof command failed: line=%s status=%s command=%s\\n' \
    "$1" "$status" "$2" >&2
  return "$status"
}
trap 'proof_error "$LINENO" "$BASH_COMMAND"' ERR
'''
if text.count(needle) != 1:
    raise SystemExit("expected exactly one strict-mode header")
text = text.replace(needle, diagnostic, 1)
target_path.write_text(text, encoding="utf-8")
PY
chmod 0700 "$patched_script"

set +e
bash "$patched_script"
status=$?
set -e

if [[ "$status" -ne 0 && ! -s "$report_path" ]]; then
  PROOF_EXIT_CODE="$status" \
  REPORT_PATH="$report_path" \
  GITHUB_SHA_VALUE="${GITHUB_SHA:-unknown}" \
  python3 - <<'PY'
import json
import os
from pathlib import Path

report = {
    "schema_version": 1,
    "report_type": "liquidations_live_portal_synology_proof",
    "result": "failure",
    "commit_sha": os.environ["GITHUB_SHA_VALUE"],
    "failure": {
        "exit_code": int(os.environ["PROOF_EXIT_CODE"]),
        "evidence": "See the paired workflow log for the exact ERR trap line and command.",
    },
    "proof": {
        "completed": False,
        "research_preview": True,
        "trading_authorized": False,
    },
}
Path(os.environ["REPORT_PATH"]).write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
PY
fi

exit "$status"
