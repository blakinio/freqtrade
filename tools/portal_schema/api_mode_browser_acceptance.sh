#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_SHA:?GITHUB_SHA is required}"
: "${PORTAL_DATABASE_URL:?PORTAL_DATABASE_URL is required}"

control_image="portal-control-plane:${GITHUB_SHA}"
web_image="portal-web:${GITHUB_SHA}"
control="portal-api-browser-control-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
web="portal-api-browser-web-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
proxy_pid=""
browser_script=""

cleanup() {
  if [[ -n "$proxy_pid" ]]; then
    kill "$proxy_pid" >/dev/null 2>&1 || true
  fi
  if [[ -n "$browser_script" ]]; then
    rm -f "$browser_script"
  fi
  docker rm -f "$web" "$control" >/dev/null 2>&1 || true
}
trap cleanup EXIT

mkdir -p artifacts

docker run --rm -i --network host \
  --env PORTAL_DATABASE_URL \
  --entrypoint python \
  "$control_image" - <<'PY'
from datetime import UTC, datetime, timedelta
import os

from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.identity.crypto import IdentityCrypto, IdentitySecrets
from ai_platform.portal.identity.repository import IdentityRepository

session_token = "browser-real-session-token-" + "s" * 40
csrf_token = "browser-real-csrf-token-" + "c" * 40
crypto = IdentityCrypto(
    IdentitySecrets(
        session_hmac_key=b"1" * 32,
        flow_encryption_key=b"0" * 32,
    )
)
engine = build_engine(os.environ["PORTAL_DATABASE_URL"])
session_factory = build_session_factory(engine)
now = datetime.now(UTC)
try:
    with session_factory() as session:
        repository = IdentityRepository(session)
        principal = repository.create_principal(
            principal_id="browser-principal",
            issuer="https://issuer.example/application/o/portal/",
            subject="browser-subject",
            display_name="Browser Operator",
            email=None,
            now=now,
        )
        membership = repository.create_membership(
            membership_id="browser-membership",
            principal_id=principal.principal_id,
            tenant_id="ci-tenant",
            roles=(RoleName.TRADER,),
            valid_from=now,
            valid_until=None,
            now=now,
        )
        repository.create_session(
            session_id_hash=crypto.hash_token(session_token),
            csrf_token_hash=crypto.hash_token(csrf_token),
            principal_id=principal.principal_id,
            membership_id=membership.membership_id,
            membership_version=membership.membership_version,
            idp_session_id="browser-idp-session",
            authentication_time=now,
            mfa_satisfied=True,
            created_at=now,
            idle_expires_at=now + timedelta(minutes=30),
            absolute_expires_at=now + timedelta(hours=4),
        )
        session.commit()
finally:
    engine.dispose()
PY

key="$(python - <<'PY'
import base64
print(base64.urlsafe_b64encode(b"1" * 32).decode("ascii").rstrip("="))
PY
)"
flow_key="$(python - <<'PY'
import base64
print(base64.urlsafe_b64encode(b"0" * 32).decode("ascii").rstrip("="))
PY
)"

docker run --detach --name "$control" --network host \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --env PORTAL_DATABASE_URL \
  --env PORTAL_ENVIRONMENT=production \
  --env PORTAL_IDENTITY_CLIENT_ID=synthetic-client \
  --env PORTAL_IDENTITY_CLIENT_SECRET=synthetic-client-secret \
  --env PORTAL_IDENTITY_FLOW_ENCRYPTION_KEY_B64="$flow_key" \
  --env PORTAL_IDENTITY_ISSUER=https://issuer.example/application/o/portal/ \
  --env PORTAL_IDENTITY_REDIRECT_URI=https://portal.example/api/identity/callback \
  --env PORTAL_IDENTITY_SESSION_HMAC_KEY_B64="$key" \
  --env PORTAL_IDENTITY_TRANSPORT_MODE=secure_https \
  "$control_image"

for _ in $(seq 1 60); do
  if curl --fail --silent http://127.0.0.1:8000/readyz > artifacts/api-mode-browser-ready.json; then
    break
  fi
  sleep 2
done
test -s artifacts/api-mode-browser-ready.json

docker run --detach --name "$web" --network host \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=32m \
  --tmpfs /app/.next/cache:rw,noexec,nosuid,nodev,size=64m,uid=1000,gid=1000 \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --env PORTAL_WEB_DATA_MODE=api \
  --env PORTAL_ENVIRONMENT=production \
  --env PORTAL_IDENTITY_FIXTURE_MODE=disabled \
  --env PORTAL_IDENTITY_TRANSPORT_MODE=https \
  --env PORTAL_IDENTITY_ISSUER=https://issuer.example/application/o/portal/ \
  --env PORTAL_CONTROL_PLANE_URL=http://127.0.0.1:8000 \
  --env PORTAL_LIQUIDATIONS_DATA_ROOT=/tmp/no-liquidations \
  "$web_image"

for _ in $(seq 1 60); do
  status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$web")"
  [[ "$status" == "healthy" ]] && break
  if [[ "$status" =~ ^(unhealthy|exited|dead)$ ]]; then
    docker logs "$web"
    exit 1
  fi
  sleep 2
done
test "$(docker inspect --format '{{.State.Health.Status}}' "$web")" = "healthy"

pushd ai_platform/portal/web >/dev/null
npm ci
npx playwright install --with-deps chromium

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$RUNNER_TEMP/portal-api-browser.key" \
  -out "$RUNNER_TEMP/portal-api-browser.crt" \
  -days 1 \
  -subj "/CN=127.0.0.1" \
  -addext "subjectAltName=IP:127.0.0.1" >/dev/null 2>&1

