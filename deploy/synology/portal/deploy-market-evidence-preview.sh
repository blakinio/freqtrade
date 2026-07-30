#!/usr/bin/env bash
set -Eeuo pipefail

image_name="${PORTAL_IMAGE_NAME:-local/freqtrade-portal-web}"
container_name="${PORTAL_CONTAINER_NAME:-freqtrade-portal-staging}"
bind_address="${PORTAL_BIND_ADDRESS:-192.168.1.2}"
portal_port="${PORTAL_PORT:-3031}"
liquidations_host_root="${PORTAL_LIQUIDATIONS_HOST_ROOT:-/volume1/docker/freqtrade-liquidations/data}"
market_evidence_host_root="${PORTAL_MARKET_EVIDENCE_HOST_ROOT:-/volume1/docker/freqtrade-staging-state/wickhunter-production-market-evidence}"
liquidations_container_root="/liquid20-data"
market_evidence_container_root="/market-evidence-data"
commit_sha="${GITHUB_SHA:?GITHUB_SHA is required}"
image="${image_name}:sha-${commit_sha}"
candidate="${container_name}-candidate-${GITHUB_RUN_ID:-manual}-${GITHUB_RUN_ATTEMPT:-1}"
previous_image=""
previous_bind_address=""
previous_port=""
liquidations_group_id=""
market_evidence_group_id=""
latest_liquid20_run=""
latest_market_evidence_run=""

cleanup_candidate() {
    docker rm -f "$candidate" >/dev/null 2>&1 || true
}
trap cleanup_candidate EXIT

