#!/usr/bin/env bash
set -euo pipefail
umask 027

: "${IMPLEMENTATION_SHA:?}"
: "${EXPECTED_BASE_SHA:?}"
: "${CANDIDATE_PACKAGE_NAME:?}"
: "${EXPECTED_CANDIDATE_MANIFEST_SHA256:?}"
: "${RUNNER_STATE_ROOT:?}"
: "${HOST_STATE_ROOT:?}"
: "${LIQUID20_LIVE_HOST:?}"
: "${PAPER_IMAGE:?}"
: "${PROD_PAPER_CONTAINER:?}"
: "${PROD_GATEWAY_CONTAINER:?}"
: "${PROD_INTERNAL_NETWORK:?}"
: "${PORTAL_CONTROL_CONTAINER:?}"
: "${PORTAL_WEB_CONTAINER:?}"
: "${PROOF_ARTIFACT_ID:?}"
: "${PROOF_ARTIFACT_DIGEST:?}"
: "${PROOF_RUN_ID:?}"
: "${PROOF_RUN_HEAD_SHA:?}"
: "${PROOF_PAPER_IMAGE_DIGEST:?}"
: "${REQUEST_HELPER:?}"
: "${RUNNER_TEMP:?}"
: "${GITHUB_WORKSPACE:?}"
: "${GITHUB_REPOSITORY:?}"
: "${GITHUB_TOKEN:?}"

EVIDENCE="$RUNNER_TEMP/issue1396-transition-v3"
RECOVERY="$EVIDENCE/recovery"
PROOF_DIR="$EVIDENCE/r13-proof"
mkdir -p "$EVIDENCE" "$RECOVERY" "$PROOF_DIR"

log() { printf '[issue1396-v3] %s\n' "$*"; }

json_value() {
  python3 - "$1" "$2" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
cur=p
for part in sys.argv[2].split('.'):
    cur=cur[part]
print(cur)
PY
}

