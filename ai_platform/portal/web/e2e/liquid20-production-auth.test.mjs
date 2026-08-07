import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { once } from "node:events";
import { test } from "node:test";

const webPort = 3199;
const identityPort = 3200;
const baseUrl = `http://127.0.0.1:${webPort}`;
const routes = [
  "/api/market/liquidations?limit=10",
  "/api/market/liquidations/summary",
  "/api/market/liquidations/health",
];

function token(label) {
  return `${label}-${"x".repeat(64)}`.slice(0, 48);
}

const tokens = Object.fromEntries(
  [
    "valid",
    "forged",
    "expired",
    "revoked",
    "unknown",
    "wrong-tenant",
    "no-permission",
    "membership-mismatch",
    "unavailable",
    "timeout",
    "malformed-response",
    "invalid-contract",
  ].map((label) => [label, token(label)]),
);

function session(overrides = {}) {
  return {
    principal_id: "principal-a",
    membership_id: "membership-a",
    tenant_id: "tenant-a",
    roles: ["user"],
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
  throw new Error("Next.js Liquid20 production-identity test server did not start");
}

async function request(path, sessionToken) {
  const cookie = sessionToken
    ? `other_cookie=must-not-forward; __Host-portal_session=${sessionToken}`
    : "";
  const response = await fetch(`${baseUrl}${path}`, {
    headers: cookie ? { cookie } : {},
  });
  return { response, body: await response.text() };
}

test("every Liquid20 local-read route calls current-session authorization", async () => {
  const routeFiles = [
    new URL("../app/api/market/liquidations/route.ts", import.meta.url),
    new URL("../app/api/market/liquidations/summary/route.ts", import.meta.url),
    new URL("../app/api/market/liquidations/health/route.ts", import.meta.url),
  ];
  for (const routeFile of routeFiles) {
    const source = await readFile(routeFile, "utf8");
    assert.match(source, /await authorizeLiquidationRequest\(request\)/u, routeFile.pathname);
  }
});

test("production Liquid20 routes validate the authoritative session", async (t) => {
  let leakedCookie = false;
  const identity = createServer((incoming, response) => {
    if (incoming.url !== "/v1/identity/session") return writeJson(response, 404, { detail: "missing" });
    if ((incoming.headers.cookie ?? "").includes("other_cookie")) leakedCookie = true;
    const value = cookieToken(incoming);
    if (value === tokens.timeout) return setTimeout(() => writeJson(response, 200, session()), 500);
    if (value === tokens.unavailable) return incoming.socket.destroy();
    if (value === tokens["malformed-response"]) {
      response.writeHead(200, { "content-type": "application/json" });
      return response.end("{");
    }
    if (value === tokens["invalid-contract"]) return writeJson(response, 200, {});
    if (value === tokens.valid) return writeJson(response, 200, session());
    if (value === tokens.expired) {
      return writeJson(response, 200, session({ idle_expires_at: "2026-07-31T00:00:00Z" }));
    }
    if (value === tokens["wrong-tenant"]) {
      return writeJson(response, 200, session({ membership_id: "membership-b", tenant_id: "tenant-b" }));
    }
    if (value === tokens["no-permission"]) return writeJson(response, 200, session({ roles: ["service"] }));
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
        PORTAL_LIQUIDATIONS_TENANT_ID: "tenant-a",
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

  await waitForServer(`${baseUrl}${routes[0]}`, next);

  for (const route of routes) {
    const missing = await request(route);
    assert.equal(missing.response.status, 401, `${route}: missing`);
    assert.equal(missing.response.headers.get("cache-control"), "private, no-store", `${route}: missing`);

    for (const label of ["forged", "expired", "revoked", "unknown", "membership-mismatch"]) {
      const result = await request(route, tokens[label]);
      assert.equal(result.response.status, 401, `${route}: ${label}`);
      assert.equal(result.response.headers.get("cache-control"), "private, no-store", `${route}: ${label}`);
      assert.equal(result.body.includes(tokens[label]), false, `${route}: ${label}`);
    }

    const malformed = await request(route, "malformed cookie value");
    assert.equal(malformed.response.status, 401, `${route}: malformed`);

    for (const label of ["wrong-tenant", "no-permission"]) {
      const result = await request(route, tokens[label]);
      assert.equal(result.response.status, 403, `${route}: ${label}`);
      assert.equal(result.body.includes(tokens[label]), false, `${route}: ${label}`);
    }

    for (const label of ["unavailable", "timeout", "malformed-response", "invalid-contract"]) {
      const result = await request(route, tokens[label]);
      assert.equal(result.response.status, 503, `${route}: ${label}`);
      assert.equal(result.body.includes(tokens[label]), false, `${route}: ${label}`);
    }

    const valid = await request(route, tokens.valid);
    assert.equal(valid.response.status, 200, `${route}: valid`);
    assert.equal(valid.response.headers.get("cache-control"), "private, no-store", `${route}: valid`);
  }

  const fixtureBypass = await fetch(`${baseUrl}${routes[0]}`, {
    headers: { cookie: "portal_fixture_identity_state=authenticated; portal_fixture_session=fixture-session-authenticated" },
  });
  assert.equal(fixtureBypass.status, 401);
  assert.equal(leakedCookie, false);
  for (const value of Object.values(tokens)) assert.equal(logs.includes(value), false, value);
});
