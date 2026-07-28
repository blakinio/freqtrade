#!/bin/sh
set -eu

umask 077

: "${VAULT_OPERATOR_TOKEN_FILE:?set VAULT_OPERATOR_TOKEN_FILE}"
: "${VAULT_APPROLE_OUTPUT_DIRECTORY:?set VAULT_APPROLE_OUTPUT_DIRECTORY}"

if [ ! -f "$VAULT_OPERATOR_TOKEN_FILE" ] || [ ! -d "$VAULT_APPROLE_OUTPUT_DIRECTORY" ]; then
  echo "Vault operator material is unavailable" >&2
  exit 1
fi

operator_mode="$(stat -c '%a' "$VAULT_OPERATOR_TOKEN_FILE")"
case "$operator_mode" in
  400|600) ;;
  *)
    echo "Vault operator token file must have mode 0400 or 0600" >&2
    exit 1
    ;;
esac

VAULT_TOKEN="$(cat "$VAULT_OPERATOR_TOKEN_FILE")"
export VAULT_TOKEN

secret_tmp="$VAULT_APPROLE_OUTPUT_DIRECTORY/secret-id.tmp"
vault write -field=secret_id -f auth/approle/role/portal-credential-broker/secret-id >"$secret_tmp"
chmod 600 "$secret_tmp"
mv -f "$secret_tmp" "$VAULT_APPROLE_OUTPUT_DIRECTORY/secret-id"

unset VAULT_TOKEN
printf '%s\n' "Vault AppRole SecretID rotated."
