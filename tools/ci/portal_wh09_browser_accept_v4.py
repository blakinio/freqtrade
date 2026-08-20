from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time

TARGET = "eafc198857c90caf89a5920da60ae7661c1061ba"
CONTROL = "freqtrade-portal-control-plane"
WEB = "freqtrade-portal-staging"
ORIGIN = "https://quant.molehill.cloud"
TASK = "FTAI-20260819-wickhunter-portal-real-integration-1561"


def run(args: list[str], *, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True, env=env)


def out(args: list[str]) -> str:
    return run(args).stdout.strip()


def docker_exec(code: str, extra: dict[str, str] | None = None) -> None:
    env = os.environ.copy()
    if extra:
        env.update(extra)
    args = ["docker", "exec", "-i"]
    for key in extra or {}:
        args += ["--env", key]
    args += [CONTROL, "python", "-"]
    subprocess.run(args, input=code, text=True, check=True, env=env)


def verify_target(harness: str, approval_path: Path, archive: Path) -> str:
    approval = json.loads(approval_path.read_text())
    if approval.get("schema_version") != 4:
        raise RuntimeError("browser helper approval schema mismatch")
    if approval.get("harness_source_sha") != harness or approval.get("target_authorization_sha") != TARGET:
        raise RuntimeError("browser helper provenance mismatch")
    if approval.get("persistent_runtime") is not False:
        raise RuntimeError("browser helper claimed persistent authority")
    if hashlib.sha256(archive.read_bytes()).hexdigest() != approval["tar_sha256"]:
        raise RuntimeError("browser helper archive digest mismatch")
    subprocess.run(["sh", "-c", f"gzip -dc '{archive}' | docker load >/dev/null"], check=True)
    image = approval["image_tag"]
    if out(["docker", "image", "inspect", "--format", "{{.Id}}", image]) != approval["image_id"]:
        raise RuntimeError("browser helper image id mismatch")
    if out(["docker", "image", "inspect", "--format", '{{index .Config.Labels "org.opencontainers.image.revision"}}', image]) != harness:
        raise RuntimeError("browser helper harness label mismatch")
    if out(["docker", "image", "inspect", "--format", '{{index .Config.Labels "ftai.target_authorization_sha"}}', image]) != TARGET:
        raise RuntimeError("browser helper target label mismatch")
    for _ in range(90):
        cr = out(["docker", "inspect", "--format", '{{index .Config.Labels "org.opencontainers.image.revision"}}', CONTROL])
        wr = out(["docker", "inspect", "--format", '{{index .Config.Labels "org.opencontainers.image.revision"}}', WEB])
        ch = out(["docker", "inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}", CONTROL])
        wh = out(["docker", "inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}", WEB])
        if cr == wr == TARGET and ch == wh == "healthy":
            break
        time.sleep(2)
    else:
        raise RuntimeError("deployed Portal target did not converge")
    web = json.loads(out(["docker", "inspect", WEB]))[0]
    env = set(web["Config"].get("Env") or [])
    if "PORTAL_WEB_DATA_MODE=api" not in env or "PORTAL_IDENTITY_FIXTURE_MODE=disabled" not in env:
        raise RuntimeError("deployed Portal is not real API mode with fixtures disabled")
    return image


