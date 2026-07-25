#!/usr/bin/env bash
set -Eeuo pipefail

image_name="${PORTAL_IMAGE_NAME:-local/freqtrade-portal-web}"
container_name="${PORTAL_CONTAINER_NAME:-freqtrade-portal-staging}"
bind_address="${PORTAL_BIND_ADDRESS:-192.168.1.2}"
portal_port="${PORTAL_PORT:-3000}"
commit_sha="${GITHUB_SHA:?GITHUB_SHA is required}"
image="${image_name}:sha-${commit_sha}"
candidate="${container_name}-candidate-${GITHUB_RUN_ID:-manual}-${GITHUB_RUN_ATTEMPT:-1}"
previous_image=""

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
    --cpus 1.5
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

start_final() {
    local selected_image="$1"
    docker run -d \
        --name "$container_name" \
        --restart unless-stopped \
        --publish "${bind_address}:${portal_port}:3000" \
        "${common_args[@]}" \
        "$selected_image"
}

rollback() {
    docker rm -f "$container_name" >/dev/null 2>&1 || true
    if [[ -n "$previous_image" ]] && docker image inspect "$previous_image" >/dev/null 2>&1; then
        echo "Restoring previous portal image: $previous_image"
        start_final "$previous_image" >/dev/null
        wait_healthy "$container_name" || true
    else
        echo "No previous portal image is available for rollback." >&2
    fi
}

echo "Validating isolated candidate container."
docker run -d \
    --name "$candidate" \
    --restart no \
    "${common_args[@]}" \
    "$image"
wait_healthy "$candidate"
cleanup_candidate

if docker inspect "$container_name" >/dev/null 2>&1; then
    previous_image="$(docker inspect --format '{{.Config.Image}}' "$container_name")"
    docker rm -f "$container_name" >/dev/null
fi

if ! start_final "$image" >/dev/null; then
    rollback
    exit 1
fi

if ! wait_healthy "$container_name"; then
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