validate_generation_snapshot() {
  local health_path="$1"
  local journal_root="$2"
  local output_path="$3"
  python3 - "$health_path" "$journal_root" "$output_path" <<'PY'
import json,sys
from pathlib import Path
health=json.load(open(sys.argv[1],encoding='utf-8'))
root=Path(sys.argv[2]); out=Path(sys.argv[3])
zero={'protected_holdout_accessed':False,'automatic_promotion_enabled':False,'trading_credentials_present':False,'order_adapter_present':False,'execution_enabled':False,'orders_submitted':0,'live_capital_authorized':False}
if health.get('status')!='healthy' or health.get('runtime_health')!='healthy': raise SystemExit('persistent PAPER health is not genuinely healthy')
if health.get('circuit_breaker_active') is not False or health.get('circuit_breaker_reasons')!=[]: raise SystemExit('persistent PAPER circuit breaker is active')
for key,value in zero.items():
    if health.get(key)!=value: raise SystemExit(f'persistent authority mismatch: {key}')
g=health.get('generation')
if isinstance(g,bool) or not isinstance(g,int) or g<1: raise SystemExit('persistent generation invalid')
path=root/'generations'/f'{g:020d}'/'runtime'/'portal-observability-snapshot.json'
s=json.loads(path.read_text(encoding='utf-8'))
expected=['binance-usdm','bybit-linear','okx-swap']
sources=s.get('source_freshness')
if s.get('health')!='healthy' or s.get('circuit_breaker_active') is not False or s.get('circuit_breaker_reasons')!=[]: raise SystemExit('persistent snapshot not breaker-free healthy')
if not isinstance(sources,list) or sorted(item.get('source') for item in sources)!=expected: raise SystemExit('persistent source set mismatch')
if any(item.get('health')!='healthy' or item.get('fresh') is not True or not isinstance(item.get('age_ms'),int) or item.get('age_ms')>300000 for item in sources): raise SystemExit('persistent source unhealthy or stale')
for key,value in zero.items():
    if s.get(key)!=value: raise SystemExit(f'persistent snapshot authority mismatch: {key}')
p={'result':'PASS','generation':g,'health_sha256':health.get('health_sha256'),'liquid20_snapshot_id':health.get('liquid20_snapshot_id'),'sources':[{'source':i['source'],'age_ms':i['age_ms']} for i in sources],**zero}
out.write_text(json.dumps(p,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(p,sort_keys=True))
PY
}

recover() {
  set +e
  mkdir -p "$RECOVERY"
  if [[ -z "${OLD_SHADOW_CONTAINER_ID:-}" ]]; then
    printf '%s\n' '{"result":"NO_MUTATION_BEFORE_BASELINE"}' > "$RECOVERY/result.json"
    return 0
  fi
  if ! docker container inspect "$PROD_PAPER_CONTAINER" >/dev/null 2>&1; then
    printf '%s\n' '{"result":"NO_PAPER_RUNTIME_CREATED"}' > "$RECOVERY/result.json"
    return 0
  fi
  local paper_id health_file recovery_exit result
  paper_id="$(docker inspect --format '{{.Id}}' "$PROD_PAPER_CONTAINER" 2>/dev/null)"
  health_file="${PROD_OPERATOR_HOST:-missing}/health.json"
  if [[ "$(docker inspect --format '{{.State.Health.Status}}' "$PROD_PAPER_CONTAINER" 2>/dev/null)" == "healthy" && -f "$health_file" && "$(docker inspect --format '{{.State.Running}}' "$PORTAL_CONTROL_CONTAINER" 2>/dev/null)" == "true" ]]; then
    cp "$REQUEST_HELPER" "$RECOVERY/issue1396_terminal_transition_v2.py"
    cp "$health_file" "$RECOVERY/paper-health.json"
    docker cp "$RECOVERY/issue1396_terminal_transition_v2.py" "$PORTAL_CONTROL_CONTAINER:/tmp/issue1396_terminal_transition_v2.py" >/dev/null 2>&1
    docker cp "$RECOVERY/paper-health.json" "$PORTAL_CONTROL_CONTAINER:/tmp/issue1396-recovery-paper-health.json" >/dev/null 2>&1
    docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396_terminal_transition_v2.py recover-to-paper \
      --old-runtime-instance-id "$OLD_SHADOW_CONTAINER_ID" --paper-runtime-instance-id "$paper_id" \
      --health-json /tmp/issue1396-recovery-paper-health.json --source-version "$IMPLEMENTATION_SHA" \
      --image-digest "${PAPER_IMAGE_DIGEST:-missing}" --config-digest "${PAPER_CONFIG_DIGEST:-missing}" \
      > "$RECOVERY/result.json"
    recovery_exit=$?
    if [[ "$recovery_exit" == "0" ]]; then
      result="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("result",""))' "$RECOVERY/result.json" 2>/dev/null)"
      if [[ "$result" == "NO_CANONICAL_MUTATION" ]]; then
        docker rm -f "$PROD_PAPER_CONTAINER" "$PROD_GATEWAY_CONTAINER" >/dev/null 2>&1
        docker network rm "$PROD_INTERNAL_NETWORK" >/dev/null 2>&1
        if [[ -n "${PROD_STATE_RUNNER:-}" && -e "$PROD_STATE_RUNNER" ]]; then rm -rf --one-file-system "$PROD_STATE_RUNNER"; fi
      fi
      return 0
    fi
  fi
  printf '%s\n' '{"result":"FAIL_CLOSED_MANUAL_RECONCILIATION_REQUIRED"}' > "$RECOVERY/result.json"
  return 1
}

on_exit() {
  local status=$?
  if [[ "$status" != "0" ]]; then
    log "transition failed; attempting fail-closed reconciliation"
    recover || true
  fi
}
trap on_exit EXIT

log "bind accepted r13 artifact"
META="$EVIDENCE/proof-artifact-meta.json"
ZIP="$EVIDENCE/proof.zip"
curl --fail --silent --show-error --location \
  -H "Authorization: Bearer $GITHUB_TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$PROOF_ARTIFACT_ID" -o "$META"
python3 - "$META" "$PROOF_ARTIFACT_ID" "$PROOF_ARTIFACT_DIGEST" "$PROOF_RUN_ID" "$PROOF_RUN_HEAD_SHA" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8')); aid,digest,run,head=sys.argv[2:]
if str(p.get('id'))!=aid: raise SystemExit('proof artifact id mismatch')
if p.get('name')!=f'issue1396-paper-proof-r13-{run}': raise SystemExit('proof artifact name mismatch')
if p.get('expired') is not False: raise SystemExit('proof artifact expired')
if p.get('digest')!=f'sha256:{digest}': raise SystemExit('proof artifact digest metadata mismatch')
w=p.get('workflow_run') or {}
if str(w.get('id'))!=run or w.get('head_sha')!=head: raise SystemExit('proof artifact workflow identity mismatch')
PY
curl --fail --silent --show-error --location \
  -H "Authorization: Bearer $GITHUB_TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$PROOF_ARTIFACT_ID/zip" -o "$ZIP"
printf '%s  %s\n' "$PROOF_ARTIFACT_DIGEST" "$ZIP" | sha256sum --check --strict
unzip -q "$ZIP" -d "$PROOF_DIR"
python3 - "$PROOF_DIR/issue1396-proof.json" "$PROOF_DIR/issue1396-liquid20-preflight.json" "$PROOF_DIR/issue1396-proof-activation.json" "$IMPLEMENTATION_SHA" "$PROOF_PAPER_IMAGE_DIGEST" "$EXPECTED_CANDIDATE_MANIFEST_SHA256" <<'PY'
import json,re,sys
proof,pre,act=[json.load(open(x,encoding='utf-8')) for x in sys.argv[1:4]]; impl,image,manifest=sys.argv[4:7]
zero={'protected_holdout_accessed':False,'automatic_promotion_enabled':False,'trading_credentials_present':False,'order_adapter_present':False,'execution_enabled':False,'orders_submitted':0,'live_capital_authorized':False}
if proof.get('result')!='PASS' or proof.get('implementation_sha')!=impl or proof.get('image_digest')!=image: raise SystemExit('r13 proof identity mismatch')
if proof.get('observation_count')!=5 or proof.get('telemetry_record_count')!=5 or proof.get('successful_outcomes')!=5 or proof.get('fresh_source_ratio')!='1' or proof.get('runtime_health')!='healthy': raise SystemExit('r13 proof acceptance mismatch')
if proof.get('maximum_gap_ms',10**18)>1_800_000: raise SystemExit('r13 proof gap invalid')
for k,v in zero.items():
    if proof.get(k)!=v: raise SystemExit(f'r13 proof authority mismatch: {k}')
g=proof.get('generation_health')
if not isinstance(g,list) or len(g)!=5 or [x.get('generation') for x in g]!=[1,2,3,4,5]: raise SystemExit('r13 generation set mismatch')
expected=['binance-usdm','bybit-linear','okx-swap']
for row in g:
    if row.get('health')!='healthy' or sorted(x.get('source') for x in row.get('sources',[]))!=expected: raise SystemExit('r13 generation health mismatch')
    if any(not isinstance(x.get('age_ms'),int) or x['age_ms']>300000 for x in row['sources']): raise SystemExit('r13 generation source stale')
if pre.get('result')!='PASS' or sorted(x.get('source') for x in pre.get('sources',[]))!=expected: raise SystemExit('r13 preflight source mismatch')
if any(x.get('health')!='healthy' or x.get('coverage_available') is not True or x.get('age_ms',10**18)>300000 for x in pre['sources']): raise SystemExit('r13 preflight health mismatch')
if act.get('candidate_manifest_sha256')!=manifest or act.get('execution_enabled') is not False or act.get('live_capital_authorized') is not False or act.get('order_adapter_present') is not False or act.get('orders_submitted')!=0: raise SystemExit('r13 activation authority mismatch')
if not re.fullmatch(r'[0-9a-f]{64}',proof.get('binding_id','')) or not re.fullmatch(r'[0-9a-f]{64}',proof.get('run_id','')): raise SystemExit('r13 binding identity invalid')
PY

log "verify exact proven PAPER image and current Liquid20"
if ! docker image inspect "$PAPER_IMAGE" >/dev/null 2>&1; then
  docker build --pull --file deploy/synology/wickhunter-paper-runtime/Dockerfile \
    --build-arg "OPERATOR_COMMIT=$IMPLEMENTATION_SHA" --label "org.opencontainers.image.revision=$IMPLEMENTATION_SHA" --tag "$PAPER_IMAGE" .
fi
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$PAPER_IMAGE")" == "$IMPLEMENTATION_SHA" ]]
[[ "$(docker image inspect --format '{{json .Config.Entrypoint}}' "$PAPER_IMAGE")" == '["python","-m","ai_platform.wickhunter.candidate_paper_runtime_parity_supervisor"]' ]]
image_id="$(docker image inspect --format '{{.Id}}' "$PAPER_IMAGE")"
[[ "$image_id" == "sha256:$PROOF_PAPER_IMAGE_DIGEST" ]]
PAPER_IMAGE_DIGEST="${image_id#sha256:}"; export PAPER_IMAGE_DIGEST
reader_gid="$(docker run --rm --read-only --entrypoint stat --mount "type=bind,src=$LIQUID20_LIVE_HOST,dst=/runtime/liquid20,readonly" "$PAPER_IMAGE" -c %g /runtime/liquid20)"
[[ "$reader_gid" =~ ^[0-9]+$ ]]; LIQUID20_READER_GID="$reader_gid"; export LIQUID20_READER_GID

