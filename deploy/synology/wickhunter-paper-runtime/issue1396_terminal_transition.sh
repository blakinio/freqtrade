#!/usr/bin/env bash
set -euo pipefail
umask 027

: "${IMPLEMENTATION_SHA:?}"
: "${PROOF_RUN_ID:?}"
: "${PROOF_ARTIFACT_ID:?}"
: "${PROOF_ARTIFACT_DIGEST:?}"
: "${PROOF_RUN_HEAD_SHA:?}"
: "${PROOF_PAPER_IMAGE_DIGEST:?}"
: "${GITHUB_TOKEN:?}"
: "${GITHUB_REPOSITORY:?}"
: "${GITHUB_WORKSPACE:?}"
: "${GITHUB_OUTPUT:?}"
: "${RUNNER_TEMP:?}"

CANDIDATE_PACKAGE_NAME="wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d"
EXPECTED_CANDIDATE_MANIFEST_SHA256="9f5ba852e33915678ca085c2eeafbf526457a079ba8f6f2fb7c1097f1d20ab79"
RUNNER_STATE_ROOT="/var/lib/freqtrade-staging-state"
HOST_STATE_ROOT="/volume1/docker/freqtrade/state"
LIQUID20_LIVE_HOST="/volume1/docker/freqtrade-liquidations/data/live"
AUTHENTIK_PROJECT="portal-authentik-local-test"
AUTHENTIK_ENV="/var/lib/freqtrade-staging-state/portal-authentik-local-test/runtime.env"
PORTAL_CONTROL_CONTAINER="freqtrade-portal-control-plane"
PORTAL_WEB_CONTAINER="freqtrade-portal-staging"
OLD_SHADOW_PROJECT="wickhunter-production-research-runtime"
OLD_SHADOW_SERVICE="wickhunter-production-research-runtime"
OLD_SHADOW_NETWORK="wickhunter-production-research-runtime_wickhunter-public-market-egress"
PROD_PAPER_CONTAINER="wickhunter-production-paper-runtime"
PROD_GATEWAY_CONTAINER="wickhunter-production-paper-egress"
PROD_INTERNAL_NETWORK="wickhunter-production-paper-internal"
PROOF_IMAGE_TAG="local/wickhunter-paper-runtime:issue1396-proof-${PROOF_RUN_ID}"
PAPER_IMAGE="local/wickhunter-paper-runtime:issue1396-terminal-paper"
SYFT_VERSION="1.50.0"
SYFT_SHA256="bf7b29ff57f06da30918266a0e1c2885a8f99784798d1bdb1628886aa015d788"
GRYPE_VERSION="0.116.1"
GRYPE_SHA256="0122df7b655981abe547ad3d2190d65551dac6a2bfc80b4dc2a989b5d0587458"
EVIDENCE="$RUNNER_TEMP/issue1396-terminal-transition"
mkdir -p "$EVIDENCE/proof" "$EVIDENCE/recovery"

log() { printf '[issue1396-transition] %s\n' "$*"; }

json_value() {
  python3 - "$1" "$2" <<'PY'
import json,sys
value=json.load(open(sys.argv[1],encoding='utf-8'))
for part in sys.argv[2].split('.'):
    value=value[part]
print(value)
PY
}

remove_task_paper() {
  docker rm -f "$PROD_PAPER_CONTAINER" "$PROD_GATEWAY_CONTAINER" >/dev/null 2>&1 || true
  docker network rm "$PROD_INTERNAL_NETWORK" >/dev/null 2>&1 || true
  if [[ -n "${PROD_STATE_RUNNER:-}" && -e "${PROD_STATE_RUNNER:-}" ]]; then
    case "$PROD_STATE_RUNNER" in
      "$RUNNER_STATE_ROOT"/wickhunter-paper-runtime/issue1396-production-paper-*)
        rm -rf --one-file-system "$PROD_STATE_RUNNER"
        ;;
    esac
  fi
}

recover() {
  set +e
  if [[ "${CANONICAL_AUTHOR_STARTED:-false}" != "true" ]]; then
    remove_task_paper
    if [[ "${OLD_SHADOW_WAS_RUNNING:-false}" == "true" && -n "${OLD_SHADOW_CONTAINER_ID:-}" ]]; then
      docker start "$OLD_SHADOW_CONTAINER_ID" >/dev/null 2>&1 || true
    fi
    printf '%s\n' '{"result":"ROLLED_BACK_BEFORE_CANONICAL_AUTHOR"}' > "$EVIDENCE/recovery/result.json"
    return 0
  fi
  if [[ -n "${PROD_OPERATOR_HOST:-}" && -f "$PROD_OPERATOR_HOST/health.json" && -n "${PAPER_GENERATION_ID:-}" ]]; then
    cp "$PROD_OPERATOR_HOST/health.json" "$EVIDENCE/recovery/paper-health.json"
    docker cp "$EVIDENCE/recovery/paper-health.json" "$PORTAL_CONTROL_CONTAINER:/tmp/issue1396-recovery-health.json" >/dev/null 2>&1
    docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396-transition.py recover \
      --old-runtime-instance-id "$OLD_SHADOW_CONTAINER_ID" \
      --paper-runtime-instance-id "$PROD_PAPER_CONTAINER_ID" \
      --health-json /tmp/issue1396-recovery-health.json \
      --source-version "$IMPLEMENTATION_SHA" \
      --image-digest "$PROOF_PAPER_IMAGE_DIGEST" \
      --config-digest "$PAPER_CONFIG_DIGEST" > "$EVIDENCE/recovery/result.json" 2>&1 && return 0
  fi
  printf '%s\n' '{"result":"FAIL_CLOSED_MANUAL_RECONCILIATION_REQUIRED"}' > "$EVIDENCE/recovery/result.json"
  return 1
}

on_exit() {
  status=$?
  if [[ "$status" != "0" ]]; then recover || true; fi
}
trap on_exit EXIT

