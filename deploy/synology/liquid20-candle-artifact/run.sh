#!/usr/bin/env bash
set -Eeuo pipefail

request_path="${REQUEST_PATH:?REQUEST_PATH is required}"
contract_path="${CONTRACT_PATH:?CONTRACT_PATH is required}"
task_path="${TASK_PATH:?TASK_PATH is required}"
evidence_root="${EVIDENCE_ROOT:?EVIDENCE_ROOT is required}"
head_sha="${HEAD_SHA:?HEAD_SHA is required}"

[[ "$head_sha" =~ ^[0-9a-f]{40}$ ]]
[[ "$evidence_root" =~ ^[A-Za-z0-9._-]+$ ]]

dockerfile="deploy/synology/liquid20-candle-artifact/Dockerfile"
image="local/liquid20-candle-artifact:sha-${head_sha}"
run_token="${GITHUB_RUN_ID:-manual}-${GITHUB_RUN_ATTEMPT:-1}"
container="liquid20-candle-artifact-${run_token}"
exporter="${container}-export"
volume="${container}-output"
build_context=""
runtime_image_id=""
phase="preflight"

cleanup() {
    if command -v docker >/dev/null 2>&1; then
        docker rm -f "$container" "$exporter" >/dev/null 2>&1 || true
        docker volume rm "$volume" >/dev/null 2>&1 || true
        docker image rm "$image" >/dev/null 2>&1 || true
    fi
    if [[ -n "$build_context" ]]; then
        rm -rf "$build_context"
    fi
}

write_failure_evidence() {
    local status="$1"
    if [[ ! -s candle-artifact-error.txt ]]; then
        printf 'Liquid20 candle artifact failed during phase=%s with exit_code=%s\n' \
            "$phase" "$status" > candle-artifact-error.txt
    fi
    if [[ ! -f candle-artifact-failure.json ]]; then
        cat > candle-artifact-failure.json <<EOF
{
  "artifact_type": "Liquid20CandleArtifactFailure",
  "code_commit": "$head_sha",
  "exit_code": $status,
  "orders_submitted": 0,
  "partial_artifact_published": false,
  "performance_research_authorized": false,
  "phase": "$phase",
  "purpose_classification": "diagnostic_only",
  "request_path": "$request_path",
  "runtime_classification": "synology_self_hosted_bounded_container",
  "runtime_image": "$image",
  "runtime_image_id": "$runtime_image_id",
  "schema_version": 1,
  "trading_credentials_present": false
}
EOF
    fi
}

finish() {
    local status=$?
    trap - EXIT
    if (( status != 0 )); then
        write_failure_evidence "$status"
    fi
    cleanup
    exit "$status"
}
trap finish EXIT

phase="preflight"
command -v docker >/dev/null
test -S /var/run/docker.sock
docker version >/dev/null

test -f "$request_path"
test -f "$contract_path"
test -f "$task_path"
test -f "$dockerfile"
test ! -e "$evidence_root"
test ! -e ".$evidence_root.partial"

phase="prepare_context"
build_context="$(mktemp -d)"
cp -R ai_platform "$build_context/ai_platform"
mkdir -p "$build_context/tools/agents"
cp tools/agents/checkpoint.py "$build_context/tools/agents/checkpoint.py"
mkdir -p "$build_context/docs/agents/tasks"
cp docs/agents/GOVERNANCE_CONTRACT.json "$build_context/docs/agents/GOVERNANCE_CONTRACT.json"
cp "$task_path" "$build_context/$task_path"
cp "$dockerfile" "$build_context/Dockerfile"

phase="build_runtime"
docker build \
    --pull \
    --build-arg "CODE_COMMIT=$head_sha" \
    --file "$build_context/Dockerfile" \
    --label "org.opencontainers.image.source=${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-blakinio/freqtrade}" \
    --label "org.opencontainers.image.revision=$head_sha" \
    --tag "$image" \
    "$build_context" >/dev/null
runtime_image_id="$(docker image inspect --format '{{.Id}}' "$image")"

common_args=(
    --read-only
    --tmpfs /tmp:size=64m,mode=1777
    --cap-drop ALL
    --security-opt no-new-privileges:true
    --pids-limit 128
    --memory 512m
)

phase="validate_checkpoint"
docker run --rm \
    "${common_args[@]}" \
    "$image" \
    python tools/agents/checkpoint.py "$task_path" --require-checkpoint

phase="validate_request"
docker run --rm \
    "${common_args[@]}" \
    "$image" \
    python -m ai_platform.scripts.liquidation_candle_artifact \
    --request "$request_path" \
    --contract "$contract_path" \
    --validate-only

phase="collect_public_candles"
docker volume create "$volume" >/dev/null
docker create \
    --name "$container" \
    "${common_args[@]}" \
    --mount "type=volume,src=$volume,dst=/output" \
    "$image" \
    python -m ai_platform.scripts.liquidation_candle_artifact \
    --request "$request_path" \
    --contract "$contract_path" \
    --output-root "/output/$evidence_root" \
    --code-commit "$head_sha" >/dev/null

set +e
docker start --attach "$container" \
    > candle-artifact-result.json \
    2> candle-artifact-error.txt
build_status=$?
set -e

if (( build_status != 0 )); then
    if ! docker run --rm \
        --user 0:0 \
        "${common_args[@]}" \
        --mount "type=volume,src=$volume,dst=/output" \
        "$image" \
        sh -c 'test -z "$(find /output -mindepth 1 -print -quit)"'; then
        printf 'Failed build left data in the temporary output volume\n' >&2
        exit 97
    fi
    cat candle-artifact-error.txt >&2
    exit "$build_status"
fi

test ! -s candle-artifact-error.txt

phase="verify_artifact"
docker run --rm -i \
    "${common_args[@]}" \
    --mount "type=volume,src=$volume,dst=/output,readonly" \
    "$image" \
    python - "$evidence_root" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

root = Path("/output") / sys.argv[1]
manifest_path = root / "candle-artifact-manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
assert manifest["schema_version"] == 1
assert manifest["artifact_type"] == "Liquid20CandleArtifactManifest"
assert manifest["purpose_classification"] == "diagnostic_only"
assert manifest["target_run_ids"] == ["liquid20-20260724T170830Z-1"]
assert manifest["source_separated"] is True
assert manifest["cross_exchange_deduplication"] is False
assert manifest["missing_candle_is_zero"] is False
assert manifest["performance_research_authorized"] is False
assert manifest["protected_holdout_check"]["passed"] is True
assert manifest["execution_safety"] == {
    "orders_submitted": 0,
    "trading_credentials_present": False,
}
artifacts = manifest["artifacts"]
assert len(artifacts) == 40
assert {item["source"] for item in artifacts} == {"bybit-linear", "binance-usdm"}
assert all(item["record_count"] == 576 for item in artifacts)
assert len({(item["source"], item["symbol"]) for item in artifacts}) == 40

hash_lines = (root / "artifact-sha256.txt").read_text(encoding="utf-8").splitlines()
assert len(hash_lines) == 41
for line in hash_lines:
    digest, separator, logical_name = line.partition("  ")
    assert separator == "  "
    target = root / logical_name
    assert target.is_file()
    assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
PY

phase="export_artifact"
docker create \
    --name "$exporter" \
    --mount "type=volume,src=$volume,dst=/output,readonly" \
    "$image" \
    true >/dev/null
mkdir -p "$evidence_root"
docker cp "$exporter:/output/$evidence_root/." "$evidence_root/"
test -f "$evidence_root/candle-artifact-manifest.json"
test -f "$evidence_root/artifact-sha256.txt"

phase="complete"
