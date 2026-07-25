#!/usr/bin/env bash
set -Eeuo pipefail

image_name="${PORTAL_IMAGE_NAME:-local/freqtrade-portal-web}"
container_name="${PORTAL_CONTAINER_NAME:-freqtrade-portal-staging}"
bind_address="${PORTAL_BIND_ADDRESS:-192.168.1.2}"
portal_port="${PORTAL_PORT:-3031}"
commit_sha="${GITHUB_SHA:?GITHUB_SHA is required}"
image="${image_name}:sha-${commit_sha}"
candidate="${container_name}-candidate-${GITHUB_RUN_ID:-manual}-${GITHUB_RUN_ATTEMPT:-1}"
previous_image=""
previous_bind_address=""
previous_port=""

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

common_args=(
    --read-only
    --tmpfs /tmp:size=64m,mode=1777
    --tmpfs /app/.next/cache:size=64m,mode=0755
    --cap-drop ALL
    --security-opt no-new-privileges:true
    --pids-limit 256
    --memory 768m
    --env PORTAL_WEB_DATA_MODE=fixture
    --env PORTAL_ENVIRONMENT=staging
    --label io.freqtrade.portal.preview=true
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
    for _ in $(seq 1 30); do
        if curl --fail --silent --show-error --max-time 5 \
            "http://${address}:${port}/" >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    echo "LAN endpoint did not become reachable: http://${address}:${port}/" >&2
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
else
    start_container "$candidate" "$image" "$bind_address" "$portal_port" no >/dev/null
    wait_healthy "$candidate"
    wait_http "$bind_address" "$portal_port"
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

if ! wait_healthy "$container_name" || ! wait_http "$bind_address" "$portal_port"; then
    rollback
    exit 1
fi

running_image="$(docker inspect --format '{{.Config.Image}}' "$container_name")"
published_port="$(docker port "$container_name" 3000/tcp)"
test "$running_image" = "$image"
test "$published_port" = "${bind_address}:${portal_port}"

printf 'Portal preview healthy: image=%s container=%s bind=%s:%s\n' \
    "$image" "$container_name" "$bind_address" "$portal_port"

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    {
        echo "### Synology portal preview deployed"
        echo
        echo "- Image: \`$image\`"
        echo "- Container: \`$container_name\`"
        echo "- LAN URL: \`http://synology:${portal_port}\`"
        echo "- Direct LAN URL: \`http://${bind_address}:${portal_port}\`"
        echo "- Data mode: \`fixture\`"
    } >> "$GITHUB_STEP_SUMMARY"
fi
