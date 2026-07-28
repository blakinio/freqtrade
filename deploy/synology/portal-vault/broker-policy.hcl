# The PI-07 broker can read only tenant-scoped exchange/runtime credentials.
# It cannot create, update, delete, undelete, destroy, list or manage mounts.
path "portal-secrets/data/tenants/+/exchange-connections/+" {
  capabilities = ["read"]
}

path "portal-secrets/metadata/tenants/+/exchange-connections/+" {
  capabilities = ["read"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}