PREFLIGHT = r'''
import os,time
from uuid import uuid4
from fastapi.testclient import TestClient
from ai_platform.portal.contracts.identity import ActorType,Permission
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import build_engine,build_session_factory
ctx=RequestContext(tenant_id="tenant-local",actor_id="system-wh09-browser-v4-preflight",actor_type=ActorType.SYSTEM,permissions=(Permission.BOT_READ,Permission.AUDIT_READ),request_id=uuid4(),correlation_id=uuid4(),causation_id=None)
f=build_session_factory(build_engine(os.environ["PORTAL_DATABASE_URL"])); c=TestClient(create_app(f,identity_context_provider=lambda:ctx)); last="not sampled"
for attempt in range(181):
    bots=c.get("/v1/bots"); truth=c.get("/v1/bots/wickhunter/runtime-truth"); runtime=c.get("/v1/bots/wickhunter/wickhunter-runtime-evidence")
    if bots.status_code==truth.status_code==runtime.status_code==200:
        rows=[r for r in bots.json() if r.get("bot_id")=="wickhunter"]
        if len(rows)!=1: raise SystemExit("canonical WickHunter identity is not unique")
        e=runtime.json().get("runtime") or {}
        if e.get("trading_credentials_present") is not False or e.get("order_adapter_present") is not False or e.get("execution_enabled") is not False or e.get("orders_submitted")!=0 or e.get("live_capital_authorized") is not False: raise SystemExit("WickHunter zero-authority invariant changed")
        if truth.json().get("pending_rollout") is False and e.get("health")=="HEALTHY" and e.get("decision_count",0)>0 and e.get("no_trade_count",0)>0: break
        last=f"health={e.get('health')} pending={truth.json().get('pending_rollout')}"
    else: last=f"status={bots.status_code}/{truth.status_code}/{runtime.status_code}"
    if attempt<180: time.sleep(5)
else: raise SystemExit(f"canonical WickHunter truth did not converge: {last}")
'''

SEED = r'''
from datetime import UTC,datetime,timedelta
import os
from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.control_plane.database import build_engine,build_session_factory
from ai_platform.portal.identity.crypto import IdentityCrypto,IdentitySecrets
from ai_platform.portal.identity.repository import IdentityRepository
from ai_platform.portal.identity.runtime import IdentityRuntimeConfig
c=IdentityRuntimeConfig.from_environment(); crypto=IdentityCrypto(IdentitySecrets(session_hmac_key=c.session_hmac_key,flow_encryption_key=c.flow_encryption_key)); eng=build_engine(os.environ["PORTAL_DATABASE_URL"]); f=build_session_factory(eng); now=datetime.now(UTC)
try:
  with f() as s:
    r=IdentityRepository(s); p=r.create_principal(principal_id=os.environ["P"],issuer=c.issuer,subject=os.environ["S"],display_name="WH09 browser v4 acceptance",email=None,now=now); m=r.create_membership(membership_id=os.environ["M"],principal_id=p.principal_id,tenant_id="tenant-local",roles=(RoleName.USER,),valid_from=now,valid_until=now+timedelta(minutes=30),now=now); r.create_session(session_id_hash=crypto.hash_token(os.environ["T"]),csrf_token_hash=crypto.hash_token(os.environ["T"]+":csrf"),principal_id=p.principal_id,membership_id=m.membership_id,membership_version=m.membership_version,idp_session_id=None,authentication_time=now,mfa_satisfied=True,created_at=now,idle_expires_at=now+timedelta(minutes=15),absolute_expires_at=now+timedelta(minutes=30)); s.commit()
finally: eng.dispose()
'''

CLEAN = r'''
import os
from ai_platform.portal.control_plane.database import build_engine,build_session_factory
from ai_platform.portal.identity.crypto import IdentityCrypto,IdentitySecrets
from ai_platform.portal.identity.models import IdentityPrincipalRow,PortalSessionRow,TenantMembershipRow
from ai_platform.portal.identity.runtime import IdentityRuntimeConfig
c=IdentityRuntimeConfig.from_environment(); crypto=IdentityCrypto(IdentitySecrets(session_hmac_key=c.session_hmac_key,flow_encryption_key=c.flow_encryption_key)); h=crypto.hash_token(os.environ["T"]); eng=build_engine(os.environ["PORTAL_DATABASE_URL"]); f=build_session_factory(eng)
try:
  with f() as s:
    x=s.get(PortalSessionRow,h)
    if x is not None:
      if x.principal_id!=os.environ["P"] or x.membership_id!=os.environ["M"]: raise SystemExit("refusing non-task session cleanup")
      s.delete(x); s.flush()
    m=s.get(TenantMembershipRow,os.environ["M"])
    if m is not None:
      if m.principal_id!=os.environ["P"] or m.tenant_id!="tenant-local": raise SystemExit("refusing non-task membership cleanup")
      s.delete(m); s.flush()
    p=s.get(IdentityPrincipalRow,os.environ["P"])
    if p is not None:
      if p.subject!=os.environ["S"]: raise SystemExit("refusing non-task principal cleanup")
      s.delete(p)
    s.commit()
    assert s.get(PortalSessionRow,h) is None and s.get(TenantMembershipRow,os.environ["M"]) is None and s.get(IdentityPrincipalRow,os.environ["P"]) is None
finally: eng.dispose()
'''


