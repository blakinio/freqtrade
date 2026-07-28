#!/bin/sh
set -eu

umask 077

: "${VAULT_ADDR:?set VAULT_ADDR}"
: "${VAULT_CACERT:?set VAULT_CACERT}"
: "${VAULT_OPERATOR_TOKEN_FILE:?set VAULT_OPERATOR_TOKEN_FILE}"
: "${VAULT_APPROLE_OUTPUT_DIRECTORY:?set VAULT_APPROLE_OUTPUT_DIRECTORY}"

if [ ! -f "$VAULT_CACERT" ]; then
  echo "Vault CA certificate is unavailable" >&2
  exit 1
fi
if [ ! -f "$VAULT_OPERATOR_TOKEN_FILE" ]; then
  echo "Vault operator token file is unavailable" >&2
  exit 1
fi
if [ ! -d "$VAULT_APPROLE_OUTPUT_DIRECTORY" ]; then
  echo "Vault AppRole output directory is unavailable" >&2
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

if ! vault status -format=json | grep -q '"sealed"[[:space:]]*:[[:space:]]*false'; then
  echo "Vault must be initialized and unsealed before bootstrap" >&2
  exit 1
fi

VAULT_TOKEN="$(cat "$VAULT_OPERATOR_TOKEN_FILE")"
export VAULT_TOKEN

if ! vault secrets list -format=json | grep -q '"portal-secrets/"'; then
  vault secrets enable -path=portal-secrets -version=2 kv >/dev/null
fi
vault write portal-secrets/config max_versions=10 cas_required=true delete_version_after=2160h >/dev/null

if ! vault auth list -format=json | grep -q '"approle/"'; then
  vault auth enable approle >/dev/null
fi

vault policy write portal-credential-broker /opt/portal-vault/broker-policy.hcl >/dev/null
vault write auth/approle/role/portal-credential-broker \
  token_policies=portal-credential-broker \
  token_ttl=10m \
  token_max_ttl=15m \
  token_num_uses=0 \
  secret_id_ttl=24h \
  secret_id_num_uses=0 >/dev/null

if ! vault audit list -format=json | grep -q '"audit-primary/"'; then
  vault audit enable -path=audit-primary file \
    file_path=/vault/audit-primary/audit.json mode=0600 >/dev/null
fi
if ! vault audit list -format=json | grep -q '"audit-secondary/"'; then
  vault audit enable -path=audit-secondary file \
    file_path=/vault/audit-secondary/audit.json mode=0600 >/dev/null
fi

role_tmp="$VAULT_APPROLE_OUTPUT_DIRECTORY/role-id.tmp"
secret_tmp="$VAULT_APPROLE_OUTPUT_DIRECTORY/secret-id.tmp"
vault read -field=role_id auth/approle/role/portal-credential-broker/role-id >"$role_tmp"
vault write -field=secret_id -f auth/approle/role/portal-credential-broker/secret-id >"$secret_tmp"
chmod 600 "$role_tmp" "$secret_tmp"
mv -f "$role_tmp" "$VAULT_APPROLE_OUTPUT_DIRECTORY/role-id"
mv -f "$secret_tmp" "$VAULT_APPROLE_OUTPUT_DIRECTORY/secret-id"

unset VAULT_TOKEN
printf '%s\n' "Vault PI-07 policy, AppRole, KV v2 and dual audit devices are configured."
