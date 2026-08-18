# Dedicated Linux runtime contract

Status: target contract introduced by ADR-024.  
Owning architecture issue: #1603.  
Physical migration programme: #1604.

This directory defines the portable runtime-host boundary for persistent Developer Quant services. It deliberately contains no Synology DSM path, Synology runner identity, production-trading authority or target-host secret.

## Topology

```text
GitHub / Actions
  CI + build + immutable artifact publication
                |
                v
Dedicated Linux runtime
  Portal / collectors / WickHunter / simulation workers
                |
                v
Synology durable storage / evidence / backup
```

GitHub Actions orchestrates delivery; it is not the long-lived application runtime. Synology stores durable material; it is not the target application-compute host.

## Host contract

A target host must satisfy the repository-neutral contract in `runtime-host.env.example` before service-specific deployment is attempted.

Required principles:

- Linux host dedicated to Developer Quant runtime workloads;
- Docker or Podman-compatible container execution as selected by the service package;
- local runtime/transactional state rooted outside the durable storage mount;
- durable storage mounted or synchronized at a separate absolute path;
- application containers receive no container-engine socket;
- optional GitHub self-hosted runner is `deploy-only` or absent;
- service images/artifacts are identified by immutable digest or exact attributable revision;
- no real-money trading credentials or execution capability;
- no Synology-specific `/volume1/...` path assumptions on the compute host.

Validate the static contract with:

```bash
python deploy/runtime/validate_host_contract.py \
  --env-file deploy/runtime/runtime-host.env.example
```

A physical host can additionally be checked with `--check-filesystem` after the actual roots are configured. That check is deployment evidence and must not be claimed from the example file.

## State classes

Do not make every persistent file a network-storage bind mount.

### Runtime-local state

`RUNTIME_STATE_ROOT` is for state that requires local filesystem/database semantics, for example:

- active PostgreSQL/MariaDB/SQLite database storage when that engine is explicitly supported;
- service-local queues/caches that have an application-defined recovery path;
- container runtime metadata that is not itself the durable research system of record.

Transactional databases must not be placed on Synology NFS/SMB merely to centralize storage. Back up or replicate them through the database/application recovery contract.

### Durable storage

`DURABLE_STORAGE_ROOT` is the narrow Synology-backed or otherwise approved durable boundary for material such as:

- chronological datasets and outcome evidence;
- model packages and reproducibility artifacts;
- long-lived reports/evidence promoted beyond Actions retention;
- database backups and restore manifests;
- service-specific append-only or immutable evidence roots that are proven safe on the selected filesystem.

Service packages must declare whether each durable root is read-only or read/write. Do not grant the whole storage tree to every container.

## Target service order

The default migration order is intentionally low-risk first:

1. public market-data collectors;
2. WickHunter/inference and research workers;
3. Portal/control-plane services and explicitly migrated transactional state;
4. Freqtrade simulation workers;
5. remaining supporting services.

Existing `deploy/synology/**` packages are transitional current-state implementations until a service-specific portable package is proven. Do not delete them simply because ADR-024 is accepted.

## Deployment runner

The target self-hosted runner contract is narrow:

```text
runner_scope = disabled | deploy-only
```

If enabled, it may perform bounded delivery operations such as immutable image pull, configuration validation, service update, health verification and rollback. It must not become the normal location for repository-wide CI, dependency builds, unrestricted shell jobs or model training.

Application containers must not mount the Docker/Podman socket. A deployment runner that requires container-engine access is a separate privileged boundary and must be scoped accordingly.

## Cutover gate

No service is considered migrated until current target evidence proves:

- exact host identity/architecture;
- exact artifact/image revision or digest;
- required local and durable storage roots;
- pre-cutover health of the old service;
- new-host startup and health;
- restart persistence appropriate to the service;
- bounded rollback;
- no silent data/evidence loss.

The example contract is not proof that such a host exists.