log "verify accepted 5/5 artifact metadata and preserved image"
[[ "$PROOF_RUN_HEAD_SHA" == "$IMPLEMENTATION_SHA" ]]
META="$EVIDENCE/proof-meta.json"
ZIP="$EVIDENCE/proof.zip"
curl --fail --silent --show-error --location \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$PROOF_ARTIFACT_ID" -o "$META"
python3 - "$META" "$PROOF_ARTIFACT_ID" "$PROOF_ARTIFACT_DIGEST" "$PROOF_RUN_ID" "$PROOF_RUN_HEAD_SHA" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8')); aid,digest,run,head=sys.argv[2:]
if str(p.get('id'))!=aid: raise SystemExit('artifact id mismatch')
if p.get('name')!=f'issue1396-paper-proof-r13-{run}': raise SystemExit('artifact name mismatch')
if p.get('expired') is not False: raise SystemExit('artifact expired')
if p.get('digest')!=f'sha256:{digest}': raise SystemExit('artifact digest mismatch')
w=p.get('workflow_run') or {}
if str(w.get('id'))!=run or w.get('head_sha')!=head: raise SystemExit('artifact workflow identity mismatch')
PY
curl --fail --silent --show-error --location \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$PROOF_ARTIFACT_ID/zip" -o "$ZIP"
printf '%s  %s\n' "$PROOF_ARTIFACT_DIGEST" "$ZIP" | sha256sum --check --strict
unzip -q "$ZIP" -d "$EVIDENCE/proof"
python3 - "$EVIDENCE/proof/issue1396-proof.json" "$EVIDENCE/proof/issue1396-liquid20.json" "$EVIDENCE/proof/issue1396-activation.json" "$IMPLEMENTATION_SHA" "$PROOF_PAPER_IMAGE_DIGEST" "$EXPECTED_CANDIDATE_MANIFEST_SHA256" <<'PY'
import json,sys
proof,liquid,activation=[json.load(open(x,encoding='utf-8')) for x in sys.argv[1:4]]
sha,image,manifest=sys.argv[4:]
zero={'protected_holdout_accessed':False,'automatic_promotion_enabled':False,'trading_credentials_present':False,'order_adapter_present':False,'execution_enabled':False,'orders_submitted':0,'live_capital_authorized':False}
if proof.get('result')!='PASS' or proof.get('implementation_sha')!=sha or proof.get('image_digest')!=image: raise SystemExit('proof identity mismatch')
if proof.get('observation_count')!=5 or proof.get('telemetry_record_count')!=5 or proof.get('successful_outcomes')!=5: raise SystemExit('proof not exact 5/5')
if float(proof.get('fresh_source_ratio',0))<0.99 or proof.get('runtime_health')!='healthy': raise SystemExit('proof health/freshness failed')
if [x.get('generation') for x in proof.get('generation_health',[])]!=[1,2,3,4,5]: raise SystemExit('proof generations mismatch')
for key,value in zero.items():
    if proof.get(key)!=value: raise SystemExit(f'proof authority mismatch: {key}')
expected=['binance-usdm','bybit-linear','okx-swap']
if liquid.get('result')!='PASS' or sorted(x.get('source') for x in liquid.get('sources',[]))!=expected: raise SystemExit('Liquid20 proof mismatch')
if activation.get('candidate_manifest_sha256')!=manifest: raise SystemExit('candidate manifest mismatch')
PY
[[ "$(docker image inspect --format '{{.Id}}' "$PROOF_IMAGE_TAG")" == "sha256:$PROOF_PAPER_IMAGE_DIGEST" ]]
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$PROOF_IMAGE_TAG")" == "$IMPLEMENTATION_SHA" ]]
[[ "$(docker image inspect --format '{{json .Config.Entrypoint}}' "$PROOF_IMAGE_TAG")" == '["python","-m","ai_platform.wickhunter.candidate_paper_runtime_parity_supervisor"]' ]]
docker tag "$PROOF_IMAGE_TAG" "$PAPER_IMAGE"

log "reverify current Liquid20 3/3 and Authentik precondition"
reader_gid="$(docker run --rm --read-only --entrypoint stat --mount "type=bind,src=$LIQUID20_LIVE_HOST,dst=/runtime/liquid20,readonly" "$PAPER_IMAGE" -c %g /runtime/liquid20)"
[[ "$reader_gid" =~ ^[0-9]+$ ]]; LIQUID20_READER_GID="$reader_gid"; export LIQUID20_READER_GID
docker run --rm -i --user 65532:65532 --group-add "$reader_gid" --read-only --network none --cap-drop ALL --security-opt no-new-privileges:true --mount "type=bind,src=$LIQUID20_LIVE_HOST,dst=/runtime/liquid20,readonly" --entrypoint python "$PAPER_IMAGE" - <<'PY' > "$EVIDENCE/current-liquid20.json"
import json,time
from pathlib import Path
from ai_platform.wickhunter.candidate_paper_runtime_operator import load_liquid20_snapshot
now=time.time_ns()//1_000_000; s=load_liquid20_snapshot(Path('/runtime/liquid20'),now_ms=now,maximum_age_ms=300000)
rows=[{'source':x.source,'health':x.health.value,'coverage_available':x.coverage_available,'age_ms':None if x.last_received_at_ms is None else now-x.last_received_at_ms} for x in s.source_states]
if sorted(x['source'] for x in rows)!=['binance-usdm','bybit-linear','okx-swap'] or any(x['health']!='healthy' or x['coverage_available'] is not True or x['age_ms'] is None or x['age_ms']>300000 for x in rows): raise SystemExit('current Liquid20 not 3/3 healthy')
print(json.dumps({'result':'PASS','snapshot_id':s.snapshot_id,'sources':rows},sort_keys=True))
PY
[[ -f "$AUTHENTIK_ENV" && ! -L "$AUTHENTIK_ENV" && "$(stat -c '%a' "$AUTHENTIK_ENV")" == "600" ]]
python3 deploy/synology/portal-authentik/validate.py --env-file "$AUTHENTIK_ENV" > "$EVIDENCE/authentik-validation.json"
compose=(docker compose --project-name "$AUTHENTIK_PROJECT" --env-file "$AUTHENTIK_ENV" -f deploy/synology/portal-authentik/compose.yml)
for service in postgresql server worker; do
  id="$("${compose[@]}" ps -q "$service")"; [[ -n "$id" ]]
  [[ "$(docker inspect --format '{{.State.Running}}' "$id")" == "true" ]]
  [[ "$(docker inspect --format '{{.State.Health.Status}}' "$id")" == "healthy" ]]
done
"${compose[@]}" exec -T server ak healthcheck
"${compose[@]}" exec -T worker ak healthcheck
python3 deploy/synology/portal-oidc/prepare_host_state.py --repository "$GITHUB_WORKSPACE"

