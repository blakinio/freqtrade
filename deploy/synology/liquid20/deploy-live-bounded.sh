#!/usr/bin/env bash
set -Eeuo pipefail

source_script="deploy/synology/liquid20/deploy-live.sh"
renderer="deploy/synology/liquid20/render-bounded-deploy.py"
rendered="${RUNNER_TEMP:-/tmp}/liquid20-deploy-live-bounded-${GITHUB_RUN_ID:-manual}-${GITHUB_RUN_ATTEMPT:-1}.sh"

cleanup() {
    rm -f "$rendered"
}
trap cleanup EXIT

python3 "$renderer" "$source_script" "$rendered"
bash -n "$rendered"
bash "$rendered"
