#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_BASE_SHA="094f3751d1109d82cc7254f4b5957cf808641c91"
IMPLEMENTATION_SHA="108eff8149f3c5dba77bfcdeaea0c63c8a22b551"
EXPECTED_IMAGE_ID="sha256:449ff348296a91865e7d884a2de26ddbb34d67c317afd348ee9e675444566f01"
ACTIVATION_NAME="wickhunter-wh09-activation-20260805-v12-108eff81"
RUN_ID="b895197c49550bd57a50fed93dda4ebbc5938839c17302ad086cce5fa4fedf14"
BINDING_ID="79ed4f7a3d211704d95b0304b633ba96512e44f4dedaa6ebaf37732397160702"
JOURNAL_IDENTITY="b2ffc66df1196c33ecf2f91c76ef3e3dd7862367a70f75db7e653d848a52a3d0"
WINDOW_START_MS="1785948307561"
WINDOW_END_MS="1786038307561"
OPERATOR_CONTAINER="wickhunter-paper-runtime-v12"
CANDIDATE_SOURCE="/volume1/docker/freqtrade/state/wickhunter-candidate-materialization/packages/wickhunter-candidate-materialization-20260803-v2-626087ca45d6"
ACTIVATION_SOURCE="/volume1/docker/freqtrade/state/wickhunter-paper-runtime/v12/activations/wickhunter-wh09-activation-20260805-v12-108eff81"
JOURNAL_SOURCE="/volume1/docker/freqtrade/state/wickhunter-paper-runtime/v12/journals/wickhunter-wh09-activation-20260805-v12-108eff81"
HEALTH_SOURCE="/volume1/docker/freqtrade/state/wickhunter-paper-runtime/v12/operator/wickhunter-wh09-activation-20260805-v12-108eff81"

: "${BASE_SHA:?BASE_SHA is required}"
: "${HEAD_SHA:?HEAD_SHA is required}"
: "${RUNNER_NAME_VALUE:?RUNNER_NAME_VALUE is required}"
: "${RUNNER_OS_VALUE:?RUNNER_OS_VALUE is required}"
: "${RUNNER_ARCH_VALUE:?RUNNER_ARCH_VALUE is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"
: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"
: "${GITHUB_STEP_SUMMARY:?GITHUB_STEP_SUMMARY is required}"

output="$RUNNER_TEMP/wickhunter-wh09-v12-terminal"
candidate_copy="$RUNNER_TEMP/wickhunter-wh09-v12-candidate-copy"
activation_copy="$RUNNER_TEMP/wickhunter-wh09-v12-activation-copy"
journal_before="$RUNNER_TEMP/wickhunter-wh09-v12-journal-before"
journal_copy="$RUNNER_TEMP/wickhunter-wh09-v12-journal-copy"
rm -rf "$output" "$candidate_copy" "$activation_copy" "$journal_before" "$journal_copy"
install -d -m 0777 "$output" "$candidate_copy" "$activation_copy" "$journal_before" "$journal_copy"
echo "output=$output" >> "$GITHUB_OUTPUT"

suffix="${GITHUB_RUN_ID:-manual}-${GITHUB_RUN_ATTEMPT:-1}-$$"
candidate_volume="wh09-candidate-$suffix"
activation_volume="wh09-activation-$suffix"
journal_volume="wh09-journal-$suffix"
output_volume="wh09-output-$suffix"
seed_containers=()
eval_container=""
extract_container=""

cleanup() {
  local status=$?
  set +e
  [[ -z "$eval_container" ]] || docker rm -f "$eval_container" >/dev/null 2>&1
  [[ -z "$extract_container" ]] || docker rm -f "$extract_container" >/dev/null 2>&1
  for container in "${seed_containers[@]}"; do
    docker rm -f "$container" >/dev/null 2>&1
  done
  docker volume rm -f "$candidate_volume" "$activation_volume" "$journal_volume" "$output_volume" >/dev/null 2>&1
  exit "$status"
}
trap cleanup EXIT
trap 'status=$?; printf "WH09_COLLECTOR_FAILURE line=%s exit=%s command=%q\n" "$LINENO" "$status" "$BASH_COMMAND" >&2; exit "$status"' ERR