log "deploy exact current Portal through approved-image supply chain"
install -d "$RUNNER_TEMP/portal-tools"
curl --fail --location --proto '=https' --tlsv1.2 "https://github.com/anchore/syft/releases/download/v${SYFT_VERSION}/syft_${SYFT_VERSION}_linux_amd64.tar.gz" -o "$RUNNER_TEMP/syft.tar.gz"
echo "${SYFT_SHA256}  $RUNNER_TEMP/syft.tar.gz" | sha256sum --check --strict
tar -xzf "$RUNNER_TEMP/syft.tar.gz" -C "$RUNNER_TEMP/portal-tools" syft
curl --fail --location --proto '=https' --tlsv1.2 "https://github.com/anchore/grype/releases/download/v${GRYPE_VERSION}/grype_${GRYPE_VERSION}_linux_amd64.tar.gz" -o "$RUNNER_TEMP/grype.tar.gz"
echo "${GRYPE_SHA256}  $RUNNER_TEMP/grype.tar.gz" | sha256sum --check --strict
tar -xzf "$RUNNER_TEMP/grype.tar.gz" -C "$RUNNER_TEMP/portal-tools" grype
export PATH="$RUNNER_TEMP/portal-tools:$PATH"
APPROVAL="$EVIDENCE/portal-approval.json"; REPORT="$EVIDENCE/portal-deploy-report.json"; DEPLOY_REQUEST="$GITHUB_WORKSPACE/deploy/synology/portal-oidc/run-requests/public-oidc-20260801-v1.json"
[[ ! -e "$DEPLOY_REQUEST" && ! -L "$DEPLOY_REQUEST" ]]
python3 - "$DEPLOY_REQUEST" "$IMPLEMENTATION_SHA" <<'PY'
import json,pathlib,sys
p={'request_id':'portal-authentik-public-oidc-20260801-v1','environment':'synology-staging','runner':'freqtrade-staging','implementation_sha':sys.argv[2],'portal_origin':'https://quant.molehill.cloud','authentik_origin':'https://auth.molehill.cloud','identity_transport':'https','identity_fixture_mode':'disabled','bootstrap_membership_authorized':False,'dry_run_required':True,'public_ingress_authorized':True,'live_capital_authorized':False,'restore_authorized':False,'secret_values_in_request':False}
pathlib.Path(sys.argv[1]).write_text(json.dumps(p,sort_keys=True),encoding='utf-8')
PY
python3 tools/agents/portal_supply_chain.py build-verify --repository "$GITHUB_WORKSPACE" --source-sha "$IMPLEMENTATION_SHA" --output-dir "$EVIDENCE/portal-supply-chain" --approval "$APPROVAL"
python3 tools/agents/portal_supply_chain.py verify-approval --approval "$APPROVAL" --expected-source-sha "$IMPLEMENTATION_SHA"
python3 tools/agents/portal_supply_chain.py deploy-approved --approved-images "$APPROVAL" --repository "$GITHUB_WORKSPACE" --request "$DEPLOY_REQUEST" --expected-repository-sha "$IMPLEMENTATION_SHA" --report "$REPORT"
rm -f -- "$DEPLOY_REQUEST"
python3 - "$REPORT" "$IMPLEMENTATION_SHA" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
if p.get('status')!='success' or p.get('implementation_sha')!=sys.argv[2] or p.get('live_capital_authorized') is not False: raise SystemExit('Portal deployment failed')
PY
for c in "$PORTAL_CONTROL_CONTAINER" "$PORTAL_WEB_CONTAINER"; do
  image="$(docker inspect --format '{{.Image}}' "$c")"; [[ "$image" =~ ^sha256:[0-9a-f]{64}$ ]]
  [[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image")" == "$IMPLEMENTATION_SHA" ]]
  [[ "$(docker inspect --format '{{.State.Running}}' "$c")" == "true" ]]
done

