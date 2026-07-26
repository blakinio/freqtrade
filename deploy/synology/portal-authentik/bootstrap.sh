#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE=${ENV_FILE:-$ROOT/.env}
BOOTSTRAP_ENV_FILE=${BOOTSTRAP_ENV_FILE:-$ROOT/bootstrap.env}
: "${BOOTSTRAP_CONFIRM:?set BOOTSTRAP_CONFIRM=INITIALIZE_EMPTY_AUTHENTIK_DATABASE}"
[ "$BOOTSTRAP_CONFIRM" = "INITIALIZE_EMPTY_AUTHENTIK_DATABASE" ] || {
  echo "bootstrap confirmation phrase mismatch" >&2
  exit 2
}
[ -f "$ENV_FILE" ] || { echo "runtime env file not found: $ENV_FILE" >&2; exit 2; }
[ -f "$BOOTSTRAP_ENV_FILE" ] || { echo "one-shot bootstrap env not found" >&2; exit 2; }
chmod 600 "$BOOTSTRAP_ENV_FILE"
bootstrap_hash=$(sed -n 's/^AUTHENTIK_BOOTSTRAP_PASSWORD_HASH=//p' "$BOOTSTRAP_ENV_FILE")
[ -n "$bootstrap_hash" ] || { echo "bootstrap hash is empty" >&2; exit 2; }
case "$bootstrap_hash" in
  *\$*) ;;
  *) echo "bootstrap value must be a Django password hash, not plaintext" >&2; exit 2 ;;
esac

python3 "$ROOT/validate.py" --env-file "$ENV_FILE" >/dev/null
set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a
compose="docker compose --env-file $ENV_FILE -f $ROOT/compose.yml"
$compose up -d postgresql

table_count=$($compose exec -T postgresql psql -At \
  -U "$AUTHENTIK_POSTGRESQL__USER" -d "$AUTHENTIK_POSTGRESQL__NAME" \
  -c "select count(*) from pg_tables where schemaname = 'public';")
[ "$table_count" = "0" ] || {
  echo "bootstrap refused: the public schema already contains tables" >&2
  exit 3
}

docker compose --env-file "$ENV_FILE" --env-file "$BOOTSTRAP_ENV_FILE" \
  -f "$ROOT/compose.yml" up -d server worker

tries=0
until $compose exec -T server ak healthcheck >/dev/null 2>&1; do
  tries=$((tries + 1))
  [ "$tries" -lt 60 ] || { echo "server did not become healthy" >&2; exit 4; }
  sleep 5
done

# Recreate without the one-shot hash so it is absent from steady-state container env.
$compose up -d --force-recreate server worker
if command -v shred >/dev/null 2>&1; then
  shred -u "$BOOTSTRAP_ENV_FILE"
else
  rm -f "$BOOTSTRAP_ENV_FILE"
fi
printf '%s\n' "bootstrap completed; configure the OIDC provider through the restricted admin path"