docker run --rm --interactive --user 65532:65532 --group-add "$LIQUID20_READER_GID" --read-only --network none --cap-drop ALL --security-opt no-new-privileges:true \
  --mount "type=bind,src=$LIQUID20_LIVE_HOST,dst=/runtime/liquid20,readonly" --entrypoint python "$PAPER_IMAGE" - <<'PY' > "$EVIDENCE/current-liquid20.json"
import json,time
from pathlib import Path
from ai_platform.wickhunter.candidate_paper_runtime_operator import load_liquid20_snapshot
now=time.time_ns()//1_000_000;s=load_liquid20_snapshot(Path('/runtime/liquid20'),now_ms=now,maximum_age_ms=300000)
rows=[{'source':x.source,'health':x.health.value,'coverage_available':x.coverage_available,'age_ms':None if x.last_received_at_ms is None else now-x.last_received_at_ms} for x in s.source_states]
expected=['binance-usdm','bybit-linear','okx-swap']
if sorted(x['source'] for x in rows)!=expected or any(x['health']!='healthy' or x['coverage_available'] is not True or x['age_ms'] is None or x['age_ms']>300000 for x in rows): raise SystemExit('current Liquid20 is not 3/3 healthy')
print(json.dumps({'result':'PASS','snapshot_id':s.snapshot_id,'sources':rows},sort_keys=True))
PY

