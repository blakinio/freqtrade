#!/usr/bin/env bash
set -euo pipefail
: "${HARNESS_SHA:?}" "${TARGET_AUTHORIZATION_SHA:?}" "${PORTAL_CONTROL_CONTAINER:?}" "${PORTAL_WEB_CONTAINER:?}" "${PORTAL_ORIGIN:?}" "${BROWSER_IMAGE:?}"
for _ in $(seq 1 90); do
  cr="$(docker inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$PORTAL_CONTROL_CONTAINER" 2>/dev/null||true)"
  wr="$(docker inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$PORTAL_WEB_CONTAINER" 2>/dev/null||true)"
  ch="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$PORTAL_CONTROL_CONTAINER" 2>/dev/null||true)"
  wh="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$PORTAL_WEB_CONTAINER" 2>/dev/null||true)"
  [[ "$cr" == "$TARGET_AUTHORIZATION_SHA" && "$wr" == "$TARGET_AUTHORIZATION_SHA" && "$ch" == healthy && "$wh" == healthy ]] && break
  sleep 2
done
[[ "$cr" == "$TARGET_AUTHORIZATION_SHA" && "$wr" == "$TARGET_AUTHORIZATION_SHA" && "$ch" == healthy && "$wh" == healthy ]]
docker inspect "$PORTAL_WEB_CONTAINER" > "$RUNNER_TEMP/web.json"
python3 - "$RUNNER_TEMP/web.json" <<'PY'
import json,sys
env=set(json.load(open(sys.argv[1]))[0]["Config"].get("Env") or [])
if "PORTAL_WEB_DATA_MODE=api" not in env or "PORTAL_IDENTITY_FIXTURE_MODE=disabled" not in env: raise SystemExit("deployed Portal mode mismatch")
PY
docker exec -i "$PORTAL_CONTROL_CONTAINER" python - <<'PY'
import os,time
from uuid import uuid4
from fastapi.testclient import TestClient
from ai_platform.portal.contracts.identity import ActorType,Permission
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import build_engine,build_session_factory
c=RequestContext(tenant_id="tenant-local",actor_id="system-wh09-browser-v4-preflight",actor_type=ActorType.SYSTEM,permissions=(Permission.BOT_READ,Permission.AUDIT_READ),request_id=uuid4(),correlation_id=uuid4(),causation_id=None)
f=build_session_factory(build_engine(os.environ["PORTAL_DATABASE_URL"])); client=TestClient(create_app(f,identity_context_provider=lambda:c)); last="not sampled"
for n in range(12):
 b=client.get("/v1/bots"); t=client.get("/v1/bots/wickhunter/runtime-truth"); r=client.get("/v1/bots/wickhunter/wickhunter-runtime-evidence")
 if b.status_code==t.status_code==r.status_code==200:
  rows=[x for x in b.json() if x.get("bot_id")=="wickhunter"]; e=r.json().get("runtime") or {}
  if len(rows)!=1: raise SystemExit("canonical WickHunter identity is not unique")
  if any((e.get("trading_credentials_present") is not False,e.get("order_adapter_present") is not False,e.get("execution_enabled") is not False,e.get("orders_submitted")!=0,e.get("live_capital_authorized") is not False)): raise SystemExit("zero-authority invariant changed")
  if t.json().get("pending_rollout") is False and e.get("health")=="HEALTHY" and e.get("decision_count",0)>0 and e.get("no_trade_count",0)>0: break
  last=f"health={e.get('health')} pending={t.json().get('pending_rollout')}"
 else: last=f"status={b.status_code}/{t.status_code}/{r.status_code}"
 if n<11: time.sleep(5)
else: raise SystemExit(f"canonical WickHunter truth did not converge: {last}")
PY
token_file="$RUNNER_TEMP/v4-token"; evidence="$RUNNER_TEMP/portal-wh09-browser-v4.json"; browser_name="portal-wh09-browser-v4-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
key="$(printf '%s:%s' "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT"|sha256sum|awk '{print substr($1,1,24)}')"; principal_id="wh09-vp-$key"; membership_id="wh09-vm-$key"; subject="urn:freqtrade:wh09-browser-v4:${GITHUB_RUN_ID}:${GITHUB_RUN_ATTEMPT}"
umask 077; python3 -c 'import secrets; print(secrets.token_urlsafe(48))' > "$token_file"; session_token="$(cat "$token_file")"; echo "::add-mask::$session_token"; [[ "$session_token" =~ ^[A-Za-z0-9_-]+$ ]]
docker exec -i --env "T=$session_token" --env "P=$principal_id" --env "M=$membership_id" --env "S=$subject" "$PORTAL_CONTROL_CONTAINER" python - <<'PY'
from datetime import UTC,datetime,timedelta
import os
from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.control_plane.database import build_engine,build_session_factory
from ai_platform.portal.identity.crypto import IdentityCrypto,IdentitySecrets
from ai_platform.portal.identity.repository import IdentityRepository
from ai_platform.portal.identity.runtime import IdentityRuntimeConfig
cfg=IdentityRuntimeConfig.from_environment(); cry=IdentityCrypto(IdentitySecrets(session_hmac_key=cfg.session_hmac_key,flow_encryption_key=cfg.flow_encryption_key)); eng=build_engine(os.environ["PORTAL_DATABASE_URL"]); f=build_session_factory(eng); now=datetime.now(UTC)
try:
 with f() as s:
  r=IdentityRepository(s); p=r.create_principal(principal_id=os.environ["P"],issuer=cfg.issuer,subject=os.environ["S"],display_name="WH09 browser v4 acceptance",email=None,now=now); m=r.create_membership(membership_id=os.environ["M"],principal_id=p.principal_id,tenant_id="tenant-local",roles=(RoleName.USER,),valid_from=now,valid_until=now+timedelta(minutes=30),now=now); r.create_session(session_id_hash=cry.hash_token(os.environ["T"]),csrf_token_hash=cry.hash_token(os.environ["T"]+":csrf"),principal_id=p.principal_id,membership_id=m.membership_id,membership_version=m.membership_version,idp_session_id=None,authentication_time=now,mfa_satisfied=True,created_at=now,idle_expires_at=now+timedelta(minutes=15),absolute_expires_at=now+timedelta(minutes=30)); s.commit()
