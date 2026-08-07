import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { once } from "node:events";
import { test } from "node:test";

const webPort = 3197;
const identityPort = 3198;
const baseUrl = `http://127.0.0.1:${webPort}`;
const routes = [
  "/api/market/evidence/summary",
  "/api/market/evidence/sources",
  "/api/market/evidence/instruments?page=1&page_size=10",
  "/api/market/evidence/runs?page=1&page_size=10",
];

function token(label) {
  return `${label}-${"x".repeat(64)}`.slice(0, 48);
}

const tokens = Object.fromEntries(
  ["valid", "forged", "expired", "revoked", "unknown", "wrong-tenant", "no-permission", "membership-mismatch", "unavailable", "timeout", "malformed-response"].map(
    (label) => [label, token(label)],
  ),
);

function session(overrides = {}) {
  return {
    principal_id: "principal-a",
    membership_id: "membership-a",
    tenant_id: "tenant-a",
    roles: ["analyst"],
    membership_version: 7,
    mfa_satisfied: true,
    authentication_time: "2026-08-01T12:00:00Z",
    created_at: "2026-08-01T12:00:00Z",
    last_seen_at: "2026-08-01T12:00:00Z",
    idle_expires_at: "2099-08-01T13:00:00Z",
    absolute_expires_at: "2099-08-01T20:00:00Z",
    ...overrides,
  };
}

function cookieToken(request) {
  const match = /(?:^|;\s*)__Host-portal_session=([^;]+)/u.exec(request.headers.cookie ?? "");
  return match?.[1] ?? null;
}

function writeJson(response, status, payload) {
  response.writeHead(status, { "content-type": "application/json", "cache-control": "no-store" });
  response.end(JSON.stringify(payload));
}

function assertPrivateNoStore(response, label) {
  assert.equal(response.headers.get("cache-control"), "private, no-store", label);
}

async function waitForServer(url, child) {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    if (child.exitCode !== null) throw new Error(`Next.js exited with ${child.exitCode}`);
    try {
      await fetch(url);
      return;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
  throw new Error("Next.js production-identity test server did not start");
}

async function request(path, sessionToken) {
  const response = await fetch(`${baseUrl}${path}`, {
    headers: sessionToken ? { cookie: `__Host-portal_session=${sessionToken}` } : {},
  });
  return { response, body: await response.text() };
}

test("production Market Evidence routes validate the authoritative session", async (t) => {
  const identity = createServer((incoming, response) => {
    if (incoming.url !== "/v1/identity/session") return writeJson(response, 404, { detail: "missing" });
    const value = cookieToken(incoming);
    if (value === tokens.timeout) return setTimeout(() => writeJson(response, 200, session()), 500);
    if (value === tokens.unavailable) return incoming.socket.destroy();
    if (value === tokens["malformed-response"]) {
      response.writeHead(200, { "content-type": "application/json" });
      return response.end("{");
    }
    if (value === tokens.valid) return writeJson(response, 200, session());
    if (value === tokens.expired) {
      return writeJson(response, 200, session({ idle_expires_at: "2026-07-31T00:00:00Z" }));
    }
    if (value === tokens["wrong-tenant"]) {
      return writeJson(response, 200, session({ membership_id: "membership-b", tenant_id: "tenant-b" }));
    }
    if (value === tokens["no-permission"]) return writeJson(response, 200, session({ roles: ["user"] }));
    if ([tokens.revoked, tokens.unknown, tokens["membership-mismatch"], tokens.forged].includes(value)) {
      return writeJson(response, 401, { detail: "session is not authorized" });
    }
    return writeJson(response, 401, { detail: "portal session is missing" });
  });
  identity.listen(identityPort, "127.0.0.1");
  await once(identity, "listening");

  let logs = "";
  const next = spawn(
    process.execPath,
    ["node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", String(webPort)],
    {
      cwd: new URL("../", import.meta.url),
      env: {
        ...process.env,
        PORTAL_WEB_DATA_MODE: "fixture",
        PORTAL_ENVIRONMENT: "production",
        PORTAL_IDENTITY_FIXTURE_MODE: "enabled",
        PORTAL_CONTROL_PLANE_URL: `http://127.0.0.1:${identityPort}`,
        PORTAL_MARKET_EVIDENCE_TENANT_ID: "tenant-a",
        PORTAL_IDENTITY_SESSION_TIMEOUT_MS: "75",
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  next.stdout.on("data", (chunk) => { logs += chunk.toString(); });
  next.stderr.on("data", (chunk) => { logs += chunk.toString(); });
  t.after(async () => {
    next.kill();
    identity.close();
    await Promise.race([once(next, "exit"), new Promise((resolve) => setTimeout(resolve, 2_000))]);
  });

  await waitForServer(`${baseUrl}/api/market/evidence/summary`, next);

  const missing = await request(routes[0]);
  assert.equal(missing.response.status, 401);
  assertPrivateNoStore(missing.response, "missing session cache policy");

  for (const label of ["forged", "expired", "revoked", "unknown", "membership-mismatch"]) {
    const result = await request(routes[0], tokens[label]);
    assert.equal(result.response.status, 401, label);
    assertPrivateNoStore(result.response, label);
    assert.equal(result.body.includes(tokens[label]), false, label);
  }

  const malformed = await request(routes[0], "malformed cookie value");
  assert.equal(malformed.response.status, 401);

  for (const label of ["wrong-tenant", "no-permission"]) {
    const result = await request(routes[0], tokens[label]);
    assert.equal(result.response.status, 403, label);
    assert.equal(result.body.includes(tokens[label]), false, label);
  }

  for (const label of ["unavailable", "timeout", "malformed-response"]) {
    const result = await request(routes[0], tokens[label]);
    assert.equal(result.response.status, 503, label);
    assert.equal(result.body.includes(tokens[label]), false, label);
  }

  for (const route of routes) {
    const result = await request(route, tokens.valid);
    assert.equal(result.response.status, 200, route);
    assertPrivateNoStore(result.response, route);
  }

  const fixtureBypass = await fetch(`${baseUrl}${routes[0]}`, {
    headers: { cookie: "portal_fixture_identity_state=authenticated; portal_fixture_session=fixture-session-authenticated" },
  });
  assert.equal(fixtureBypass.status, 401);
  for (const value of Object.values(tokens)) assert.equal(logs.includes(value), false, value);
});
