# Synology Liquid20 Collector

This project runs the data-only `liquid20-v1` Bybit and Binance liquidation collector in Synology Container Manager. It exposes no ports, uses no exchange credentials, writes all evidence to a bind-mounted directory, and exits after the declared smoke or acceptance duration.

## Safety model

- public Bybit and Binance market-data endpoints only;
- no API keys, Freqtrade trading credentials, strategy, orders, DCA, leverage, protected holdout, or live capital;
- read-only container root filesystem;
- all Linux capabilities dropped and `no-new-privileges` enabled;
- no automatic restart, because an interrupted acceptance attempt must remain failed evidence instead of silently continuing as if it were one uninterrupted run;
- every start creates a new UTC `RUN_ID` unless one is explicitly supplied;
- the container refuses an existing run directory and recognized trading credential variables.

The container finishing and changing to a stopped state is expected. Exit code `0` means the selected smoke or acceptance command completed. It is not intended to be a permanently running service after the declared period.

## Directory layout

Recommended NAS location:

```text
/volume1/docker/freqtrade-liquidations/repo/
  deploy/synology/liquid20/
    compose.yaml
    .env
    data/
      runs/
```

The repository root is the Docker build context. Keep `compose.yaml`, `.env`, and `data/` together in `deploy/synology/liquid20/`.

## 1. Prepare the project through SSH

Clone or update the repository on the NAS:

```bash
sudo -i
mkdir -p /volume1/docker/freqtrade-liquidations
cd /volume1/docker/freqtrade-liquidations

git clone --branch develop https://github.com/blakinio/freqtrade.git repo
cd repo

git pull --ff-only origin develop
COMMIT="$(git rev-parse HEAD)"
printf '%s\n' "$COMMIT"
```

Create the local environment file and persistent data directory:

```bash
cd deploy/synology/liquid20
cp .env.example .env
mkdir -p data/runs
```

Determine the numeric UID and GID of the DSM account that should own the artifacts:

```bash
id YOUR_DSM_USER
```

Edit `.env` and set:

```dotenv
COLLECTOR_COMMIT=<the exact output of git rev-parse HEAD>
PUID=<numeric uid>
PGID=<numeric gid>
HOST_ID=synology-pl-01
MODE=smoke
SMOKE_DURATION_SECONDS=60
RUN_ID=
```

Then grant that account access to the data directory:

```bash
chown -R <PUID>:<PGID> data
chmod 0750 data data/runs
```

Do not add exchange keys to `.env` or to the Container Manager project.

When Git is unavailable on DSM, download an archive of the exact `develop` commit, extract it as `repo`, and put that same 40-character commit in `COLLECTOR_COMMIT`.

## 2. Check NAS prerequisites

Before starting:

- enable DSM time synchronization with a reliable NTP source;
- make sure the NAS will not sleep, shut down, update, or reboot during the 24-hour acceptance period;
- make sure the volume has free space and the `data` directory is writable by `PUID:PGID`;
- confirm outbound DNS, HTTPS, and WebSocket access to Bybit and Binance;
- do not route this container through a US exit node, restricted VPN location, or proxy that blocks exchange clock endpoints.

No router port-forward, reverse proxy, Container Manager port mapping, or inbound firewall rule is required.

## 3. Create the Container Manager project

In DSM:

1. Open **Container Manager**.
2. Open **Project** and select **Create**.
3. Use the project name `liquid20-collector`.
4. Select the folder:
   `/volume1/docker/freqtrade-liquidations/repo/deploy/synology/liquid20`
5. Use the existing `compose.yaml` from that folder.
6. Build and start the project.

The first image build installs only Python and the pinned `websockets` dependency. It does not install or start the trading bot.

Equivalent SSH command:

```bash
cd /volume1/docker/freqtrade-liquidations/repo/deploy/synology/liquid20
docker compose --env-file .env up --build --abort-on-container-exit
```

## 4. Run the smoke first

Keep `MODE=smoke`. The default smoke lasts 60 seconds and verifies that the NAS can connect to both public feeds and both exchange clock endpoints.

Watch the project log. After completion, inspect the newest directory under:

```text
data/runs/liquid20-<UTC timestamp>-<process id>/
```

A successful smoke should contain at least:

```text
bybit-linear.ndjson
bybit-linear-summary.json
binance-usdm.ndjson
binance-usdm-summary.json
multi-source-manifest.json
artifact-sha256.txt
```

Zero liquidation events in a one-minute smoke is not by itself a failure. The important checks are successful source completion, no parser errors, no restricted-region clock error, and valid artifact hashes.

Do not treat the smoke as 24-hour acceptance. The frozen evaluator is intentionally not run in smoke mode because the duration and activity gates cannot pass.

## 5. Start the declared 24-hour acceptance run

Only after the smoke is clean, edit `.env`:

```dotenv
MODE=acceptance
RUN_ID=
```

Leave `COLLECTOR_COMMIT`, `PUID`, `PGID`, and `HOST_ID` unchanged. Rebuild or recreate the project so the updated environment is applied.

Acceptance mode ignores `SMOKE_DURATION_SECONDS` and always uses exactly `86400` seconds. Do not manually stop, restart, update, or recreate the container during this run.

After approximately 24 hours, the container evaluates the immutable package and writes:

```text
multi-source-acceptance-report.json
artifact-sha256.txt
```

The report passes only when:

```json
"passed": true
```

If it contains `"passed": false`, preserve the complete run directory unchanged. Review `failed_gates`; do not edit the artifacts or weaken the policy after seeing the result.

## 6. Preserve and back up evidence

The complete directory under `data/runs/<RUN_ID>/` is the evidence package. Preserve all NDJSON, summaries, manifest, report, and `artifact-sha256.txt` together.

Verify hashes from SSH:

```bash
cd /volume1/docker/freqtrade-liquidations/repo/deploy/synology/liquid20/data/runs/<RUN_ID>
sha256sum --check artifact-sha256.txt
```

Optionally copy the completed directory to a read-only backup share after verification. Never reuse the same run directory for a rerun.

## Updating the collector later

A new repository commit requires a new image and a matching `.env` value:

```bash
cd /volume1/docker/freqtrade-liquidations/repo
git pull --ff-only origin develop
NEW_COMMIT="$(git rev-parse HEAD)"
```

Update `COLLECTOR_COMMIT` in `.env`, rebuild the image, and use a new generated `RUN_ID`. Never claim that artifacts produced by one commit were collected by another commit.