[[ "$RUNNER_NAME_VALUE" == "freqtrade-synology-staging" ]]
[[ "$RUNNER_OS_VALUE" == "Linux" ]]
[[ "$RUNNER_ARCH_VALUE" == "X64" ]]
[[ "$BASE_SHA" == "$EXPECTED_BASE_SHA" ]]
[[ "$HEAD_SHA" == "$(git rev-parse HEAD)" ]]
docker version >/dev/null
test -S /var/run/docker.sock

mapfile -t changed < <(git diff --name-only "$BASE_SHA...$HEAD_SHA")
[[ "${#changed[@]}" -eq 2 ]]
[[ "${changed[0]}" == ".github/scripts/wickhunter-wh09-collect-v12.sh" ]]
[[ "${changed[1]}" == ".github/workflows/wickhunter-wh09-collect-20260806-v12.yml" ]]

now_ms="$(date +%s%3N)"
[[ "$now_ms" -ge "$WINDOW_END_MS" ]]
[[ $((WINDOW_END_MS - WINDOW_START_MS)) -ge 86400000 ]]

docker inspect "$OPERATOR_CONTAINER" > "$output/container-inspect.json"
image_id="$(docker inspect --format '{{.Image}}' "$OPERATOR_CONTAINER")"
[[ "$image_id" == "$EXPECTED_IMAGE_ID" ]]

INSPECT="$output/container-inspect.json" \
CANDIDATE_SOURCE="$CANDIDATE_SOURCE" \
ACTIVATION_SOURCE="$ACTIVATION_SOURCE" \
JOURNAL_SOURCE="$JOURNAL_SOURCE" \
HEALTH_SOURCE="$HEALTH_SOURCE" \
python3 - <<'PY'
import json
import os
from pathlib import Path

payload = json.loads(Path(os.environ["INSPECT"]).read_text(encoding="utf-8"))
if not isinstance(payload, list) or len(payload) != 1:
    raise SystemExit("unexpected docker inspect payload")
container = payload[0]
expected = {
    "/runtime/candidate": (os.environ["CANDIDATE_SOURCE"], False),
    "/runtime/activation": (os.environ["ACTIVATION_SOURCE"], False),
    "/runtime/journal": (os.environ["JOURNAL_SOURCE"], True),
    "/runtime/operator": (os.environ["HEALTH_SOURCE"], True),
}
actual = {
    mount["Destination"]: (mount["Source"], bool(mount["RW"]))
    for mount in container.get("Mounts", [])
    if mount.get("Destination") in expected
}
if actual != expected:
    raise SystemExit(f"operator mount identity mismatch: {actual!r}")
PY

# The self-hosted runner is containerized and does not expose Synology host
# paths directly. Copy through the Docker API from the exact operator instead.
docker cp "$OPERATOR_CONTAINER:/runtime/candidate/." "$candidate_copy/"
docker cp "$OPERATOR_CONTAINER:/runtime/activation/." "$activation_copy/"
docker cp "$OPERATOR_CONTAINER:/runtime/journal/." "$journal_before/"
docker cp "$OPERATOR_CONTAINER:/runtime/operator/health.json" "$output/health.json"
sleep 3
docker cp "$OPERATOR_CONTAINER:/runtime/journal/." "$journal_copy/"