def main() -> None:
    harness = os.environ["HARNESS_SHA"]
    root = Path(os.environ["RUNNER_TEMP"]) / "portal-wh09-browser-image"
    evidence = Path(os.environ["RUNNER_TEMP"]) / "portal-wh09-browser-v4.json"
    image = verify_target(harness, root / "approval.json", root / "browser-image.tar.gz")
    docker_exec(PREFLIGHT)
    token = secrets.token_urlsafe(48)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", token):
        raise RuntimeError("session token is not URL-safe")
    key = hashlib.sha256(f"{os.environ['GITHUB_RUN_ID']}:{os.environ['GITHUB_RUN_ATTEMPT']}".encode()).hexdigest()[:24]
    principal, membership = f"wh09-vp-{key}", f"wh09-vm-{key}"
    subject = f"urn:freqtrade:wh09-browser-v4:{os.environ['GITHUB_RUN_ID']}:{os.environ['GITHUB_RUN_ATTEMPT']}"
    owned = {"T": token, "P": principal, "M": membership, "S": subject}
    name = f"portal-wh09-browser-v4-{os.environ['GITHUB_RUN_ID']}-{os.environ['GITHUB_RUN_ATTEMPT']}"
    browser_rc = 1
    try:
        docker_exec(SEED, owned)
        create = ["docker","create","--name",name,"--label",f"ftai.task={TASK}","--label",f"ftai.harness_sha={harness}","--label",f"ftai.target_authorization_sha={TARGET}","--read-only","--tmpfs","/tmp:rw,noexec,nosuid,nodev,size=512m","--cap-drop","ALL","--security-opt","no-new-privileges:true","--shm-size","256m","--env",f"WICKHUNTER_BROWSER_ORIGIN={ORIGIN}","--env",f"WICKHUNTER_SESSION_TOKEN={token}","--env",f"WICKHUNTER_CSRF_TOKEN={token}:csrf","--env","WICKHUNTER_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium","--env","WICKHUNTER_BROWSER_NO_SANDBOX=1","--env","WICKHUNTER_BROWSER_EVIDENCE_PATH=/tmp/evidence.json",image]
        run(create)
        browser_rc = run(["docker","start","--attach",name],check=False).returncode
        run(["docker","cp",f"{name}:/tmp/evidence.json",str(evidence)])
    finally:
        docker_exec(CLEAN, owned)
        run(["docker","rm","-f",name],check=False)
        run(["docker","image","rm",image],check=False)
    if browser_rc != 0 or not evidence.is_file():
        raise RuntimeError("real Chromium v4 failed")
    e=json.loads(evidence.read_text())
    required={"result":"PASS","origin":ORIGIN,"mode":"shadow","authenticated":True,"fixture_cookie_present":False,"health_visible":True,"runtime_generation_converged":True,"reload_persistence":True}
    if any(e.get(k)!=v for k,v in required.items()) or e.get("decision_count",0)<=0 or e.get("no_trade_count",0)<=0:
        raise RuntimeError("real Chromium v4 evidence mismatch")
    e.update({"harness_source_sha":harness,"target_authorization_sha":TARGET,"trading_credentials_present":False,"order_adapter_present":False,"execution_enabled":False,"orders_submitted":0,"live_capital_authorized":False,"task_owned_session_absent":True,"task_owned_membership_absent":True,"task_owned_principal_absent":True,"browser_container_absent":True,"helper_image_absent":True})
    evidence.write_text(json.dumps(e,indent=2,sort_keys=True)+"\n")


if __name__ == "__main__":
    main()
