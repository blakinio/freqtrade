#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE=${ENV_FILE:?set ENV_FILE to an emulated runtime env file}
REPORT_FILE=${REPORT_FILE:-$ROOT/pi06-emulated-acceptance.json}
PI06_EMULATED_RESOURCE_PREFIX=${PI06_EMULATED_RESOURCE_PREFIX:-pi06_emulated_$$}
export PI06_EMULATED_RESOURCE_PREFIX

case "$PI06_EMULATED_RESOURCE_PREFIX" in
  *[!a-zA-Z0-9_-]* | "")
    echo "PI06_EMULATED_RESOURCE_PREFIX must contain only letters, digits, underscore or dash" >&2
    exit 2
    ;;
esac

[ -f "$ENV_FILE" ] || {
  echo "emulated runtime env file not found: $ENV_FILE" >&2
  exit 2
}

python3 "$ROOT/validate.py" --env-file "$ENV_FILE" >/dev/null

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

: "${AUTHENTIK_HTTP_PORT:?set AUTHENTIK_HTTP_PORT in the emulated env file}"
[ "$AUTHENTIK_BIND_ADDRESS" = "127.0.0.1" ] || {
  echo "emulation refuses non-loopback Authentik ingress" >&2
  exit 2
}
[ "$AUTHENTIK_HTTP_PORT" != "9000" ] || {
  echo "emulation refuses the default target port; use a dedicated high port" >&2
  exit 2
}

compose() {
  docker compose \
    --env-file "$ENV_FILE" \
    -f "$ROOT/compose.yml" \
    -f "$ROOT/compose.emulated.yml" \
    "$@"
}

cleanup() {
  compose down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

compose config --quiet
compose up -d --pull always postgresql server worker

wait_healthy() {
  service=$1
  tries=0
  while :; do
    container_id=$(compose ps -q "$service")
    [ -n "$container_id" ] || {
      echo "$service container was not created" >&2
      exit 3
    }
    health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id")
    [ "$health" = "healthy" ] && return 0
    [ "$health" = "unhealthy" ] && {
      compose logs --no-color "$service" >&2 || true
      echo "$service became unhealthy" >&2
      exit 3
    }
    tries=$((tries + 1))
    [ "$tries" -lt 90 ] || {
      compose logs --no-color "$service" >&2 || true
      echo "$service did not become healthy" >&2
      exit 3
    }
    sleep 5
  done
}

wait_healthy postgresql
wait_healthy server
wait_healthy worker

compose exec -T server ak healthcheck >/dev/null
compose exec -T worker ak healthcheck >/dev/null

server_id=$(compose ps -q server)
worker_id=$(compose ps -q worker)
postgres_id=$(compose ps -q postgresql)

published=$(docker port "$server_id" 9000/tcp)
[ "$published" = "127.0.0.1:$AUTHENTIK_HTTP_PORT" ] || {
  echo "unexpected Authentik port binding: $published" >&2
  exit 4
}
[ -z "$(docker port "$postgres_id" 5432/tcp)" ] || {
  echo "PostgreSQL must not publish a host port" >&2
  exit 4
}

data_internal=$(docker network inspect "${PI06_EMULATED_RESOURCE_PREFIX}_data" --format '{{.Internal}}')
[ "$data_internal" = "true" ] || {
  echo "identity data network is not internal" >&2
  exit 4
}

for container_id in "$server_id" "$worker_id" "$postgres_id"; do
  [ "$(docker inspect --format '{{.HostConfig.Privileged}}' "$container_id")" = "false" ] || {
    echo "privileged container detected" >&2
    exit 4
  }
  [ "$(docker inspect --format '{{.HostConfig.NetworkMode}}' "$container_id")" != "host" ] || {
    echo "host networking detected" >&2
    exit 4
  }
  if docker inspect --format '{{range .Mounts}}{{println .Source}}{{end}}' "$container_id" |
    grep -Fxq "/var/run/docker.sock"; then
    echo "Docker socket mount detected" >&2
    exit 4
  fi
done

if docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$server_id" |
  grep -E '^AUTHENTIK_BOOTSTRAP_PASSWORD_HASH=.+$' >/dev/null; then
  echo "steady-state server contains bootstrap material" >&2
  exit 4
fi

compose exec -T server sh -ec 'printf "%s\n" "pi06-emulated-persistence" > /media/.pi06-emulated-acceptance'
compose restart server >/dev/null
wait_healthy server
compose exec -T server grep -Fxq "pi06-emulated-persistence" /media/.pi06-emulated-acceptance

http_code=$(
  curl --silent --show-error --output /dev/null \
    --write-out '%{http_code}' \
    "http://127.0.0.1:$AUTHENTIK_HTTP_PORT/"
)
case "$http_code" in
  200 | 301 | 302 | 303 | 307 | 308) ;;
  *)
    echo "unexpected Authentik HTTP status: $http_code" >&2
    exit 4
    ;;
esac

mkdir -p "$(dirname -- "$REPORT_FILE")"
python3 - "$REPORT_FILE" "$PI06_EMULATED_RESOURCE_PREFIX" "$AUTHENTIK_HTTP_PORT" "$http_code" <<'PY'
import json
import os
import sys
from datetime import UTC, datetime

report_file, prefix, port, http_code = sys.argv[1:]
report = {
    "schema_version": 1,
    "claim": "emulated_non_production_acceptance_only",
    "generated_at": datetime.now(UTC).isoformat(),
    "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
    "commit": os.environ.get("GITHUB_SHA", "local"),
    "resource_prefix": prefix,
    "authentik_loopback_port": int(port),
    "checks": {
        "compose_rendered": "pass",
        "postgresql_healthy": "pass",
        "authentik_server_healthy": "pass",
        "authentik_worker_healthy": "pass",
        "loopback_only_ingress": "pass",
        "postgresql_not_published": "pass",
        "internal_data_network": "pass",
        "no_privileged_host_network_or_docker_socket": "pass",
        "bootstrap_material_absent": "pass",
        "volume_persistence_after_restart": "pass",
        "http_reachable": {"result": "pass", "status": int(http_code)},
    },
    "manual_owner_evidence": {
        "totp_enrollment_google_authenticator": "required",
        "totp_challenge_after_new_login": "required",
        "recovery_and_restore": "required",
    },
    "forbidden_claims": [
        "real_synology_target_accepted",
        "real_mfa_accepted",
        "real_oidc_portal_callback_accepted",
        "real_restore_accepted",
        "p11_accepted",
        "live_capital_authorized",
    ],
}
with open(report_file, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

trap - EXIT INT TERM
cleanup
printf '%s\n' "$REPORT_FILE"