require_absolute_directory() {
    local name="$1"
    local value="$2"
    if [[ "$value" != /* || ! -d "$value" ]]; then
        echo "$name must be an existing absolute directory: $value" >&2
        exit 1
    fi
}

require_absolute_directory PORTAL_LIQUIDATIONS_HOST_ROOT "$liquidations_host_root"
require_absolute_directory PORTAL_MARKET_EVIDENCE_HOST_ROOT "$market_evidence_host_root"
docker version >/dev/null
docker compose version >/dev/null
test -S /var/run/docker.sock

if [[ ! "$commit_sha" =~ ^[0-9a-f]{40}$ ]]; then
    echo "GITHUB_SHA must be a lowercase 40-character commit SHA" >&2
    exit 1
fi

echo "Building exact portal image: $image"
docker build \
    --pull \
    --file deploy/synology/portal/Dockerfile \
    --label "org.opencontainers.image.source=${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-blakinio/freqtrade}" \
    --label "org.opencontainers.image.revision=${commit_sha}" \
    --tag "$image" \
    ai_platform/portal/web

read -r latest_liquid20_run liquidations_group_id < <(
    docker run --rm \
        --user 0 \
        --entrypoint node \
        --mount "type=bind,src=${liquidations_host_root},dst=${liquidations_container_root},readonly" \
        "$image" \
        -e '
          const fs = require("node:fs");
          const path = require("node:path");
          const root = "/liquid20-data";
          const rootStat = fs.lstatSync(root);
          if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) process.exit(1);
          const nested = path.join(root, "runs");
          const runsRoot = fs.existsSync(nested) && fs.lstatSync(nested).isDirectory() ? nested : root;
          const runIds = fs.readdirSync(runsRoot, {withFileTypes: true})
            .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink() && /^liquid20-\d{8}T\d{6}Z-\d+$/.test(entry.name))
            .map((entry) => entry.name)
            .sort()
            .reverse();
          if (runIds.length === 0) process.exit(1);
          const latest = runIds[0];
          const paths = [root, runsRoot, path.join(runsRoot, latest)];
          for (const required of ["bybit-linear.ndjson", "binance-usdm.ndjson"]) {
            paths.push(path.join(runsRoot, latest, required));
          }
          const stats = paths.map((candidate) => fs.lstatSync(candidate));
          if (stats.some((stat) => stat.isSymbolicLink())) process.exit(1);
          if (!stats.slice(0, 3).every((stat) => stat.isDirectory())) process.exit(1);
          if (!stats.slice(3).every((stat) => stat.isFile())) process.exit(1);
          const groupId = stats[0].gid;
          if (stats.some((stat) => stat.gid !== groupId || (stat.mode & 0o040) === 0)) process.exit(1);
          process.stdout.write(`${latest} ${groupId}`);
        '
)

read -r latest_market_evidence_run market_evidence_group_id < <(
    docker run --rm \
        --user 0 \
        --entrypoint node \
        --mount "type=bind,src=${market_evidence_host_root},dst=${market_evidence_container_root},readonly" \
        "$image" \
        -e '
          const fs = require("node:fs");
          const path = require("node:path");
          const root = "/market-evidence-data";
          const rootStat = fs.lstatSync(root);
          if (!rootStat.isDirectory() || rootStat.isSymbolicLink() || (rootStat.mode & 0o050) !== 0o050) process.exit(1);
          const nested = path.join(root, "runs");
          const runsRoot = fs.existsSync(nested) && fs.lstatSync(nested).isDirectory() ? nested : root;
          const runIds = fs.readdirSync(runsRoot, {withFileTypes: true})
            .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink() && /^wickhunter-production-market-evidence-\d{8}-v\d+-r\d+$/.test(entry.name))
            .map((entry) => entry.name)
            .sort()
            .reverse();
          const latest = runIds[0] ?? "none";
          const stats = [rootStat];
          if (latest !== "none") {
            const runRoot = path.join(runsRoot, latest);
            const runStat = fs.lstatSync(runRoot);
            if (!runStat.isDirectory() || runStat.isSymbolicLink()) process.exit(1);
            stats.push(runStat);
            const packageRoot = path.join(runRoot, "immutable-package");
            if (fs.existsSync(packageRoot)) {
              const packageStat = fs.lstatSync(packageRoot);
              if (!packageStat.isDirectory() || packageStat.isSymbolicLink()) process.exit(1);
              stats.push(packageStat);
              for (const name of ["manifest.json", "run-state.json", "verification-report.json"]) {
                const fileStat = fs.lstatSync(path.join(packageRoot, name));
                if (!fileStat.isFile() || fileStat.isSymbolicLink()) process.exit(1);
                stats.push(fileStat);
              }
            }
          }
          const groupId = stats[0].gid;
          if (stats.some((stat) => stat.gid !== groupId || (stat.mode & 0o040) === 0)) process.exit(1);
          process.stdout.write(`${latest} ${groupId}`);
        '
)

test -n "$latest_liquid20_run"
test -n "$latest_market_evidence_run"
[[ "$liquidations_group_id" =~ ^[0-9]+$ ]]
[[ "$market_evidence_group_id" =~ ^[0-9]+$ ]]
printf 'Portal data preflight: liquid20=%s gid=%s market_evidence=%s gid=%s\n' \
    "$latest_liquid20_run" "$liquidations_group_id" \
    "$latest_market_evidence_run" "$market_evidence_group_id"

group_args=(--group-add "$liquidations_group_id")
if [[ "$market_evidence_group_id" != "$liquidations_group_id" ]]; then
    group_args+=(--group-add "$market_evidence_group_id")
fi

common_args=(
    --read-only
    --tmpfs /tmp:size=64m,mode=1777
    --tmpfs /app/.next/cache:size=64m,mode=0755
    --cap-drop ALL
    --security-opt no-new-privileges:true
    --pids-limit 256
    --memory 768m
    "${group_args[@]}"
    --mount "type=bind,src=${liquidations_host_root},dst=${liquidations_container_root},readonly"
    --mount "type=bind,src=${market_evidence_host_root},dst=${market_evidence_container_root},readonly"
    --env PORTAL_WEB_DATA_MODE=fixture
    --env PORTAL_ENVIRONMENT=test
    --env PORTAL_IDENTITY_FIXTURE_MODE=enabled
    --env "PORTAL_LIQUIDATIONS_DATA_ROOT=${liquidations_container_root}"
    --env "PORTAL_MARKET_EVIDENCE_DATA_ROOT=${market_evidence_container_root}"
    --label io.freqtrade.portal.preview=true
    --label io.freqtrade.portal.identity=fixture
    --label io.freqtrade.portal.liquidations=read-only
    --label io.freqtrade.portal.market-evidence=read-only
    --label "io.freqtrade.portal.commit=${commit_sha}"
)

wait_healthy() {
    local name="$1"
    local status=""
    for _ in $(seq 1 90); do
        status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$name" 2>/dev/null || true)"
        [[ "$status" == "healthy" ]] && return 0
        [[ "$status" == "exited" || "$status" == "dead" ]] && break
        sleep 2
    done
    echo "Container $name did not become healthy; status=${status:-missing}" >&2
    docker logs --tail 120 "$name" 2>&1 || true
    return 1
}

wait_http() {
    local address="$1"
    local port="$2"
    local path="$3"
    for _ in $(seq 1 30); do
        curl --fail --silent --show-error --max-time 5 \
            "http://${address}:${port}${path}" >/dev/null 2>&1 && return 0
        sleep 2
    done
    return 1
}

wait_internal_boundaries() {
    local name="$1"
    for _ in $(seq 1 30); do
        if docker exec "$name" node -e '
          (async () => {
            const login = await fetch("http://127.0.0.1:3000/api/identity/login?return_to=%2Fmarket%2Fevidence", {redirect: "manual"});
            if (login.status !== 303) process.exit(1);
            const cookies = login.headers.getSetCookie?.() ?? [];
            const cookie = cookies.map((value) => value.split(";", 1)[0]).join("; ");
            if (!cookie.includes("portal_fixture_session=") || !cookie.includes("portal_fixture_csrf=")) process.exit(1);
            const page = await fetch("http://127.0.0.1:3000/market/evidence", {headers: {cookie}});
            if (!page.ok) process.exit(1);
            for (const path of [
              "/api/market/liquidations/health",
              "/api/market/evidence/summary",
              "/api/market/evidence/sources",
              "/api/market/evidence/instruments?page=1&page_size=1",
              "/api/market/evidence/runs?page=1&page_size=1",
            ]) {
              const response = await fetch(`http://127.0.0.1:3000${path}`, {headers: {cookie}});
              if (!response.ok) process.exit(1);
              const payload = await response.text();
              if (/\/volume1\/|\/var\/lib\/|api[_-]?key|passphrase/i.test(payload)) process.exit(1);
              if (payload.length > 250000) process.exit(1);
            }
          })().catch(() => process.exit(1));
        ' >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    echo "Portal identity and market-evidence boundaries failed in $name" >&2
    docker logs --tail 120 "$name" 2>&1 || true
    return 1
}

start_container() {
    local name="$1"
    local selected_image="$2"
    local selected_bind="$3"
    local selected_port="$4"
    local restart_policy="$5"
    docker run -d \
        --name "$name" \
        --restart "$restart_policy" \
        --publish "${selected_bind}:${selected_port}:3000" \
        "${common_args[@]}" \
        "$selected_image"
}

rollback() {
    docker rm -f "$container_name" >/dev/null 2>&1 || true
    if [[ -n "$previous_image" && -n "$previous_bind_address" && -n "$previous_port" ]] \
        && docker image inspect "$previous_image" >/dev/null 2>&1; then
        start_container \
            "$container_name" "$previous_image" "$previous_bind_address" "$previous_port" \
            unless-stopped >/dev/null
        wait_healthy "$container_name" || true
        wait_http "$previous_bind_address" "$previous_port" "/market/evidence" || true
    else
        echo "No complete previous portal mapping is available for rollback." >&2
    fi
}

if docker inspect "$container_name" >/dev/null 2>&1; then
    previous_image="$(docker inspect --format '{{.Config.Image}}' "$container_name")"
    previous_published="$(docker port "$container_name" 3000/tcp | head -n 1 || true)"
    if [[ -n "$previous_published" ]]; then
        previous_bind_address="${previous_published%:*}"
        previous_port="${previous_published##*:}"
    fi
fi

start_container "$candidate" "$image" "$bind_address" "$portal_port" no >/dev/null
wait_healthy "$candidate"
wait_internal_boundaries "$candidate"
wait_http "$bind_address" "$portal_port" "/market/evidence"
cleanup_candidate

if docker inspect "$container_name" >/dev/null 2>&1; then
    docker rm -f "$container_name" >/dev/null
fi
if ! start_container \
    "$container_name" "$image" "$bind_address" "$portal_port" unless-stopped >/dev/null; then
    rollback
    exit 1
fi
if ! wait_healthy "$container_name" \
    || ! wait_internal_boundaries "$container_name" \
    || ! wait_http "$bind_address" "$portal_port" "/market/evidence"; then
    rollback
    exit 1
fi

running_image="$(docker inspect --format '{{.Config.Image}}' "$container_name")"
published_port="$(docker port "$container_name" 3000/tcp)"
liquidations_mount_rw="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/liquid20-data"}}{{.RW}}{{end}}{{end}}' "$container_name")"
market_evidence_mount_rw="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/market-evidence-data"}}{{.RW}}{{end}}{{end}}' "$container_name")"
docker_socket_mount="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/run/docker.sock"}}{{.Source}}{{end}}{{end}}' "$container_name")"
running_uid="$(docker exec "$container_name" id -u)"
running_groups="$(docker exec "$container_name" id -G)"
running_environment="$(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$container_name")"

test "$running_image" = "$image"
test "$published_port" = "${bind_address}:${portal_port}"
test "$liquidations_mount_rw" = "false"
test "$market_evidence_mount_rw" = "false"
test -z "$docker_socket_mount"
test "$running_uid" != "0"
[[ " $running_groups " == *" $liquidations_group_id "* ]]
[[ " $running_groups " == *" $market_evidence_group_id "* ]]
grep -qx "PORTAL_LIQUIDATIONS_DATA_ROOT=${liquidations_container_root}" <<< "$running_environment"
grep -qx "PORTAL_MARKET_EVIDENCE_DATA_ROOT=${market_evidence_container_root}" <<< "$running_environment"
if grep -Eq 'PORTAL_CONTROL_PLANE_URL=|API_KEY=|API_SECRET=|PASSPHRASE=' <<< "$running_environment"; then
    echo "Preview must not declare control-plane or exchange credentials" >&2
    exit 1
fi

printf 'Portal preview healthy: image=%s bind=%s:%s liquid20=%s:ro market_evidence=%s:ro uid=%s\n' \
    "$image" "$bind_address" "$portal_port" \
    "$liquidations_host_root" "$market_evidence_host_root" "$running_uid"

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    {
        echo "### Synology Portal market-evidence preview deployed"
        echo
        echo "- Image: \`$image\`"
        echo "- Direct LAN URL: \`http://${bind_address}:${portal_port}/market/evidence\`"
        echo "- Liquid20 source: \`${liquidations_host_root}:ro\`"
        echo "- Market evidence source: \`${market_evidence_host_root}:ro\`"
        echo "- Market evidence run: \`${latest_market_evidence_run}\`"
        echo "- Runtime UID: \`${running_uid}\`"
        echo "- Identity mode: fixture preview"
        echo "- Trading authorized: \`false\`"
    } >> "$GITHUB_STEP_SUMMARY"
fi
