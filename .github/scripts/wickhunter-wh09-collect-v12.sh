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
CANDIDATE_ROOT="/volume1/docker/freqtrade/state/wickhunter-candidate-materialization/packages/wickhunter-candidate-materialization-20260803-v2-626087ca45d6"
ACTIVATION_ROOT="/volume1/docker/freqtrade/state/wickhunter-paper-runtime/v12/activations/wickhunter-wh09-activation-20260805-v12-108eff81"
JOURNAL_ROOT="/volume1/docker/freqtrade/state/wickhunter-paper-runtime/v12/journals/wickhunter-wh09-activation-20260805-v12-108eff81"
HEALTH_ROOT="/volume1/docker/freqtrade/state/wickhunter-paper-runtime/v12/operator/wickhunter-wh09-activation-20260805-v12-108eff81"

: "${BASE_SHA:?BASE_SHA is required}"
: "${HEAD_SHA:?HEAD_SHA is required}"
: "${RUNNER_NAME_VALUE:?RUNNER_NAME_VALUE is required}"
: "${RUNNER_OS_VALUE:?RUNNER_OS_VALUE is required}"
: "${RUNNER_ARCH_VALUE:?RUNNER_ARCH_VALUE is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"
: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"
: "${GITHUB_STEP_SUMMARY:?GITHUB_STEP_SUMMARY is required}"

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

output="$RUNNER_TEMP/wickhunter-wh09-v12-terminal"
journal_copy="$RUNNER_TEMP/wickhunter-wh09-v12-journal-copy"
rm -rf "$output" "$journal_copy"
install -d -m 0777 "$output"
install -d -m 0777 "$journal_copy"

for path in "$CANDIDATE_ROOT" "$ACTIVATION_ROOT" "$JOURNAL_ROOT" "$HEALTH_ROOT"; do
  [[ "$path" == /* && -d "$path" && ! -L "$path" ]]
done
[[ -f "$HEALTH_ROOT/health.json" && ! -L "$HEALTH_ROOT/health.json" ]]
docker inspect "$OPERATOR_CONTAINER" >/dev/null
image_id="$(docker inspect --format '{{.Image}}' "$OPERATOR_CONTAINER")"
[[ "$image_id" == "$EXPECTED_IMAGE_ID" ]]

export IMPLEMENTATION_SHA ACTIVATION_NAME RUN_ID BINDING_ID JOURNAL_IDENTITY
export WINDOW_START_MS WINDOW_END_MS OPERATOR_CONTAINER HEALTH_ROOT
export OUTPUT_ROOT="$output" IMAGE_ID="$image_id"
python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path

health_path = Path(os.environ["HEALTH_ROOT"]) / "health.json"
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

manifest "$JOURNAL_ROOT" "$RUNNER_TEMP/journal-manifest-before.json"
sleep 3
manifest "$JOURNAL_ROOT" "$RUNNER_TEMP/journal-manifest-after.json"
cmp "$RUNNER_TEMP/journal-manifest-before.json" "$RUNNER_TEMP/journal-manifest-after.json"
cp -a "$JOURNAL_ROOT/." "$journal_copy/"
manifest "$journal_copy" "$output/journal-source-manifest.json"
cmp "$RUNNER_TEMP/journal-manifest-after.json" "$output/journal-source-manifest.json"
chmod -R a+rwX "$journal_copy"

finalized_at_ms="$(date +%s%3N)"
docker run --rm --interactive \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e FINALIZED_AT_MS="$finalized_at_ms" \
  -v "$CANDIDATE_ROOT:/candidate:ro" \
  -v "$ACTIVATION_ROOT:/activation:ro" \
  -v "$journal_copy:/journal:rw" \
  -v "$output:/out:rw" \
  --entrypoint python \
  "$image_id" - <<'PY'
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
  echo "output=$output"
  echo "outcome=$outcome"
  echo "blockers=$blockers"
} >> "$GITHUB_OUTPUT"