finally: eng.dispose()
PY
browser_rc=0
if docker create --name "$browser_name" --label "ftai.task=FTAI-20260819-wickhunter-portal-real-integration-1561" --label "ftai.harness_sha=$HARNESS_SHA" --label "ftai.target_authorization_sha=$TARGET_AUTHORIZATION_SHA" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=512m --cap-drop ALL --security-opt no-new-privileges:true --shm-size 256m --env WICKHUNTER_BROWSER_ORIGIN="$PORTAL_ORIGIN" --env WICKHUNTER_SESSION_TOKEN="$session_token" --env WICKHUNTER_CSRF_TOKEN="${session_token}:csrf" --env WICKHUNTER_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium --env WICKHUNTER_BROWSER_NO_SANDBOX=1 --env WICKHUNTER_BROWSER_EVIDENCE_PATH=/tmp/evidence.json "$BROWSER_IMAGE" >/dev/null; then
 docker start --attach "$browser_name" || browser_rc=$?; docker cp "$browser_name:/tmp/evidence.json" "$evidence" 2>/dev/null || true
else browser_rc=$?; fi
cleanup_rc=0
docker exec -i --env "T=$session_token" --env "P=$principal_id" --env "M=$membership_id" --env "S=$subject" "$PORTAL_CONTROL_CONTAINER" python - <<'PY' || cleanup_rc=$?
import os
from ai_platform.portal.control_plane.database import build_engine,build_session_factory
from ai_platform.portal.identity.crypto import IdentityCrypto,IdentitySecrets
from ai_platform.portal.identity.models import IdentityPrincipalRow,PortalSessionRow,TenantMembershipRow
from ai_platform.portal.identity.runtime import IdentityRuntimeConfig
cfg=IdentityRuntimeConfig.from_environment(); cry=IdentityCrypto(IdentitySecrets(session_hmac_key=cfg.session_hmac_key,flow_encryption_key=cfg.flow_encryption_key)); eng=build_engine(os.environ["PORTAL_DATABASE_URL"]); f=build_session_factory(eng); h=cry.hash_token(os.environ["T"])
try:
 with f() as s:
  x=s.get(PortalSessionRow,h)
  if x is not None:
   if x.principal_id!=os.environ["P"] or x.membership_id!=os.environ["M"]: raise SystemExit("refusing non-task session cleanup")
   s.delete(x); s.flush()
  x=s.get(TenantMembershipRow,os.environ["M"])
  if x is not None:
   if x.principal_id!=os.environ["P"] or x.tenant_id!="tenant-local": raise SystemExit("refusing non-task membership cleanup")
   s.delete(x); s.flush()
  x=s.get(IdentityPrincipalRow,os.environ["P"])
  if x is not None:
   if x.subject!=os.environ["S"]: raise SystemExit("refusing non-task principal cleanup")
   s.delete(x)
  s.commit()
  if s.get(PortalSessionRow,h) or s.get(TenantMembershipRow,os.environ["M"]) or s.get(IdentityPrincipalRow,os.environ["P"]): raise SystemExit("task-owned identity cleanup failed")
finally: eng.dispose()
PY
rm -f "$token_file"; resource_rc=0; docker rm -f "$browser_name" >/dev/null 2>&1 || true; docker image rm "$BROWSER_IMAGE" >/dev/null 2>&1 || resource_rc=$?
[[ "$cleanup_rc" -eq 0 && "$resource_rc" -eq 0 ]]; test -s "$evidence"
python3 - "$evidence" "$HARNESS_SHA" "$TARGET_AUTHORIZATION_SHA" <<'PY'
import json,sys
p=sys.argv[1]; e=json.load(open(p)); required={"result":"PASS","origin":"https://quant.molehill.cloud","mode":"shadow","authenticated":True,"fixture_cookie_present":False,"health_visible":True,"runtime_generation_converged":True,"reload_persistence":True}
for k,v in required.items():
 if e.get(k)!=v: raise SystemExit(f"browser v4 evidence mismatch: {k}")
if e.get("decision_count",0)<=0 or e.get("no_trade_count",0)<=0: raise SystemExit("missing decision evidence")
e["harness_source_sha"]=sys.argv[2]; e["target_authorization_sha"]=sys.argv[3]; open(p,"w").write(json.dumps(e,indent=2,sort_keys=True)+"\n")
PY
[[ "$browser_rc" -eq 0 ]]