log "capture canonical SHADOW baseline and create persistent PAPER material"
mapfile -t old_ids < <(docker ps -aq --no-trunc --filter "label=com.docker.compose.project=$OLD_SHADOW_PROJECT" --filter "label=com.docker.compose.service=$OLD_SHADOW_SERVICE" | sed '/^$/d')
[[ ${#old_ids[@]} -eq 1 ]]
OLD_SHADOW_CONTAINER_ID="${old_ids[0]}"; export OLD_SHADOW_CONTAINER_ID
OLD_SHADOW_WAS_RUNNING="$(docker inspect --format '{{.State.Running}}' "$OLD_SHADOW_CONTAINER_ID")"; export OLD_SHADOW_WAS_RUNNING
OLD_SHADOW_IMAGE_DIGEST="$(docker inspect --format '{{.Image}}' "$OLD_SHADOW_CONTAINER_ID")"; OLD_SHADOW_IMAGE_DIGEST="${OLD_SHADOW_IMAGE_DIGEST#sha256:}"; export OLD_SHADOW_IMAGE_DIGEST

state_name="issue1396-production-paper-${IMPLEMENTATION_SHA:0:12}-${GITHUB_RUN_ID}"
activation_name="wickhunter-production-paper-${IMPLEMENTATION_SHA:0:12}-${GITHUB_RUN_ID}"
candidate_runner="$RUNNER_STATE_ROOT/wickhunter-candidate-materialization/packages/$CANDIDATE_PACKAGE_NAME"
candidate_host="$HOST_STATE_ROOT/wickhunter-candidate-materialization/packages/$CANDIDATE_PACKAGE_NAME"
state_runner="$RUNNER_STATE_ROOT/wickhunter-paper-runtime/$state_name"; state_host="$HOST_STATE_ROOT/wickhunter-paper-runtime/$state_name"
PROD_STATE_RUNNER="$state_runner"; export PROD_STATE_RUNNER
[[ -d "$candidate_runner" && ! -L "$candidate_runner" && ! -e "$state_runner" ]]
install -d -m 0750 -o 65532 -g 65532 "$state_runner" "$state_runner/activations" "$state_runner/journals" "$state_runner/operator" "$state_runner/operator/$activation_name"
cat > "$EVIDENCE/gateway.py" <<'PY'
import socket,socketserver,threading
TARGET=('fapi.binance.com',443)
class S(socketserver.ThreadingMixIn,socketserver.TCPServer): daemon_threads=True; allow_reuse_address=True
class H(socketserver.BaseRequestHandler):
    def handle(self):
        r=socket.create_connection(TARGET,timeout=15)
        def p(a,b):
            try:
                while True:
                    c=a.recv(65536)
                    if not c:return
                    b.sendall(c)
            except OSError:return
        t=threading.Thread(target=p,args=(self.request,r),daemon=True);t.start();p(r,self.request);t.join(timeout=5);r.close()
S(('0.0.0.0',443),H).serve_forever()
PY
GATEWAY_CODE_SHA256="$(sha256sum "$EVIDENCE/gateway.py" | awk '{print $1}')"
python3 - "$EVIDENCE/gateway-material.json" "$IMPLEMENTATION_SHA" "$PROOF_PAPER_IMAGE_DIGEST" "$GATEWAY_CODE_SHA256" "$PROD_INTERNAL_NETWORK" <<'PY'
import json,pathlib,sys
from ai_platform.wickhunter.canonical import canonical_sha256
path,sha,image,code,network=sys.argv[1:]
artifact={'schema_version':'wickhunter-public-market-gateway-artifact-v3','implementation_sha':sha,'runtime_image_digest':image,'gateway_code_sha256':code,'target':'fapi.binance.com:443'}
contract={'schema_version':'wickhunter-public-market-gateway-contract-v3','market_data_only':True,'target':'fapi.binance.com:443','credentials_allowed':False,'orders_allowed':False}
egress={'schema_version':'wickhunter-public-market-egress-v3','internal_network':network,'allowed_target':'fapi.binance.com:443','direct_external_egress':False,'trading_credentials_present':False,'order_adapter_present':False}
p={'gateway_artifact_digest':canonical_sha256(artifact),'gateway_contract_digest':canonical_sha256(contract),'market_egress_policy_digest':canonical_sha256(egress),'artifact':artifact,'contract':contract,'egress':egress}
pathlib.Path(path).write_text(json.dumps(p,sort_keys=True)+'\n',encoding='utf-8')
PY
GATEWAY_ARTIFACT_DIGEST="$(json_value "$EVIDENCE/gateway-material.json" gateway_artifact_digest)"; GATEWAY_CONTRACT_DIGEST="$(json_value "$EVIDENCE/gateway-material.json" gateway_contract_digest)"; MARKET_EGRESS_POLICY_DIGEST="$(json_value "$EVIDENCE/gateway-material.json" market_egress_policy_digest)"; export GATEWAY_ARTIFACT_DIGEST GATEWAY_CONTRACT_DIGEST MARKET_EGRESS_POLICY_DIGEST

docker run --rm -i --user 65532:65532 --read-only --network none --cap-drop ALL --security-opt no-new-privileges:true --mount "type=bind,src=$candidate_host,dst=/runtime/candidate,readonly" --mount "type=bind,src=$state_host,dst=/runtime/state" --env "ACTIVATION_NAME=$activation_name" --env EXPECTED_CANDIDATE_MANIFEST_SHA256 --env IMPLEMENTATION_SHA --env "PAPER_IMAGE_DIGEST=$PROOF_PAPER_IMAGE_DIGEST" --env GATEWAY_ARTIFACT_DIGEST --env GATEWAY_CONTRACT_DIGEST --env MARKET_EGRESS_POLICY_DIGEST --entrypoint python "$PAPER_IMAGE" - <<'PY' > "$EVIDENCE/production-activation.json"
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
if CandidatePaperRuntimeService(binding=binding,runtime_policy=_runtime_policy(),journal_root=journal).journal.latest_state() is not None: raise SystemExit('journal not fresh')
auth={'schema_version':'issue1396-paper-auth-v4','authorization_id':'issue1396-production-paper-v4','run_id':binding.request.run_id,'binding_id':binding.binding_id,'candidate_package_id':result.identity.package_id,'candidate_manifest_sha256':result.identity.manifest_sha256,'execution_enabled':False,'live_capital_authorized':False}
digest=canonical_sha256(auth)
r=resolve_managed_runtime_mode(ManagedRuntimeModeRequest(mode=BotMode.PAPER,paper_activation_authorized=True,paper_authorization_id=auth['authorization_id'],paper_authorization_digest=digest,paper_candidate_package_id=result.identity.package_id,paper_candidate_manifest_sha256=result.identity.manifest_sha256))
zero={'trading_credentials_present':r.trading_credentials_present,'order_adapter_present':r.order_adapter_present,'execution_enabled':r.execution_enabled,'orders_submitted':r.orders_submitted,'live_capital_authorized':r.live_capital_authorized,'automatic_promotion_enabled':r.automatic_promotion_enabled}
if zero!={'trading_credentials_present':False,'order_adapter_present':False,'execution_enabled':False,'orders_submitted':0,'live_capital_authorized':False,'automatic_promotion_enabled':False}: raise SystemExit('authority mismatch')
config={'schema_version':'issue1396-paper-config-v4','implementation_sha':os.environ['IMPLEMENTATION_SHA'],'image_digest':os.environ['PAPER_IMAGE_DIGEST'],'run_id':binding.request.run_id,'binding_id':binding.binding_id,'candidate_manifest_sha256':result.identity.manifest_sha256,'poll_seconds':120,'maximum_source_age_ms':300000,'gateway_artifact_digest':os.environ['GATEWAY_ARTIFACT_DIGEST'],'gateway_contract_digest':os.environ['GATEWAY_CONTRACT_DIGEST'],'market_egress_policy_digest':os.environ['MARKET_EGRESS_POLICY_DIGEST'],**zero}
print(json.dumps({'run_id':binding.request.run_id,'binding_id':binding.binding_id,'candidate_package_id':result.identity.package_id,'candidate_manifest_sha256':result.identity.manifest_sha256,'authorization_id':auth['authorization_id'],'authorization_digest':digest,'config_digest':canonical_sha256(config),**zero},sort_keys=True))
PY
activation_runner="$state_runner/activations/$activation_name"; journal_runner="$state_runner/journals/$activation_name"; operator_runner="$state_runner/operator/$activation_name"
find "$activation_runner" -type d -exec chmod 0550 {} +; find "$activation_runner" -type f -exec chmod 0440 {} +; find "$journal_runner" -type d -exec chmod 0750 {} +; find "$journal_runner" -type f -exec chmod 0640 {} +; chown -R 65532:65532 "$journal_runner" "$operator_runner"
PROD_ACTIVATION_HOST="$state_host/activations/$activation_name"; PROD_JOURNAL_HOST="$state_host/journals/$activation_name"; PROD_OPERATOR_HOST="$state_host/operator/$activation_name"; export PROD_ACTIVATION_HOST PROD_JOURNAL_HOST PROD_OPERATOR_HOST
PAPER_AUTHORIZATION_ID="$(json_value "$EVIDENCE/production-activation.json" authorization_id)"; PAPER_AUTHORIZATION_DIGEST="$(json_value "$EVIDENCE/production-activation.json" authorization_digest)"; PAPER_CANDIDATE_PACKAGE_ID="$(json_value "$EVIDENCE/production-activation.json" candidate_package_id)"; PAPER_CANDIDATE_MANIFEST="$(json_value "$EVIDENCE/production-activation.json" candidate_manifest_sha256)"; PAPER_CONFIG_DIGEST="$(json_value "$EVIDENCE/production-activation.json" config_digest)"; export PAPER_CONFIG_DIGEST

log "start and prove persistent PAPER before canonical mutation"
! docker container inspect "$PROD_PAPER_CONTAINER" >/dev/null 2>&1
! docker container inspect "$PROD_GATEWAY_CONTAINER" >/dev/null 2>&1
! docker network inspect "$PROD_INTERNAL_NETWORK" >/dev/null 2>&1
docker network create --internal "$PROD_INTERNAL_NETWORK" >/dev/null
gateway_code="$(cat "$EVIDENCE/gateway.py")"
docker create --name "$PROD_GATEWAY_CONTAINER" --init --user 0:0 --read-only --restart unless-stopped --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777 --cap-drop ALL --cap-add NET_BIND_SERVICE --security-opt no-new-privileges:true --memory 256m --network bridge --label "io.freqtrade.wickhunter.issue=1396" --label "io.freqtrade.wickhunter.role=production-paper-egress" --entrypoint python "$PAPER_IMAGE" -c "$gateway_code" >/dev/null
docker network connect "$PROD_INTERNAL_NETWORK" "$PROD_GATEWAY_CONTAINER"; docker start "$PROD_GATEWAY_CONTAINER" >/dev/null; sleep 2
gateway_ip="$(docker inspect --format "{{with index .NetworkSettings.Networks \"$PROD_INTERNAL_NETWORK\"}}{{.IPAddress}}{{end}}" "$PROD_GATEWAY_CONTAINER")"
docker create --name "$PROD_PAPER_CONTAINER" --restart unless-stopped --label "io.freqtrade.wickhunter.issue=1396" --label "io.freqtrade.wickhunter.mode=paper" --label "io.freqtrade.wickhunter.config-digest=$PAPER_CONFIG_DIGEST" --label "org.opencontainers.image.revision=$IMPLEMENTATION_SHA" --user 65532:65532 --group-add "$LIQUID20_READER_GID" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777 --cap-drop ALL --security-opt no-new-privileges:true --memory 2g --cpus 2.0 --pids-limit 256 --network "$PROD_INTERNAL_NETWORK" --add-host "fapi.binance.com:$gateway_ip" --env "OPERATOR_COMMIT=$IMPLEMENTATION_SHA" --env HEALTH_PATH=/runtime/operator/health.json --env HEALTH_MAX_AGE_SECONDS=1200 --env HTTP_PROXY= --env HTTPS_PROXY= --env ALL_PROXY= --env http_proxy= --env https_proxy= --env all_proxy= --mount "type=bind,src=$candidate_host,dst=/runtime/candidate,readonly" --mount "type=bind,src=$PROD_ACTIVATION_HOST,dst=/runtime/activation,readonly" --mount "type=bind,src=$LIQUID20_LIVE_HOST,dst=/runtime/liquid20,readonly" --mount "type=bind,src=$PROD_JOURNAL_HOST,dst=/runtime/journal" --mount "type=bind,src=$PROD_OPERATOR_HOST,dst=/runtime/operator" --health-cmd 'python /app/deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py' --health-interval 30s --health-timeout 10s --health-retries 3 --health-start-period 120s "$PAPER_IMAGE" --candidate-root /runtime/candidate --activation-root /runtime/activation --journal-root /runtime/journal --liquid20-root /runtime/liquid20 --health-root /runtime/operator --operator-commit "$IMPLEMENTATION_SHA" --public-market-base-url https://fapi.binance.com --poll-seconds 120 --maximum-source-age-ms 300000 --model-drift healthy --data-drift healthy --circuit-breaker-active false >/dev/null
docker start "$PROD_PAPER_CONTAINER" >/dev/null
for _ in $(seq 1 90); do h="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$PROD_PAPER_CONTAINER")"; [[ "$h" == "healthy" ]] && break; [[ "$h" =~ ^(unhealthy|exited|dead)$ ]] && exit 1; sleep 10; done
[[ "$(docker inspect --format '{{.State.Health.Status}}' "$PROD_PAPER_CONTAINER")" == "healthy" ]]
docker exec "$PROD_PAPER_CONTAINER" python /app/deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py
docker exec -i "$PROD_PAPER_CONTAINER" python - <<'PY'
import socket
s=socket.socket();s.settimeout(2);rc=s.connect_ex(('1.1.1.1',443));s.close()
if rc==0: raise SystemExit('forbidden direct external egress')
PY
docker exec "$PROD_PAPER_CONTAINER" python -c "import json,urllib.request;o=urllib.request.build_opener(urllib.request.ProxyHandler({}));r=o.open('https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT',timeout=20);json.loads(r.read().decode());r.close()"
PROD_PAPER_CONTAINER_ID="$(docker inspect --format '{{.Id}}' "$PROD_PAPER_CONTAINER")"; export PROD_PAPER_CONTAINER_ID
[[ "$(docker inspect --format '{{.Image}}' "$PROD_PAPER_CONTAINER")" == "sha256:$PROOF_PAPER_IMAGE_DIGEST" ]]
cp "$PROD_OPERATOR_HOST/health.json" "$EVIDENCE/production-health.json"

log "install current-contract canonical reconciliation helper in exact Portal control plane"
cat > "$EVIDENCE/transition.py" <<'PY'
from __future__ import annotations
import argparse,json,os
from datetime import UTC,datetime,timedelta
from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
from ai_platform.portal.contracts.bots import BotObservedState
from ai_platform.portal.contracts.identity import ActorType,Permission
from ai_platform.portal.contracts.runtime_generation import ReconciliationCompletenessStatus,ReconciliationFreshnessStatus,RuntimeGenerationMaterial,RuntimeGenerationObservation,RuntimeIdentityStatus
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import build_engine,build_session_factory
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.control_plane.runtime_adoption import latest_runtime_observation,reconcile_external_runtime_observation,record_external_runtime_stop_observation
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import BotMode
BOT='wickhunter'; TENANT='tenant-local'
def sf(): return build_session_factory(build_engine(os.environ['PORTAL_DATABASE_URL']))
def ctx(actor): return RequestContext(tenant_id=TENANT,actor_id=actor,actor_type=ActorType.SYSTEM,permissions=(Permission.ADMIN_MANAGE,Permission.AUDIT_READ,Permission.BOT_CREATE,Permission.BOT_READ,Permission.BOT_START),request_id=uuid4(),correlation_id=uuid4(),causation_id=None)
def truth(factory,context):
 r=TestClient(create_app(factory,identity_context_provider=lambda:context)).get(f'/v1/bots/{BOT}/runtime-truth'); r.raise_for_status(); return r.json()
def zero(h):
 e={'trading_credentials_present':False,'order_adapter_present':False,'execution_enabled':False,'orders_submitted':0,'live_capital_authorized':False}
 if any(h.get(k)!=v for k,v in e.items()): raise SystemExit('zero-authority mismatch')
def baseline(a):
 f=sf(); c=ctx('issue1396-baseline'); t=truth(f,c); d=t['desired_generation']; o=t['observed_generation']; latest=latest_runtime_observation(f,c,BOT)
 if d['generation_id']!=o['generation_id'] or d['managed_mode']!='shadow' or o['managed_mode']!='shadow' or t['pending_rollout'] is not False: raise SystemExit('baseline not converged SHADOW')
 if o['runtime_image_digest']!=a.old_image_digest or latest is None or latest.runtime_instance_id!=a.old_container_id: raise SystemExit('baseline physical identity mismatch')
 print(json.dumps({'truth':t,'latest':latest.model_dump(mode='json')},sort_keys=True))
def author(a):
 f=sf(); c=ctx('issue1396-author'); repo=BotRepository()
 with f() as s:
  b=repo.get_bot(s,TENANT,BOT); old=repo.get_runtime_generation(s,TENANT,b.observed_runtime_generation_id) if b and b.observed_runtime_generation_id else None
 if b is None or old is None or b.desired_runtime_generation_id!=b.observed_runtime_generation_id or old.managed_mode is not BotMode.SHADOW: raise SystemExit('cannot author PAPER from current state')
 isolation={'schema_version':'issue1396-isolation-v4','runtime_user':'65532:65532','read_only_rootfs':True,'network':a.internal_network}
 risk={'schema_version':'issue1396-risk-v4','minimum_healthy_sources':1,'maximum_source_age_ms':300000,'execution_enabled':False,'live_capital_authorized':False}
 material=RuntimeGenerationMaterial(normalized_runtime_config_digest=a.config_digest,runtime_image_digest=a.image_digest,strategy_artifact_digest=old.strategy_artifact_digest,model_artifact_digest=old.model_artifact_digest,feature_schema_version=old.feature_schema_version,risk_policy_digest=canonical_sha256(risk),exchange_mode=old.exchange_mode,exchange_connection_revision=old.exchange_connection_revision,isolation_profile_version='issue1396-isolation-v4',isolation_profile_digest=canonical_sha256(isolation),isolation_plan_digest=canonical_sha256(isolation),gateway_artifact_digest=a.gateway_artifact_digest,gateway_contract_version='issue1396-gateway-v4',gateway_contract_digest=a.gateway_contract_digest,market_data_egress_policy_version='issue1396-egress-v4',market_data_egress_policy_digest=a.egress_digest,paper_activation_authorized=True,paper_authorization_id=a.authorization_id,paper_authorization_digest=a.authorization_digest,paper_candidate_package_id=a.candidate_package_id,paper_candidate_manifest_sha256=a.candidate_manifest,generation_spec_version='issue1396-paper-generation-v4')
 service=ControlPlaneService(f,generation_material_resolver=lambda _c,r: material if r.managed_mode is BotMode.PAPER else (_ for _ in ()).throw(RuntimeError('PAPER only')))
 current=service.get_bot(c,BOT); spec=current.spec.model_copy(update={'managed_mode':BotMode.PAPER,'config_revision':current.spec.config_revision+1,'runtime_version':f'wh09-paper-{a.implementation_sha[:12]}','risk_policy_version':'issue1396-risk-v4'})
 revised=service.revise_bot(c,BOT,spec); promoted=service.promote_revision(c,BOT,revised.latest_authored_revision_id,revised.state_version); current=service.get_bot(c,BOT); pending,generation,rollout=service.apply_revision(c,BOT,promoted.revision_id,current.state_version,f'issue1396-paper-{a.implementation_sha[:12]}')
 if generation.managed_mode is not BotMode.PAPER or generation.runtime_image_digest!=a.image_digest or generation.normalized_runtime_config_digest!=a.config_digest or pending.observed_runtime_generation_id!=old.generation_id: raise SystemExit('authored PAPER binding mismatch')
 print(json.dumps({'old_generation':old.model_dump(mode='json'),'paper_generation':generation.model_dump(mode='json'),'rollout':rollout.model_dump(mode='json')},sort_keys=True))
def stop(a):
 f=sf(); c=ctx('issue1396-stop'); repo=BotRepository(); latest=latest_runtime_observation(f,c,BOT)
 with f() as s: g=repo.get_runtime_generation(s,TENANT,a.generation_id)
 if g is None or latest is None or latest.generation_id!=g.generation_id or latest.runtime_instance_id!=a.runtime_instance_id: raise SystemExit('STOP identity mismatch')
 if latest.observed_state=='STOPPED': obs=latest
 else:
  at=max(datetime.now(UTC),latest.reconciled_at+timedelta(microseconds=1)); evidence={'generation_id':g.generation_id,'runtime_instance_id':a.runtime_instance_id,'state':'STOPPED','at':at.isoformat()}; obs=RuntimeGenerationObservation(observation_id=str(uuid4()),generation_id=g.generation_id,runtime_instance_id=a.runtime_instance_id,reconciliation_epoch=latest.reconciliation_epoch+1,reconciliation_attempt=latest.reconciliation_attempt+1,observed_state='STOPPED',observed_generation_spec_digest=g.generation_spec_digest,observed_image_digest=g.runtime_image_digest,observed_config_digest=g.normalized_runtime_config_digest,source_sequence=None,source_version=None,source_observed_at=at,reconciled_at=at,identity_status=RuntimeIdentityStatus.MATCHED,freshness_status=ReconciliationFreshnessStatus.CURRENT,completeness_status=ReconciliationCompletenessStatus.COMPLETE,evidence_hash=canonical_sha256(evidence),reason_code='ISSUE1396_SHADOW_STOPPED')
 persisted=record_external_runtime_stop_observation(f,c,BOT,obs); print(persisted.model_dump_json())
def reconcile(a):
 f=sf(); c=ctx(a.actor); repo=BotRepository(); h=json.loads(Path(a.health_json).read_text()); zero(h)
 with f() as s: g=repo.get_runtime_generation(s,TENANT,a.generation_id)
 if g is None or h.get('operator_commit')!=a.source_version or h.get('status')!='healthy' or h.get('runtime_health')!='healthy': raise SystemExit('PAPER health mismatch')
 latest=latest_runtime_observation(f,c,BOT); same=latest is not None and latest.generation_id==g.generation_id and latest.runtime_instance_id==a.runtime_instance_id; epoch=latest.reconciliation_epoch+1 if same else 1; attempt=latest.reconciliation_attempt+1 if same else 1; observed=datetime.fromtimestamp(h['checked_at_ms']/1000,tz=UTC); at=max(datetime.now(UTC),observed,(latest.reconciled_at+timedelta(microseconds=1)) if same else observed); seq=h['generation']; evidence={'generation_id':g.generation_id,'runtime_instance_id':a.runtime_instance_id,'health_sha256':h['health_sha256'],'sequence':seq,'source':a.source_version,'at':at.isoformat()}; obs=RuntimeGenerationObservation(observation_id=str(uuid4()),generation_id=g.generation_id,runtime_instance_id=a.runtime_instance_id,reconciliation_epoch=epoch,reconciliation_attempt=attempt,observed_state='RUNNING',observed_generation_spec_digest=g.generation_spec_digest,observed_image_digest=g.runtime_image_digest,observed_config_digest=g.normalized_runtime_config_digest,source_sequence=seq,source_version=a.source_version,source_observed_at=observed,reconciled_at=at,identity_status=RuntimeIdentityStatus.MATCHED,freshness_status=ReconciliationFreshnessStatus.CURRENT,completeness_status=ReconciliationCompletenessStatus.COMPLETE,evidence_hash=canonical_sha256(evidence),reason_code='ISSUE1396_PAPER_RUNNING'); result=reconcile_external_runtime_observation(f,c,BOT,obs); t=truth(f,c)
 if result.bot.desired_runtime_generation_id!=g.generation_id or result.bot.observed_runtime_generation_id!=g.generation_id or t['pending_rollout'] is not False or t['latest_rollout']['status']!='SUCCEEDED': raise SystemExit('PAPER reconciliation failed')
 print(json.dumps({'observation':obs.model_dump(mode='json'),'truth':t},sort_keys=True))
def final(_a):
 f=sf(); c=ctx('issue1396-final'); cl=TestClient(create_app(f,identity_context_provider=lambda:c)); bots=cl.get('/v1/bots'); rt=cl.get(f'/v1/bots/{BOT}/runtime-truth'); bots.raise_for_status(); rt.raise_for_status(); rows=[x for x in bots.json() if x.get('bot_id')==BOT]; t=rt.json()
 if len(rows)!=1 or t['desired_generation']['generation_id']!=t['observed_generation']['generation_id'] or t['desired_generation']['managed_mode']!='paper' or t['observed_generation']['managed_mode']!='paper' or t['pending_rollout'] is not False: raise SystemExit('final canonical truth mismatch')
 print(json.dumps({'bots':rows,'truth':t},sort_keys=True))
p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True)
q=s.add_parser('baseline'); q.add_argument('--old-container-id',required=True); q.add_argument('--old-image-digest',required=True); q.set_defaults(fn=baseline)
q=s.add_parser('author');
for x in ('implementation-sha','image-digest','config-digest','authorization-id','authorization-digest','candidate-package-id','candidate-manifest','internal-network','gateway-artifact-digest','gateway-contract-digest','egress-digest'): q.add_argument('--'+x,required=True)
q.set_defaults(fn=author)
q=s.add_parser('stop'); q.add_argument('--generation-id',required=True); q.add_argument('--runtime-instance-id',required=True); q.set_defaults(fn=stop)
q=s.add_parser('reconcile'); q.add_argument('--generation-id',required=True); q.add_argument('--runtime-instance-id',required=True); q.add_argument('--health-json',required=True); q.add_argument('--source-version',required=True); q.add_argument('--actor',required=True); q.set_defaults(fn=reconcile)
q=s.add_parser('final'); q.set_defaults(fn=final)
a=p.parse_args(); a.fn(a)
PY
docker cp "$EVIDENCE/transition.py" "$PORTAL_CONTROL_CONTAINER:/tmp/issue1396-transition.py"
docker exec "$PORTAL_CONTROL_CONTAINER" python -m py_compile /tmp/issue1396-transition.py
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396-transition.py baseline --old-container-id "$OLD_SHADOW_CONTAINER_ID" --old-image-digest "$OLD_SHADOW_IMAGE_DIGEST" > "$EVIDENCE/baseline.json"

log "stop exact legacy SHADOW, author canonical PAPER, reconcile RUNNING"
if [[ "$OLD_SHADOW_WAS_RUNNING" == "true" ]]; then docker stop --time 30 "$OLD_SHADOW_CONTAINER_ID" >/dev/null; fi
[[ "$(docker inspect --format '{{.State.Running}}' "$OLD_SHADOW_CONTAINER_ID")" == "false" ]]
CANONICAL_AUTHOR_STARTED=true; export CANONICAL_AUTHOR_STARTED
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396-transition.py author --implementation-sha "$IMPLEMENTATION_SHA" --image-digest "$PROOF_PAPER_IMAGE_DIGEST" --config-digest "$PAPER_CONFIG_DIGEST" --authorization-id "$PAPER_AUTHORIZATION_ID" --authorization-digest "$PAPER_AUTHORIZATION_DIGEST" --candidate-package-id "$PAPER_CANDIDATE_PACKAGE_ID" --candidate-manifest "$PAPER_CANDIDATE_MANIFEST" --internal-network "$PROD_INTERNAL_NETWORK" --gateway-artifact-digest "$GATEWAY_ARTIFACT_DIGEST" --gateway-contract-digest "$GATEWAY_CONTRACT_DIGEST" --egress-digest "$MARKET_EGRESS_POLICY_DIGEST" > "$EVIDENCE/desired-paper.json"
OLD_GENERATION_ID="$(json_value "$EVIDENCE/desired-paper.json" old_generation.generation_id)"; PAPER_GENERATION_ID="$(json_value "$EVIDENCE/desired-paper.json" paper_generation.generation_id)"; export PAPER_GENERATION_ID
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396-transition.py stop --generation-id "$OLD_GENERATION_ID" --runtime-instance-id "$OLD_SHADOW_CONTAINER_ID" > "$EVIDENCE/shadow-stopped.json"
docker cp "$EVIDENCE/production-health.json" "$PORTAL_CONTROL_CONTAINER:/tmp/issue1396-health.json"
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396-transition.py reconcile --generation-id "$PAPER_GENERATION_ID" --runtime-instance-id "$PROD_PAPER_CONTAINER_ID" --health-json /tmp/issue1396-health.json --source-version "$IMPLEMENTATION_SHA" --actor issue1396-paper-reconcile > "$EVIDENCE/paper-reconciled.json"

log "restart exact PAPER runtime and record newer reconciliation"
before_generation="$(json_value "$EVIDENCE/production-health.json" generation)"; before_checked="$(json_value "$EVIDENCE/production-health.json" checked_at_ms)"; before_id="$PROD_PAPER_CONTAINER_ID"
docker restart "$PROD_PAPER_CONTAINER" >/dev/null
for _ in $(seq 1 90); do
  h="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$PROD_PAPER_CONTAINER")"
  if [[ "$h" == "healthy" && -f "$PROD_OPERATOR_HOST/health.json" ]]; then g="$(json_value "$PROD_OPERATOR_HOST/health.json" generation)"; c="$(json_value "$PROD_OPERATOR_HOST/health.json" checked_at_ms)"; if (( g > before_generation && c > before_checked )); then break; fi; fi
  sleep 10
done
[[ "$(docker inspect --format '{{.Id}}' "$PROD_PAPER_CONTAINER")" == "$before_id" ]]
[[ "$(docker inspect --format '{{.Image}}' "$PROD_PAPER_CONTAINER")" == "sha256:$PROOF_PAPER_IMAGE_DIGEST" ]]
[[ "$(docker inspect --format '{{.State.Health.Status}}' "$PROD_PAPER_CONTAINER")" == "healthy" ]]
cp "$PROD_OPERATOR_HOST/health.json" "$EVIDENCE/health-after-restart.json"
after_generation="$(json_value "$EVIDENCE/health-after-restart.json" generation)"; (( after_generation > before_generation ))
docker cp "$EVIDENCE/health-after-restart.json" "$PORTAL_CONTROL_CONTAINER:/tmp/issue1396-health-after-restart.json"
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396-transition.py reconcile --generation-id "$PAPER_GENERATION_ID" --runtime-instance-id "$PROD_PAPER_CONTAINER_ID" --health-json /tmp/issue1396-health-after-restart.json --source-version "$IMPLEMENTATION_SHA" --actor issue1396-paper-restart-reconcile > "$EVIDENCE/paper-restart-reconciled.json"
docker exec "$PORTAL_CONTROL_CONTAINER" python /tmp/issue1396-transition.py final > "$EVIDENCE/final-api.json"
python3 - "$EVIDENCE/restart.json" "$before_id" "$before_generation" "$after_generation" "$PROOF_PAPER_IMAGE_DIGEST" "$PAPER_CONFIG_DIGEST" <<'PY'
import json,pathlib,sys
path,runtime,before,after,image,config=sys.argv[1:]
pathlib.Path(path).write_text(json.dumps({'result':'PASS','same_runtime_instance':True,'runtime_instance_id':runtime,'before_generation':int(before),'after_generation':int(after),'paper_image_digest':image,'paper_config_digest':config},sort_keys=True)+'\n',encoding='utf-8')
PY
python3 - "$EVIDENCE/closeout.json" "$EVIDENCE/final-api.json" "$EVIDENCE/proof/issue1396-proof.json" "$EVIDENCE/health-after-restart.json" "$EVIDENCE/restart.json" "$EVIDENCE/production-activation.json" "$EVIDENCE/gateway-material.json" "$PROOF_ARTIFACT_ID" "$PROOF_ARTIFACT_DIGEST" "$PROOF_RUN_ID" "$IMPLEMENTATION_SHA" "$PROD_PAPER_CONTAINER_ID" "$OLD_SHADOW_CONTAINER_ID" <<'PY'
import json,pathlib,sys
out,api,proof,health,restart,activation,gateway=sys.argv[1:8]; artifact,digest,run,sha,paper,old=sys.argv[8:]
p={'result':'PASS','implementation_sha':sha,'api':json.load(open(api)),'five_cycle_proof':json.load(open(proof)),'paper_health':json.load(open(health)),'restart':json.load(open(restart)),'activation':json.load(open(activation)),'gateway':json.load(open(gateway)),'proof_artifact':{'id':int(artifact),'digest':digest,'run_id':int(run)},'physical':{'paper_container_id':paper,'old_shadow_container_id':old}}
pathlib.Path(out).write_text(json.dumps(p,sort_keys=True)+'\n',encoding='utf-8')
PY
DESIRED_GENERATION_ID="$(json_value "$EVIDENCE/final-api.json" truth.desired_generation.generation_id)"; OBSERVED_GENERATION_ID="$(json_value "$EVIDENCE/final-api.json" truth.observed_generation.generation_id)"; [[ "$DESIRED_GENERATION_ID" == "$OBSERVED_GENERATION_ID" ]]
base64 -w0 "$EVIDENCE/closeout.json" > "$EVIDENCE/closeout.b64"
{
  echo "closeout_b64=$(cat "$EVIDENCE/closeout.b64")"
  echo "desired_generation_id=$DESIRED_GENERATION_ID"
  echo "observed_generation_id=$OBSERVED_GENERATION_ID"
  echo "paper_container_id=$PROD_PAPER_CONTAINER_ID"
  echo "old_shadow_container_id=$OLD_SHADOW_CONTAINER_ID"
  echo "paper_image_digest=$PROOF_PAPER_IMAGE_DIGEST"
  echo "paper_config_digest=$PAPER_CONFIG_DIGEST"
} >> "$GITHUB_OUTPUT"
log "terminal transition PASS"
