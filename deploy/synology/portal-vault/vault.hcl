ui = false

disable_mlock = true
default_lease_ttl = "10m"
max_lease_ttl = "15m"
api_addr = "https://vault:8200"
cluster_addr = "https://vault:8201"

storage "raft" {
  path = "/vault/data"
  node_id = "portal-vault-synology-1"
}

listener "tcp" {
  address = "0.0.0.0:8200"
  cluster_address = "0.0.0.0:8201"
  tls_cert_file = "/vault/tls/vault.crt"
  tls_key_file = "/vault/tls/vault.key"
  tls_client_ca_file = "/vault/tls/ca.crt"
  tls_min_version = "tls13"
  tls_max_version = "tls13"
  redact_addresses = "true"
  redact_cluster_name = "true"
  redact_version = "true"
}

telemetry {
  disable_hostname = true
  unauthenticated_metrics_access = false
}