log "capture physically stopped legacy SHADOW"
[[ "$(docker inspect --format '{{.State.Running}}' liquid20-live)" == "true" ]]
mapfile -t old_ids < <(docker ps -aq --no-trunc --filter "label=com.docker.compose.project=$OLD_SHADOW_PROJECT" --filter "label=com.docker.compose.service=$OLD_SHADOW_SERVICE" | sed '/^$/d')
[[ ${#old_ids[@]} -eq 1 ]]
OLD_SHADOW_CONTAINER_ID="${old_ids[0]}"; export OLD_SHADOW_CONTAINER_ID
docker inspect "$OLD_SHADOW_CONTAINER_ID" > "$EVIDENCE/old-shadow-inspect.json"
python3 - "$EVIDENCE/old-shadow-inspect.json" > "$EVIDENCE/old-shadow.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))[0]; labels=(p.get('Config') or {}).get('Labels') or {}; host=p.get('HostConfig') or {}; state=p.get('State') or {}
if labels.get('com.docker.compose.project')!='wickhunter-production-research-runtime' or labels.get('com.docker.compose.service')!='wickhunter-production-research-runtime': raise SystemExit('old SHADOW labels mismatch')
if (p.get('Config') or {}).get('User')!='65531:65531': raise SystemExit('old SHADOW user mismatch')
if state.get('Running') is not False or state.get('Status')!='exited' or state.get('OOMKilled') is not False: raise SystemExit('old SHADOW is not authoritative stopped runtime')
if host.get('ReadonlyRootfs') is not True or host.get('Privileged') is not False or 'ALL' not in (host.get('CapDrop') or []): raise SystemExit('old SHADOW hardening mismatch')
if not any('no-new-privileges' in x for x in (host.get('SecurityOpt') or [])): raise SystemExit('old SHADOW no-new-privileges missing')
image=p.get('Image','')
if not image.startswith('sha256:') or len(image)!=71: raise SystemExit('old SHADOW image identity invalid')
print(json.dumps({'container_id':p['Id'],'image_digest':image[7:],'exit_code':state.get('ExitCode'),'oom_killed':False,'running':False,'docker_state':'exited'},sort_keys=True))
PY
OLD_SHADOW_IMAGE_DIGEST="$(json_value "$EVIDENCE/old-shadow.json" image_digest)"; export OLD_SHADOW_IMAGE_DIGEST

log "install pinned Portal supply-chain tools"
install -d "$RUNNER_TEMP/portal-tools"
curl --fail --location --proto '=https' --tlsv1.2 "https://github.com/anchore/syft/releases/download/v${SYFT_VERSION}/syft_${SYFT_VERSION}_linux_amd64.tar.gz" -o "$RUNNER_TEMP/syft.tar.gz"
echo "${SYFT_LINUX_AMD64_SHA256}  $RUNNER_TEMP/syft.tar.gz" | sha256sum --check --strict
tar -xzf "$RUNNER_TEMP/syft.tar.gz" -C "$RUNNER_TEMP/portal-tools" syft
curl --fail --location --proto '=https' --tlsv1.2 "https://github.com/anchore/grype/releases/download/v${GRYPE_VERSION}/grype_${GRYPE_VERSION}_linux_amd64.tar.gz" -o "$RUNNER_TEMP/grype.tar.gz"
echo "${GRYPE_LINUX_AMD64_SHA256}  $RUNNER_TEMP/grype.tar.gz" | sha256sum --check --strict
tar -xzf "$RUNNER_TEMP/grype.tar.gz" -C "$RUNNER_TEMP/portal-tools" grype
export PATH="$RUNNER_TEMP/portal-tools:$PATH"

log "build approve and deploy exact current Portal"
PORTAL_EVIDENCE="$EVIDENCE/portal-supply-chain"; APPROVAL="$PORTAL_EVIDENCE/approval.json"; REPORT="$EVIDENCE/portal-deploy-report.json"; DEPLOY_REQUEST="deploy/synology/portal-oidc/run-requests/public-oidc-20260801-v1.json"
mkdir -p "$PORTAL_EVIDENCE" "$(dirname "$DEPLOY_REQUEST")"
python3 tools/agents/portal_supply_chain.py build-verify --repository "$GITHUB_WORKSPACE" --source-sha "$IMPLEMENTATION_SHA" --output-dir "$PORTAL_EVIDENCE" --approval "$APPROVAL"
python3 tools/agents/portal_supply_chain.py verify-approval --approval "$APPROVAL" --expected-source-sha "$IMPLEMENTATION_SHA"
python3 - "$DEPLOY_REQUEST" "$IMPLEMENTATION_SHA" <<'PY'
import json,pathlib,sys
p={'request_id':'portal-authentik-public-oidc-20260801-v1','environment':'synology-staging','runner':'freqtrade-staging','implementation_sha':sys.argv[2],'portal_origin':'https://quant.molehill.cloud','authentik_origin':'https://auth.molehill.cloud','identity_transport':'https','identity_fixture_mode':'disabled','bootstrap_membership_authorized':False,'dry_run_required':True,'public_ingress_authorized':True,'live_capital_authorized':False,'restore_authorized':False,'secret_values_in_request':False}
pathlib.Path(sys.argv[1]).write_text(json.dumps(p,sort_keys=True),encoding='utf-8')
PY
python3 deploy/synology/portal-oidc/prepare_host_state.py --repository "$GITHUB_WORKSPACE"
python3 tools/agents/portal_supply_chain.py deploy-approved --approved-images "$APPROVAL" --repository "$GITHUB_WORKSPACE" --request "$DEPLOY_REQUEST" --expected-repository-sha "$IMPLEMENTATION_SHA" --report "$REPORT"
python3 - "$REPORT" "$IMPLEMENTATION_SHA" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
if p.get('status')!='success' or p.get('implementation_sha')!=sys.argv[2] or p.get('live_capital_authorized') is not False: raise SystemExit('exact Portal deploy failed')
PY
for c in "$PORTAL_CONTROL_CONTAINER" "$PORTAL_WEB_CONTAINER"; do
  image="$(docker inspect --format '{{.Image}}' "$c")"
  [[ "$image" =~ ^sha256:[0-9a-f]{64}$ ]]
  [[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image")" == "$IMPLEMENTATION_SHA" ]]
  [[ "$(docker inspect --format '{{.State.Running}}' "$c")" == "true" ]]
done
docker cp "$REQUEST_HELPER" "$PORTAL_CONTROL_CONTAINER:/tmp/issue1396_terminal_transition_v2.py"
docker exec "$PORTAL_CONTROL_CONTAINER" python -m py_compile /tmp/issue1396_terminal_transition_v2.py
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396_terminal_transition_v2.py baseline-stopped --old-container-id "$OLD_SHADOW_CONTAINER_ID" --old-image-digest "$OLD_SHADOW_IMAGE_DIGEST" > "$EVIDENCE/baseline.json"

log "create persistent PAPER activation and initialized journal"
state_name="issue1396-production-paper-v3-${IMPLEMENTATION_SHA:0:12}-${GITHUB_RUN_ID}"
activation_name="wickhunter-production-paper-v3-${IMPLEMENTATION_SHA:0:12}-${GITHUB_RUN_ID}"
candidate_runner="$RUNNER_STATE_ROOT/wickhunter-candidate-materialization/packages/$CANDIDATE_PACKAGE_NAME"
candidate_host="$HOST_STATE_ROOT/wickhunter-candidate-materialization/packages/$CANDIDATE_PACKAGE_NAME"
state_runner="$RUNNER_STATE_ROOT/wickhunter-paper-runtime/$state_name"; state_host="$HOST_STATE_ROOT/wickhunter-paper-runtime/$state_name"
[[ -d "$candidate_runner" && ! -L "$candidate_runner" && ! -e "$state_runner" && ! -L "$state_runner" ]]
install -d -m 0750 -o 65532 -g 65532 "$state_runner" "$state_runner/activations" "$state_runner/journals" "$state_runner/operator" "$state_runner/operator/$activation_name"
docker run --rm --interactive --user 65532:65532 --read-only --network none --cap-drop ALL --security-opt no-new-privileges:true \
  --mount "type=bind,src=$candidate_host,dst=/runtime/candidate,readonly" --mount "type=bind,src=$state_host,dst=/runtime/state" \
  --env "ACTIVATION_NAME=$activation_name" --env EXPECTED_CANDIDATE_MANIFEST_SHA256 --env IMPLEMENTATION_SHA --env PAPER_IMAGE_DIGEST \
  --entrypoint python "$PAPER_IMAGE" - <<'PY' > "$EVIDENCE/production-activation.json"
import json,os,time
from pathlib import Path
from ai_platform.wickhunter.candidate_paper_runtime_operator import _runtime_policy
from ai_platform.wickhunter.candidate_paper_runtime_service import CandidatePaperRuntimeService
from ai_platform.wickhunter.candidate_runtime_activation import activate_verified_runtime_candidate
from ai_platform.wickhunter.candidate_runtime_binding import build_candidate_paper_runtime_binding
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import BotMode
from ai_platform.wickhunter.runtime_mode import ManagedRuntimeModeRequest,resolve_managed_runtime_mode
root=Path('/runtime/state'); activation=root/'activations'/os.environ['ACTIVATION_NAME']; journal=root/'journals'/os.environ['ACTIVATION_NAME']
result=activate_verified_runtime_candidate(candidate_root=Path('/runtime/candidate'),activation_root=activation,created_at_ms=time.time_ns()//1_000_000,bot_instance='wickhunter-production-paper',mode=BotMode.PAPER,wh08_consumer_version='wickhunter-portal-consumer-v1',window_duration_ms=31_536_000_000)
if result.identity.manifest_sha256!=os.environ['EXPECTED_CANDIDATE_MANIFEST_SHA256']: raise SystemExit('candidate manifest mismatch')
binding=build_candidate_paper_runtime_binding(candidate_root=Path('/runtime/candidate'),activation_root=activation)
service=CandidatePaperRuntimeService(binding=binding,runtime_policy=_runtime_policy(),journal_root=journal)
if service.journal.latest_state() is not None: raise SystemExit('production PAPER journal is not fresh')
auth={'schema_version':'wickhunter-issue1396-paper-authorization-v3','authorization_id':'issue-1396-production-paper-owner-directed-v3','run_id':binding.request.run_id,'binding_id':binding.binding_id,'candidate_package_id':result.identity.package_id,'candidate_manifest_sha256':result.identity.manifest_sha256,'live_capital_authorized':False,'execution_enabled':False}
digest=canonical_sha256(auth)
r=resolve_managed_runtime_mode(ManagedRuntimeModeRequest(mode=BotMode.PAPER,paper_activation_authorized=True,paper_authorization_id=auth['authorization_id'],paper_authorization_digest=digest,paper_candidate_package_id=result.identity.package_id,paper_candidate_manifest_sha256=result.identity.manifest_sha256))
zero={'trading_credentials_present':r.trading_credentials_present,'order_adapter_present':r.order_adapter_present,'execution_enabled':r.execution_enabled,'orders_submitted':r.orders_submitted,'live_capital_authorized':r.live_capital_authorized,'automatic_promotion_enabled':r.automatic_promotion_enabled}
if zero!={'trading_credentials_present':False,'order_adapter_present':False,'execution_enabled':False,'orders_submitted':0,'live_capital_authorized':False,'automatic_promotion_enabled':False}: raise SystemExit('PAPER authority mismatch')
config={'schema_version':'issue1396-production-paper-runtime-config-v3','implementation_sha':os.environ['IMPLEMENTATION_SHA'],'runtime_image_digest':os.environ['PAPER_IMAGE_DIGEST'],'run_id':binding.request.run_id,'binding_id':binding.binding_id,'candidate_package_id':result.identity.package_id,'candidate_manifest_sha256':result.identity.manifest_sha256,'public_market_base_url':'https://fapi.binance.com','poll_seconds':120,'maximum_source_age_ms':300000,'model_drift':'healthy','data_drift':'healthy','circuit_breaker_active':False,**zero}
print(json.dumps({'run_id':binding.request.run_id,'binding_id':binding.binding_id,'candidate_package_id':result.identity.package_id,'candidate_manifest_sha256':result.identity.manifest_sha256,'authorization_id':auth['authorization_id'],'authorization_digest':digest,'config_digest':canonical_sha256(config),**zero},sort_keys=True))
PY
activation_runner="$state_runner/activations/$activation_name"; journal_runner="$state_runner/journals/$activation_name"; operator_runner="$state_runner/operator/$activation_name"
[[ -d "$activation_runner" && -d "$journal_runner" && -d "$operator_runner" ]]
find "$activation_runner" -type d -exec chmod 0550 {} +; find "$activation_runner" -type f -exec chmod 0440 {} +
find "$journal_runner" -type d -exec chmod 0750 {} +; find "$journal_runner" -type f -exec chmod 0640 {} +
chown -R 65532:65532 "$journal_runner" "$operator_runner"
PAPER_RUN_ID="$(json_value "$EVIDENCE/production-activation.json" run_id)"; PAPER_BINDING_ID="$(json_value "$EVIDENCE/production-activation.json" binding_id)"; PAPER_AUTHORIZATION_ID="$(json_value "$EVIDENCE/production-activation.json" authorization_id)"; PAPER_AUTHORIZATION_DIGEST="$(json_value "$EVIDENCE/production-activation.json" authorization_digest)"; PAPER_CONFIG_DIGEST="$(json_value "$EVIDENCE/production-activation.json" config_digest)"; PAPER_CANDIDATE_PACKAGE_ID="$(json_value "$EVIDENCE/production-activation.json" candidate_package_id)"; PAPER_CANDIDATE_MANIFEST="$(json_value "$EVIDENCE/production-activation.json" candidate_manifest_sha256)"
export PAPER_RUN_ID PAPER_BINDING_ID PAPER_AUTHORIZATION_ID PAPER_AUTHORIZATION_DIGEST PAPER_CONFIG_DIGEST PAPER_CANDIDATE_PACKAGE_ID PAPER_CANDIDATE_MANIFEST
PROD_STATE_RUNNER="$state_runner"; PROD_ACTIVATION_HOST="$state_host/activations/$activation_name"; PROD_JOURNAL_HOST="$state_host/journals/$activation_name"; PROD_OPERATOR_HOST="$state_host/operator/$activation_name"
export PROD_STATE_RUNNER PROD_ACTIVATION_HOST PROD_JOURNAL_HOST PROD_OPERATOR_HOST

log "start persistent PAPER and prove 3/3 healthy before desired mutation"
! docker container inspect "$PROD_PAPER_CONTAINER" >/dev/null 2>&1
! docker container inspect "$PROD_GATEWAY_CONTAINER" >/dev/null 2>&1
! docker network inspect "$PROD_INTERNAL_NETWORK" >/dev/null 2>&1
docker network create --internal "$PROD_INTERNAL_NETWORK" >/dev/null
gateway_code="$(cat <<'PY'
import socket,socketserver,threading
TARGET=('fapi.binance.com',443)
class S(socketserver.ThreadingMixIn,socketserver.TCPServer): daemon_threads=True; allow_reuse_address=True
class H(socketserver.BaseRequestHandler):
    @staticmethod
    def pump(a,b):
        try:
            while True:
                x=a.recv(65536)
                if not x:return
                b.sendall(x)
        except OSError:return
    def handle(self):
        r=socket.create_connection(TARGET,timeout=15)
        try:
            t=threading.Thread(target=self.pump,args=(self.request,r),daemon=True);t.start();self.pump(r,self.request);t.join(timeout=5)
        finally:r.close()
S(('0.0.0.0',443),H).serve_forever()
PY
)"
docker create --name "$PROD_GATEWAY_CONTAINER" --init --user 0:0 --read-only --restart unless-stopped --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777 --cap-drop ALL --cap-add NET_BIND_SERVICE --security-opt no-new-privileges:true --memory 256m --network bridge --label "io.freqtrade.wickhunter.issue=1396" --label "io.freqtrade.wickhunter.role=production-paper-public-market-egress" --label "io.freqtrade.wickhunter.target=fapi.binance.com:443" --label "org.opencontainers.image.revision=$IMPLEMENTATION_SHA" --entrypoint python "$PAPER_IMAGE" -c "$gateway_code" >/dev/null
docker network connect "$PROD_INTERNAL_NETWORK" "$PROD_GATEWAY_CONTAINER"; docker start "$PROD_GATEWAY_CONTAINER" >/dev/null; sleep 2
gateway_ip="$(docker inspect --format "{{with index .NetworkSettings.Networks \"$PROD_INTERNAL_NETWORK\"}}{{.IPAddress}}{{end}}" "$PROD_GATEWAY_CONTAINER")"; [[ "$gateway_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
docker create --name "$PROD_PAPER_CONTAINER" --restart unless-stopped --label "io.freqtrade.wickhunter.issue=1396" --label "io.freqtrade.wickhunter.bot=wickhunter" --label "io.freqtrade.wickhunter.mode=paper" --label "io.freqtrade.wickhunter.binding=$PAPER_BINDING_ID" --label "org.opencontainers.image.revision=$IMPLEMENTATION_SHA" --user 65532:65532 --group-add "$LIQUID20_READER_GID" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777 --cap-drop ALL --security-opt no-new-privileges:true --memory 2g --cpus 2.0 --pids-limit 256 --network "$PROD_INTERNAL_NETWORK" --add-host "fapi.binance.com:$gateway_ip" --env "OPERATOR_COMMIT=$IMPLEMENTATION_SHA" --env HEALTH_PATH=/runtime/operator/health.json --env HEALTH_MAX_AGE_SECONDS=1200 --env HTTP_PROXY= --env HTTPS_PROXY= --env ALL_PROXY= --env http_proxy= --env https_proxy= --env all_proxy= --mount "type=bind,src=$candidate_host,dst=/runtime/candidate,readonly" --mount "type=bind,src=$PROD_ACTIVATION_HOST,dst=/runtime/activation,readonly" --mount "type=bind,src=$LIQUID20_LIVE_HOST,dst=/runtime/liquid20,readonly" --mount "type=bind,src=$PROD_JOURNAL_HOST,dst=/runtime/journal" --mount "type=bind,src=$PROD_OPERATOR_HOST,dst=/runtime/operator" --health-cmd 'python /app/deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py' --health-interval 30s --health-timeout 10s --health-retries 3 --health-start-period 120s "$PAPER_IMAGE" --candidate-root /runtime/candidate --activation-root /runtime/activation --journal-root /runtime/journal --liquid20-root /runtime/liquid20 --health-root /runtime/operator --operator-commit "$IMPLEMENTATION_SHA" --public-market-base-url https://fapi.binance.com --poll-seconds 120 --maximum-source-age-ms 300000 --model-drift healthy --data-drift healthy --circuit-breaker-active false >/dev/null
docker start "$PROD_PAPER_CONTAINER" >/dev/null
for _ in $(seq 1 90); do h="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$PROD_PAPER_CONTAINER")"; [[ "$h" == "healthy" ]] && break; [[ "$h" =~ ^(unhealthy|exited|dead)$ ]] && { docker logs "$PROD_PAPER_CONTAINER"; exit 1; }; sleep 10; done
[[ "$(docker inspect --format '{{.State.Health.Status}}' "$PROD_PAPER_CONTAINER")" == "healthy" ]]
docker exec "$PROD_PAPER_CONTAINER" python /app/deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py
docker exec -i "$PROD_PAPER_CONTAINER" python - <<'PY'
import socket
s=socket.socket();s.settimeout(2);rc=s.connect_ex(('1.1.1.1',443));s.close()
if rc==0: raise SystemExit('persistent PAPER has forbidden direct external egress')
PY
docker exec "$PROD_PAPER_CONTAINER" python -c "import json,urllib.request; o=urllib.request.build_opener(urllib.request.ProxyHandler({})); r=o.open('https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT',timeout=20); json.loads(r.read().decode()); r.close()"
PROD_PAPER_CONTAINER_ID="$(docker inspect --format '{{.Id}}' "$PROD_PAPER_CONTAINER")"; export PROD_PAPER_CONTAINER_ID
[[ "$(docker inspect --format '{{.Image}}' "$PROD_PAPER_CONTAINER")" == "sha256:$PAPER_IMAGE_DIGEST" ]]
cp "$PROD_OPERATOR_HOST/health.json" "$EVIDENCE/production-health.json"
validate_generation_snapshot "$EVIDENCE/production-health.json" "$PROD_JOURNAL_HOST" "$EVIDENCE/production-generation-health.json"

log "author desired PAPER, persist stopped SHADOW proof, reconcile observed PAPER"
docker cp "$EVIDENCE/production-health.json" "$PORTAL_CONTROL_CONTAINER:/tmp/issue1396-production-health.json"
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396_terminal_transition_v2.py author-paper --implementation-sha "$IMPLEMENTATION_SHA" --image-digest "$PAPER_IMAGE_DIGEST" --config-digest "$PAPER_CONFIG_DIGEST" --authorization-id "$PAPER_AUTHORIZATION_ID" --authorization-digest "$PAPER_AUTHORIZATION_DIGEST" --run-id "$PAPER_RUN_ID" --binding-id "$PAPER_BINDING_ID" --candidate-package-id "$PAPER_CANDIDATE_PACKAGE_ID" --candidate-manifest "$PAPER_CANDIDATE_MANIFEST" > "$EVIDENCE/desired-paper.json"
OLD_GENERATION_ID="$(json_value "$EVIDENCE/desired-paper.json" old_generation.generation_id)"; PAPER_GENERATION_ID="$(json_value "$EVIDENCE/desired-paper.json" paper_generation.generation_id)"; export OLD_GENERATION_ID PAPER_GENERATION_ID
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396_terminal_transition_v2.py record-stop --generation-id "$OLD_GENERATION_ID" --runtime-instance-id "$OLD_SHADOW_CONTAINER_ID" --evidence-kind issue1396-physical-stopped-shadow-v3 > "$EVIDENCE/shadow-stopped.json"
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396_terminal_transition_v2.py reconcile-running --generation-id "$PAPER_GENERATION_ID" --runtime-instance-id "$PROD_PAPER_CONTAINER_ID" --health-json /tmp/issue1396-production-health.json --source-version "$IMPLEMENTATION_SHA" --evidence-kind issue1396-production-paper-running-v3 > "$EVIDENCE/paper-reconciled.json"

log "prove exact-generation restart and second healthy reconciliation"
before_generation="$(json_value "$EVIDENCE/production-health.json" generation)"; before_checked="$(json_value "$EVIDENCE/production-health.json" checked_at_ms)"; same_id="$PROD_PAPER_CONTAINER_ID"
docker restart "$PROD_PAPER_CONTAINER" >/dev/null
for _ in $(seq 1 90); do h="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$PROD_PAPER_CONTAINER")"; if [[ "$h" == "healthy" && -f "$PROD_OPERATOR_HOST/health.json" ]]; then g="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["generation"])' "$PROD_OPERATOR_HOST/health.json")"; c="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["checked_at_ms"])' "$PROD_OPERATOR_HOST/health.json")"; if (( g > before_generation && c > before_checked )); then break; fi; fi; [[ "$h" =~ ^(unhealthy|exited|dead)$ ]] && { docker logs "$PROD_PAPER_CONTAINER"; exit 1; }; sleep 10; done
[[ "$(docker inspect --format '{{.Id}}' "$PROD_PAPER_CONTAINER")" == "$same_id" ]]
[[ "$(docker inspect --format '{{.Image}}' "$PROD_PAPER_CONTAINER")" == "sha256:$PAPER_IMAGE_DIGEST" ]]
[[ "$(docker inspect --format '{{.State.Health.Status}}' "$PROD_PAPER_CONTAINER")" == "healthy" ]]
docker exec "$PROD_PAPER_CONTAINER" python /app/deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py
cp "$PROD_OPERATOR_HOST/health.json" "$EVIDENCE/production-health-after-restart.json"
validate_generation_snapshot "$EVIDENCE/production-health-after-restart.json" "$PROD_JOURNAL_HOST" "$EVIDENCE/restart-generation-health.json"
after_generation="$(json_value "$EVIDENCE/production-health-after-restart.json" generation)"; (( after_generation > before_generation ))
python3 - "$EVIDENCE/restart-proof.json" "$same_id" "$before_generation" "$after_generation" "$PAPER_IMAGE_DIGEST" <<'PY'
import json,pathlib,sys
path,paper,before,after,image=sys.argv[1:]
p={'result':'PASS','same_runtime_instance':True,'runtime_instance_id':paper,'before_generation':int(before),'after_generation':int(after),'paper_image_digest':image}
pathlib.Path(path).write_text(json.dumps(p,sort_keys=True)+'\n',encoding='utf-8')
PY
docker cp "$EVIDENCE/production-health-after-restart.json" "$PORTAL_CONTROL_CONTAINER:/tmp/issue1396-production-health-after-restart.json"
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396_terminal_transition_v2.py reconcile-running --generation-id "$PAPER_GENERATION_ID" --runtime-instance-id "$PROD_PAPER_CONTAINER_ID" --health-json /tmp/issue1396-production-health-after-restart.json --source-version "$IMPLEMENTATION_SHA" --evidence-kind issue1396-production-paper-restart-v3 > "$EVIDENCE/paper-restart-observation.json"

