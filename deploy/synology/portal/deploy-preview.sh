#!/usr/bin/env bash
set -Eeuo pipefail

image_name="${PORTAL_IMAGE_NAME:-local/freqtrade-portal-web}"
container_name="${PORTAL_CONTAINER_NAME:-freqtrade-portal-staging}"
bind_address="${PORTAL_BIND_ADDRESS:-192.168.1.2}"
portal_port="${PORTAL_PORT:-3031}"
liquidations_host_root="${PORTAL_LIQUIDATIONS_HOST_ROOT:-/volume1/docker/freqtrade-liquidations/data}"
liquidations_container_root="/liquid20-data"
commit_sha="${GITHUB_SHA:?GITHUB_SHA is required}"
image="${image_name}:sha-${commit_sha}"
candidate="${container_name}-candidate-${GITHUB_RUN_ID:-manual}-${GITHUB_RUN_ATTEMPT:-1}"
previous_image=""
previous_bind_address=""
previous_port=""
latest_liquid20_run=""
liquidations_group_id=""

cleanup_candidate() {
    docker rm -f "$candidate" >/dev/null 2>&1 || true
}
trap cleanup_candidate EXIT

docker version >/dev/null
docker compose version >/dev/null
test -S /var/run/docker.sock

echo "Building exact portal image: $image"
docker build \
    --pull \
    --file deploy/synology/portal/Dockerfile \
    --label "org.opencontainers.image.source=${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-blakinio/freqtrade}" \
    --label "org.opencontainers.image.revision=${commit_sha}" \
    --tag "$image" \
    ai_platform/portal/web

liquidations_preflight="$(
    docker run --rm \
        --user 0 \
        --entrypoint node \
        --mount "type=bind,src=${liquidations_host_root},dst=${liquidations_container_root},readonly" \
        "$image" \
        -e '
          const fs = require("node:fs");
          const path = require("node:path");
          const root = "/liquid20-data";
          const nested = path.join(root, "runs");
          const rootStat = fs.lstatSync(root);
          if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) process.exit(1);
          const runsRoot = fs.existsSync(nested) && fs.lstatSync(nested).isDirectory() ? nested : root;
          const runIds = fs.readdirSync(runsRoot, {withFileTypes: true})
            .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink() && /^liquid20-\d{8}T\d{6}Z-\d+$/.test(entry.name))
            .map((entry) => entry.name)
            .sort()
            .reverse()
            .slice(0, 100);
          if (runIds.length === 0) process.exit(1);
          const latestRun = runIds[0];
          const directories = [root, runsRoot, ...runIds.map((runId) => path.join(runsRoot, runId))];
          const files = [
            path.join(runsRoot, latestRun, "bybit-linear.ndjson"),
            path.join(runsRoot, latestRun, "binance-usdm.ndjson"),
          ];
          for (const optional of [
            "bybit-linear-summary.json",
            "binance-usdm-summary.json",
            "multi-source-acceptance-report.json",
          ]) {
            const candidate = path.join(runsRoot, latestRun, optional);
            if (fs.existsSync(candidate)) files.push(candidate);
          }
          for (const runId of runIds) {
            const report = path.join(runsRoot, runId, "multi-source-acceptance-report.json");
            if (fs.existsSync(report) && !files.includes(report)) files.push(report);
          }
          const stats = [];
          for (const directory of directories) {
            const stat = fs.lstatSync(directory);
            if (!stat.isDirectory() || stat.isSymbolicLink()) process.exit(1);
            if ((stat.mode & 0o050) !== 0o050) process.exit(1);
            stats.push(stat);
          }
          for (const file of files) {
            const stat = fs.lstatSync(file);
            if (!stat.isFile() || stat.isSymbolicLink()) process.exit(1);
            if ((stat.mode & 0o040) !== 0o040) process.exit(1);
            stats.push(stat);
          }
          const groupId = stats[0].gid;
          if (stats.some((stat) => stat.gid !== groupId)) process.exit(1);
          process.stdout.write(`${latestRun}|${groupId}`);
        '
)"
IFS='|' read -r latest_liquid20_run liquidations_group_id <<< "$liquidations_preflight"
test -n "$latest_liquid20_run"
[[ "$liquidations_group_id" =~ ^[0-9]+$ ]]
printf 'Liquid20 Docker-daemon preflight: root=%s latest_run=%s read_group=%s\n' \
    "$liquidations_host_root" "$latest_liquid20_run" "$liquidations_group_id"

common_args=(
    --read-only
    --tmpfs /tmp:size=64m,mode=1777
    --tmpfs /app/.next/cache:size=64m,mode=0755
    --cap-drop ALL
    --security-opt no-new-privileges:true
    --pids-limit 256
    --memory 768m
    --group-add "$liquidations_group_id"
    --mount "type=bind,src=${liquidations_host_root},dst=${liquidations_container_root},readonly"
    --env PORTAL_WEB_DATA_MODE=fixture
    --env PORTAL_ENVIRONMENT=staging
    --env "PORTAL_LIQUIDATIONS_DATA_ROOT=${liquidations_container_root}"
    --label io.freqtrade.portal.preview=true
    --label io.freqtrade.portal.liquidations=read-only
    --label "io.freqtrade.portal.commit=${commit_sha}"
)