manifest() {
  local root="$1"
  local destination="$2"
  ROOT="$root" DESTINATION="$destination" python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
records = []
for path in sorted(root.rglob("*")):
    if path.is_symlink():
        raise SystemExit(f"symlink rejected: {path}")
    if not path.is_file():
        continue
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    records.append({
        "path": path.relative_to(root).as_posix(),
        "size": path.stat().st_size,
        "sha256": digest.hexdigest(),
    })
Path(os.environ["DESTINATION"]).write_text(
    json.dumps(records, separators=(",", ":"), sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
}

manifest "$journal_before" "$RUNNER_TEMP/journal-manifest-before.json"
manifest "$journal_copy" "$RUNNER_TEMP/journal-manifest-after.json"
cmp "$RUNNER_TEMP/journal-manifest-before.json" "$RUNNER_TEMP/journal-manifest-after.json"
cp "$RUNNER_TEMP/journal-manifest-after.json" "$output/journal-source-manifest.json"

export IMPLEMENTATION_SHA ACTIVATION_NAME RUN_ID BINDING_ID JOURNAL_IDENTITY
export WINDOW_START_MS WINDOW_END_MS OPERATOR_CONTAINER
export OUTPUT_ROOT="$output" IMAGE_ID="$image_id"
python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path

health_path = Path(os.environ["OUTPUT_ROOT"]) / "health.json"
health = json.loads(health_path.read_text(encoding="utf-8"))
claimed = health.pop("health_sha256", None)
canonical = json.dumps(health, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
if claimed != hashlib.sha256(canonical.encode("utf-8")).hexdigest():
    raise SystemExit("health self-hash mismatch")
expected = {
    "operator_commit": os.environ["IMPLEMENTATION_SHA"],
    "binding_id": os.environ["BINDING_ID"],
    "run_id": os.environ["RUN_ID"],
    "window_start_ms": int(os.environ["WINDOW_START_MS"]),
    "window_end_ms": int(os.environ["WINDOW_END_MS"]),
    "protected_holdout_accessed": False,
    "automatic_promotion_enabled": False,
    "trading_credentials_present": False,
    "order_adapter_present": False,
    "execution_enabled": False,
    "orders_submitted": 0,
    "live_capital_authorized": False,
}
for key, value in expected.items():
    if health.get(key) != value:
        raise SystemExit(f"health identity or authority mismatch: {key}")
output = Path(os.environ["OUTPUT_ROOT"])
(output / "terminal-health.json").write_text(
    json.dumps({**health, "health_sha256": claimed}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
health_path.unlink()
provenance = {
    "container": os.environ["OPERATOR_CONTAINER"],
    "image_id": os.environ["IMAGE_ID"],
    "implementation_sha": os.environ["IMPLEMENTATION_SHA"],
    "activation_name": os.environ["ACTIVATION_NAME"],
    "run_id": os.environ["RUN_ID"],
    "binding_id": os.environ["BINDING_ID"],
    "journal_identity": os.environ["JOURNAL_IDENTITY"],
    "window_start_ms": int(os.environ["WINDOW_START_MS"]),
    "window_end_ms": int(os.environ["WINDOW_END_MS"]),
    "source_journal_mutated": False,
    "network_used_for_evaluation": False,
    "protected_holdout_accessed": False,
    "automatic_promotion_enabled": False,
    "trading_credentials_present": False,
    "order_adapter_present": False,
    "execution_enabled": False,
    "orders_submitted": 0,
    "live_capital_authorized": False,
}
(output / "collection-provenance.json").write_text(
    json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
PY

docker volume create "$candidate_volume" >/dev/null
docker volume create "$activation_volume" >/dev/null
docker volume create "$journal_volume" >/dev/null
docker volume create "$output_volume" >/dev/null

seed_volume() {
  local volume="$1"
  local source="$2"
  local name="wh09-seed-${suffix}-${#seed_containers[@]}"
  docker create --name "$name" -v "$volume:/seed" --entrypoint /bin/true "$image_id" >/dev/null
  seed_containers+=("$name")
  docker cp "$source/." "$name:/seed/"
  docker rm "$name" >/dev/null
  seed_containers=("${seed_containers[@]:0:${#seed_containers[@]}-1}")
}

seed_volume "$candidate_volume" "$candidate_copy"
seed_volume "$activation_volume" "$activation_copy"
seed_volume "$journal_volume" "$journal_copy"

finalized_at_ms="$(date +%s%3N)"
eval_container="wh09-evaluate-$suffix"
docker create --interactive \
  --name "$eval_container" \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e FINALIZED_AT_MS="$finalized_at_ms" \
  -v "$candidate_volume:/candidate:ro" \
  -v "$activation_volume:/activation:ro" \
  -v "$journal_volume:/journal:rw" \
  -v "$output_volume:/out:rw" \
  --entrypoint python \
  "$image_id" - >/dev/null

docker start --attach --interactive "$eval_container" <<'PY'
from pathlib import Path
import os

from ai_platform.wickhunter.candidate_paper_runtime_operator import _runtime_policy
from ai_platform.wickhunter.candidate_paper_runtime_service import (
    CandidatePaperRuntimeJournal,
    CandidatePaperRuntimeService,
)
from ai_platform.wickhunter.candidate_runtime_binding import (
    build_candidate_paper_runtime_binding,
)
from ai_platform.wickhunter.canonical import canonical_json
from ai_platform.wickhunter.paper_validation import PaperValidationOutcome

candidate_root = Path("/candidate")
activation_root = Path("/activation")
journal_root = Path("/journal")
output_root = Path("/out")
binding = build_candidate_paper_runtime_binding(
    candidate_root=candidate_root,
    activation_root=activation_root,
)
journal = CandidatePaperRuntimeJournal(journal_root, binding, _runtime_policy())
result = journal.evaluate()
(output_root / "evaluation-report.json").write_text(
    canonical_json(result.report) + "\n", encoding="utf-8"
)
(output_root / "candidate-review.json").write_text(
    canonical_json(result.candidate_review) + "\n", encoding="utf-8"
)
summary = {
    "outcome": result.report.outcome.value,
    "blocker_codes": list(result.report.blocker_codes),
    "candidate_review_eligible": result.report.candidate_review_eligible,
    "owner_decision_required": result.report.owner_decision_required,
    "summary": result.report.summary,
    "observation_count": len(result.observations),
    "protected_holdout_accessed": False,
    "automatic_promotion_enabled": False,
    "trading_credentials_present": False,
    "order_adapter_present": False,
    "execution_enabled": False,
    "orders_submitted": 0,
    "live_capital_authorized": False,
}
(output_root / "terminal-summary.json").write_text(
    canonical_json(summary) + "\n", encoding="utf-8"
)
if result.report.outcome is PaperValidationOutcome.READY_FOR_OWNER_REVIEW:
    service = CandidatePaperRuntimeService(
        binding=binding,
        runtime_policy=_runtime_policy(),
        journal_root=journal_root,
    )
    service.finalize(
        output_root / "immutable-final-package",
        finalized_at_ms=int(os.environ["FINALIZED_AT_MS"]),
    )
PY

docker rm "$eval_container" >/dev/null
eval_container=""
extract_container="wh09-extract-$suffix"
docker create --name "$extract_container" -v "$output_volume:/out:ro" --entrypoint /bin/true "$image_id" >/dev/null
docker cp "$extract_container:/out/." "$output/"
docker rm "$extract_container" >/dev/null
extract_container=""

outcome="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["outcome"])' "$output/terminal-summary.json")"
blockers="$(python3 -c 'import json,sys; print(",".join(json.load(open(sys.argv[1]))["blocker_codes"]))' "$output/terminal-summary.json")"

OUTPUT_ROOT="$output" python3 - <<'PY'
import hashlib
import os
from pathlib import Path

root = Path(os.environ["OUTPUT_ROOT"])
index = root / "artifact-sha256.txt"
names = sorted(
    path.relative_to(root).as_posix()
    for path in root.rglob("*")
    if path.is_file() and path != index
)
with index.open("x", encoding="utf-8") as handle:
    for name in names:
        digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
        handle.write(f"{digest}  {name}\n")
PY
find "$output" -type l -print -quit | grep -q . && exit 1 || true
test -s "$output/artifact-sha256.txt"

{
  echo "## WickHunter WH09 v12 terminal PAPER collection"
  echo
  echo "- Implementation: \`$IMPLEMENTATION_SHA\`"
  echo "- Run: \`$RUN_ID\`"
  echo "- Binding: \`$BINDING_ID\`"
  echo "- Outcome: \`$outcome\`"
  echo "- Blockers: \`${blockers:-none}\`"
  echo "- Source journal mutation: \`false\`"
  echo "- Evaluation network: \`none\`"
  echo "- Orders submitted: \`0\`"
  echo "- Owner decision remains separate: \`true\`"
} >> "$GITHUB_STEP_SUMMARY"

{
  echo "outcome=$outcome"
  echo "blockers=$blockers"
} >> "$GITHUB_OUTPUT"