log "final Portal API truth"
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396_terminal_transition_v2.py final-api --expected-mode paper > "$EVIDENCE/production-api.json"
python3 - "$EVIDENCE/production-api.json" "$PROOF_DIR/issue1396-proof.json" "$EVIDENCE/production-health-after-restart.json" "$EVIDENCE/restart-proof.json" "$EVIDENCE/old-shadow.json" "$EVIDENCE/production-activation.json" "$PROOF_ARTIFACT_ID" "$PROOF_ARTIFACT_DIGEST" "$IMPLEMENTATION_SHA" "$PAPER_IMAGE_DIGEST" "$PAPER_CONFIG_DIGEST" "$PROD_PAPER_CONTAINER_ID" > "$EVIDENCE/production-closeout.json" <<'PY'
import json,sys
api,proof,health,restart,old,activation=[json.load(open(x,encoding='utf-8')) for x in sys.argv[1:7]]
artifact_id,artifact_digest,implementation,image,config,paper_id=sys.argv[7:13]
truth=api['truth'];bot=api['bots'][0]
zero={'protected_holdout_accessed':False,'automatic_promotion_enabled':False,'trading_credentials_present':False,'order_adapter_present':False,'execution_enabled':False,'orders_submitted':0,'live_capital_authorized':False}
if truth['desired_generation']['generation_id']!=truth['observed_generation']['generation_id'] or truth['desired_generation']['managed_mode']!='paper' or truth['observed_generation']['managed_mode']!='paper' or truth['pending_rollout'] is not False: raise SystemExit('final API truth not converged PAPER')
if truth['desired_generation']['runtime_image_digest']!=image or truth['desired_generation']['normalized_runtime_config_digest']!=config: raise SystemExit('final generation identity mismatch')
if health.get('status')!='healthy' or health.get('runtime_health')!='healthy': raise SystemExit('final persistent PAPER unhealthy')
for k,v in zero.items():
    if health.get(k)!=v: raise SystemExit(f'final authority mismatch: {k}')
