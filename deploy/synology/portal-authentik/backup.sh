#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE=${ENV_FILE:-$ROOT/.env}
BACKUP_DIR=${BACKUP_DIR:-$ROOT/backups}
: "${AGE_RECIPIENT:?set AGE_RECIPIENT to the offline backup recipient}"
: "${BACKUP_CONFIRM:?set BACKUP_CONFIRM=BACKUP_AUTHENTIK_DATABASE_AND_VOLUMES}"
[ "$BACKUP_CONFIRM" = "BACKUP_AUTHENTIK_DATABASE_AND_VOLUMES" ] || {
  echo "backup confirmation phrase mismatch" >&2
  exit 2
}
[ -f "$ENV_FILE" ] || { echo "runtime env file not found: $ENV_FILE" >&2; exit 2; }
command -v age >/dev/null 2>&1 || { echo "age is required" >&2; exit 2; }
command -v docker >/dev/null 2>&1 || { echo "docker is required" >&2; exit 2; }

python3 "$ROOT/validate.py" --env-file "$ENV_FILE" >/dev/null
set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a
umask 077
mkdir -p "$BACKUP_DIR"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
base="$BACKUP_DIR/authentik-$stamp"
compose="docker compose --env-file $ENV_FILE -f $ROOT/compose.yml"

restart_services() {
  $compose up -d server worker >/dev/null 2>&1 || true
}
trap restart_services EXIT INT TERM
$compose stop server worker
$compose up -d postgresql

$compose exec -T postgresql pg_dump \
  --format=custom --no-owner --no-acl \
  -U "$AUTHENTIK_POSTGRESQL__USER" "$AUTHENTIK_POSTGRESQL__NAME" \
  | age -r "$AGE_RECIPIENT" -o "$base.dump.age"

$compose run --rm -T --no-deps server tar -C / -cf - media templates \
  | age -r "$AGE_RECIPIENT" -o "$base.volumes.tar.age"

test -s "$base.dump.age"
test -s "$base.volumes.tar.age"
sha256sum "$base.dump.age" "$base.volumes.tar.age" > "$base.sha256"
chmod 600 "$base.dump.age" "$base.volumes.tar.age" "$base.sha256"
restart_services
trap - EXIT INT TERM
printf '%s\n' "$base"