wait_healthy() {
    local name="$1"
    local status=""
    for _ in $(seq 1 90); do
        status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$name" 2>/dev/null || true)"
        if [[ "$status" == "healthy" ]]; then
            return 0
        fi
        if [[ "$status" == "exited" || "$status" == "dead" ]]; then
            break
        fi
        sleep 2
    done
    echo "Container $name did not become healthy; status=${status:-missing}" >&2
    docker logs --tail 80 "$name" 2>&1 || true
    return 1
}

wait_http() {
    local address="$1"
    local port="$2"
    local path="${3:-/}"
    for _ in $(seq 1 30); do
        if curl --fail --silent --show-error --max-time 5 \
            "http://${address}:${port}${path}" >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    echo "LAN endpoint did not become reachable: http://${address}:${port}${path}" >&2
    return 1
}

wait_liquidations_internal() {
    local name="$1"
    for _ in $(seq 1 30); do
        if docker exec "$name" node -e '
          const paths = [
            "/api/market/liquidations/health",
            "/api/market/liquidations/summary",
            "/api/market/liquidations?limit=1",
            "/market/liquidations",
          ];
          Promise.all(paths.map((path) => fetch(`http://127.0.0.1:3000${path}`)))
            .then(async (responses) => {
              if (responses.some((response) => !response.ok)) process.exit(1);
              const health = await responses[0].json();
              if (health.schema_version !== 1) process.exit(1);
              if (health.research_preview !== true) process.exit(1);
              if (health.trading_authorized !== false) process.exit(1);
              if (!health.run_id || !Array.isArray(health.active_sources)) process.exit(1);
            })
            .catch(() => process.exit(1));
        ' >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    echo "Liquid20 BFF or page did not become healthy in container $name" >&2
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
        echo "Restoring previous portal image on ${previous_bind_address}:${previous_port}: $previous_image"
        start_container \
            "$container_name" \
            "$previous_image" \
            "$previous_bind_address" \
            "$previous_port" \
            unless-stopped >/dev/null
        wait_healthy "$container_name" || true
        wait_http "$previous_bind_address" "$previous_port" || true
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

echo "Validating isolated candidate container."
if [[ "$previous_bind_address" == "$bind_address" && "$previous_port" == "$portal_port" ]]; then
    docker run -d \
        --name "$candidate" \
        --restart no \
        "${common_args[@]}" \
        "$image" >/dev/null
    wait_healthy "$candidate"
    wait_liquidations_internal "$candidate"
else
    start_container "$candidate" "$image" "$bind_address" "$portal_port" no >/dev/null
    wait_healthy "$candidate"
    wait_liquidations_internal "$candidate"
    wait_http "$bind_address" "$portal_port" "/market/liquidations"
fi
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
    || ! wait_liquidations_internal "$container_name" \
    || ! wait_http "$bind_address" "$portal_port" "/market/liquidations" \
    || ! wait_http "$bind_address" "$portal_port" "/api/market/liquidations/health"; then
    rollback
    exit 1
fi

running_image="$(docker inspect --format '{{.Config.Image}}' "$container_name")"
published_port="$(docker port "$container_name" 3000/tcp)"
liquidations_mount_source="$(docker inspect --format \
    '{{range .Mounts}}{{if eq .Destination "/liquid20-data"}}{{.Source}}{{end}}{{end}}' \
    "$container_name")"
liquidations_mount_rw="$(docker inspect --format \
    '{{range .Mounts}}{{if eq .Destination "/liquid20-data"}}{{.RW}}{{end}}{{end}}' \
    "$container_name")"
docker_socket_mount="$(docker inspect --format \
    '{{range .Mounts}}{{if eq .Destination "/var/run/docker.sock"}}{{.Source}}{{end}}{{end}}' \
    "$container_name")"
running_uid="$(docker exec "$container_name" id -u)"
running_groups="$(docker exec "$container_name" id -G)"

test "$running_image" = "$image"
test "$published_port" = "${bind_address}:${portal_port}"
test "$liquidations_mount_source" = "$liquidations_host_root"
test "$liquidations_mount_rw" = "false"
test -z "$docker_socket_mount"
test "$running_uid" != "0"
[[ " $running_groups " == *" $liquidations_group_id "* ]]

printf 'Portal preview healthy: image=%s container=%s bind=%s:%s liquid20=%s:ro uid=%s read_group=%s\n' \
    "$image" "$container_name" "$bind_address" "$portal_port" "$liquidations_host_root" \
    "$running_uid" "$liquidations_group_id"

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    {
        echo "### Synology portal preview deployed"
        echo
        echo "- Image: \`$image\`"
        echo "- Container: \`$container_name\`"
        echo "- LAN URL: \`http://synology:${portal_port}\`"
        echo "- Direct LAN URL: \`http://${bind_address}:${portal_port}\`"
        echo "- Liquid20 source: \`${liquidations_host_root}\` -> \`${liquidations_container_root}:ro\`"
        echo "- Liquid20 latest run: \`${latest_liquid20_run}\`"
        echo "- Runtime UID: \`${running_uid}\` (non-root)"
        echo "- Liquid20 read group: \`${liquidations_group_id}\`"
        echo "- Data mode: \`server-side Liquid20 read-model\`"
        echo "- Trading authorized: \`false\`"
    } >> "$GITHUB_STEP_SUMMARY"
fi