print(json.dumps({'result':'PASS','implementation_sha':implementation,'bot':bot,'truth':truth,'five_cycle_proof':proof,'proof_artifact':{'id':int(artifact_id),'sha256':artifact_digest},'paper_health':health,'restart':restart,'physical':{'paper_container_id':paper_id,'old_shadow_container_id':old['container_id'],'paper_image_digest':image,'paper_config_digest':config},'activation':activation,'zero_authority':zero},sort_keys=True))
PY
D="$(json_value "$EVIDENCE/production-closeout.json" truth.desired_generation.generation_id)"; O="$(json_value "$EVIDENCE/production-closeout.json" truth.observed_generation.generation_id)"; [[ "$D" == "$O" ]]
base64 -w0 "$EVIDENCE/production-closeout.json" > "$EVIDENCE/production-closeout.b64"
{
  echo "production_payload_b64=$(cat "$EVIDENCE/production-closeout.b64")"
  echo "desired_generation_id=$D"
  echo "observed_generation_id=$O"
  echo "paper_container_id=$PROD_PAPER_CONTAINER_ID"
  echo "old_shadow_container_id=$OLD_SHADOW_CONTAINER_ID"
  echo "paper_image_digest=$PAPER_IMAGE_DIGEST"
  echo "paper_config_digest=$PAPER_CONFIG_DIGEST"
} >> "$GITHUB_OUTPUT"

log "terminal transition job passed"
