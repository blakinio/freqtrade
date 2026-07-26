#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE=${ENV_FILE:-$ROOT/.env}
: "${BACKUP_BASE:?set BACKUP_BASE to the path without .dump.age suffix}"
: "${RESTORE_CONFIRM:?set RESTORE_CONFIRM=RESTORE_AUTHENTIK_DATABASE_AND_VOLUMES}"
[ "$RESTORE_CONFIRM" = "RESTORE_AUTHENTIK_DATABASE_AND_VOLUMES" ] || {
  echo "restore confirmation phrase mismatch" >&2
  exit 2
}
[ -f "$ENV_FILE" ] || { echo "runtime env file not found: $ENV_FILE" >&2; exit 2; }
command -v age >/dev/null 2>&1 || { echo "age is required" >&2; exit 2; }
command -v docker >/dev/null 2>&1 || { echo "docker is required" >&2; exit 2; }
for suffix in dump.age volumes.tar.age sha256; do
  [ -f "$BACKUP_BASE.$suffix" ] || { echo "missing $BACKUP_BASE.$suffix" >&2; exit 2; }
done

python3 "$ROOT/validate.py" --env-file "$ENV_FILE" >/dev/null
(
  cd "$(dirname "$BACKUP_BASE")"
  sha256sum -c "$(basename "$BACKUP_BASE").sha256"
)
set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a
compose="docker compose --env-file $ENV_FILE -f $ROOT/compose.yml"

$compose stop server worker
$compose up -d postgresql

age --decrypt "$BACKUP_BASE.dump.age" \
  | $compose exec -T postgresql pg_restore \
      --clean --if-exists --no-owner --no-acl \
      -U "$AUTHENTIK_POSTGRESQL__USER" -d "$AUTHENTIK_POSTGRESQL__NAME"

age --decrypt "$BACKUP_BASE.volumes.tar.age" \
  | $compose run --rm -T --no-deps server tar -C / -xf -

$compose up -d server worker
$compose exec -T server ak healthcheck
$compose exec -T worker ak healthcheck