cat > "$RUNNER_TEMP/portal-api-browser-proxy.mjs" <<'JS'
import fs from "node:fs";
import http from "node:http";
import https from "node:https";

const [keyPath, certPath] = process.argv.slice(2);
const server = https.createServer(
  { key: fs.readFileSync(keyPath), cert: fs.readFileSync(certPath) },
  (request, response) => {
    const upstream = http.request(
      {
        hostname: "127.0.0.1",
        port: 3000,
        path: request.url,
        method: request.method,
        headers: { ...request.headers, host: "127.0.0.1:3000" },
      },
      (upstreamResponse) => {
        response.writeHead(upstreamResponse.statusCode ?? 502, upstreamResponse.headers);
        upstreamResponse.pipe(response);
      },
    );
    upstream.on("error", () => {
      response.writeHead(502);
      response.end();
    });
    request.pipe(upstream);
  },
);
server.listen(3443, "127.0.0.1");
JS
node "$RUNNER_TEMP/portal-api-browser-proxy.mjs" \
  "$RUNNER_TEMP/portal-api-browser.key" "$RUNNER_TEMP/portal-api-browser.crt" \
  > "$RUNNER_TEMP/portal-api-browser-proxy.log" 2>&1 &
proxy_pid=$!

for _ in $(seq 1 30); do
  curl --insecure --fail --silent https://127.0.0.1:3443/login >/dev/null && break
  sleep 1
done

browser_script=".portal-api-mode-browser-${GITHUB_RUN_ID:-local}.mjs"
cat > "$browser_script" <<'JS'
import { chromium } from "@playwright/test";
import fs from "node:fs";

const origin = "https://127.0.0.1:3443";
const sessionToken = "browser-real-session-token-" + "s".repeat(40);
const csrfToken = "browser-real-csrf-token-" + "c".repeat(40);
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ ignoreHTTPSErrors: true });
await context.addCookies([
  {
    name: "__Host-portal_session",
    value: sessionToken,
    url: origin,
    secure: true,
    httpOnly: true,
    sameSite: "Lax",
  },
  {
    name: "__Host-portal_csrf",
    value: csrfToken,
    url: origin,
    secure: true,
    httpOnly: false,
    sameSite: "Lax",
  },
]);
const page = await context.newPage();
const response = await page.goto(`${origin}/bots`, { waitUntil: "networkidle" });
if (!response || response.status() !== 200) {
  throw new Error(`bots page failed: ${response?.status()}`);
}
await page.getByText("Preserved dry-run bot", { exact: true }).waitFor();
await page.getByText("ci-preserved-bot", { exact: true }).waitFor();

const mutation = await page.evaluate(async (token) => {
  const response = await fetch("/api/bots", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-csrf-token": token,
    },
    body: JSON.stringify({
      bot_id: "ci-browser-bot",
      name: "Chromium API-mode dry-run bot",
      spec: {
        tenant_id: "ci-tenant",
        strategy_version: "ci-strategy-v1",
        model_version: "ci-model-v1",
        risk_policy_version: "ci-risk-v1",
        exchange_connection_ref: "ci-exchange-reference",
        pair_universe: ["SOL/USDT"],
        timeframe: "5m",
        capital_allocation: "25",
        capital_currency: "USDT",
        runtime_version: "ci-runtime-v1",
        config_revision: 1,
        environment: "production",
        execution_mode: "dry_run",
      },
    }),
  });
  return { status: response.status, body: await response.text() };
}, csrfToken);
if (mutation.status !== 201) {
  throw new Error(`browser mutation failed: ${mutation.status}: ${mutation.body}`);
}

await page.reload({ waitUntil: "networkidle" });
await page.getByText("Chromium API-mode dry-run bot", { exact: true }).waitFor();
await page.getByText("ci-browser-bot", { exact: true }).waitFor();
if ((await page.locator("body").innerText()).includes("fixture-session")) {
  throw new Error("fixture identity marker leaked into API-mode journey");
}
fs.writeFileSync(
  "../../../artifacts/api-mode-browser-e2e.json",
  JSON.stringify(
    {
      status: "pass",
      chromium: "pass",
      web_data_mode: "api",
      identity_fixture_mode: "disabled",
      authenticated_backend_read: "pass",
      authenticated_dry_run_mutation: "pass",
      refresh_persistence: "pass",
      request_interception: false,
      live_capital_authorized: false,
      secret_values_recorded: false,
    },
    null,
    2,
  ) + "\n",
);
await browser.close();
JS
node "$browser_script"
rm -f "$browser_script"
browser_script=""
popd >/dev/null

docker run --rm -i --network host \
  --env PORTAL_DATABASE_URL \
  --entrypoint python \
  "$control_image" - <<'PY' > artifacts/api-mode-browser-persistence.json
import json
import os
from sqlalchemy import text
from ai_platform.portal.control_plane.database import build_engine

engine = build_engine(os.environ["PORTAL_DATABASE_URL"])
try:
    with engine.connect() as connection:
        rows = dict(
            connection.execute(
                text(
                    "SELECT bot_id, COUNT(*) FROM portal_bots "
                    "WHERE tenant_id='ci-tenant' GROUP BY bot_id"
                )
            ).all()
        )
    expected = {"ci-api-bot": 1, "ci-browser-bot": 1, "ci-preserved-bot": 1}
    assert rows == expected, rows
    print(
        json.dumps(
            {
                "status": "pass",
                "rows": rows,
                "live_capital_authorized": False,
                "secret_values_recorded": False,
            },
            sort_keys=True,
        )
    )
finally:
    engine.dispose()
PY
