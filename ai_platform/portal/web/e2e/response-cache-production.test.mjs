import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { existsSync } from "node:fs";
import test, { after, before } from "node:test";

const host = "127.0.0.1";
const port = 3199;
const baseURL = `http://${host}:${port}`;
const authenticatedSessionCookie = "__Host-portal_session=cache-probe-session";
let server;
let output = "";

before(async () => {
  assert.equal(existsSync(".next/BUILD_ID"), true, "production build is required before this test");
  server = spawn(
    process.execPath,
    ["node_modules/next/dist/bin/next", "start", "--hostname", host, "--port", String(port)],
    {
      env: {
        ...process.env,
        PORTAL_WEB_DATA_MODE: "fixture",
        PORTAL_ENVIRONMENT: "test",
        PORTAL_IDENTITY_FIXTURE_MODE: "disabled",
        PORTAL_IDENTITY_TRANSPORT_MODE: "https",
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  server.stdout.on("data", (chunk) => {
    output += chunk.toString();
  });
  server.stderr.on("data", (chunk) => {
    output += chunk.toString();
  });
  await waitForServer();
});

after(async () => {
  if (!server || server.exitCode !== null) return;
  server.kill("SIGTERM");
  await Promise.race([
    once(server, "exit"),
    new Promise((resolve) => setTimeout(resolve, 5_000)),
  ]);
  if (server.exitCode === null) server.kill("SIGKILL");
});

test("production documents, redirects and API errors are private no-store", async () => {
  const login = await fetch(`${baseURL}/login`);
  assert.equal(login.status, 200);
  assertPrivateNoStore(login.headers);

  const redirect = await fetch(`${baseURL}/bots`, { redirect: "manual" });
  assert.ok([307, 308].includes(redirect.status));
  assertPrivateNoStore(redirect.headers);

  const unauthorized = await fetch(`${baseURL}/api/terminal`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      amount: "0.01",
      bot_id: "bot-btc-dryrun-01",
      pair: "BTC/USDT",
      side: "BUY",
    }),
  });
  assert.equal(unauthorized.status, 401);
  assertPrivateNoStore(unauthorized.headers);

  const notFound = await fetch(`${baseURL}/api/route-that-does-not-exist`, {
    headers: { cookie: authenticatedSessionCookie },
  });
  assert.equal(notFound.status, 404);
  assertFrameworkPrivateNoStore(notFound.headers);
});

test("production immutable Next assets retain framework cache policy", async () => {
  const login = await fetch(`${baseURL}/login`);
  const html = await login.text();
  const source = html.match(/<script[^>]+src="([^"]+)"/)?.[1];
  assert.ok(source, "rendered login page must include a Next script");

  const asset = await fetch(new URL(source, baseURL));
  assert.equal(asset.status, 200);
  const directives = cacheDirectives(asset.headers);
  assert.equal(directives.includes("public"), true);
  assert.equal(directives.includes("immutable"), true);
  assert.equal(directives.some((directive) => directive.startsWith("max-age=")), true);
});

async function waitForServer() {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    if (server.exitCode !== null) {
      throw new Error(`production server exited before readiness\n${output}`);
    }
    try {
      const response = await fetch(`${baseURL}/login`);
      if (response.status === 200) return;
    } catch {
      // Retry until the bounded readiness deadline.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`production server did not become ready\n${output}`);
}

function assertPrivateNoStore(headers) {
  assert.deepEqual(cacheDirectives(headers), ["private", "no-store"]);
}

function assertFrameworkPrivateNoStore(headers) {
  const directives = cacheDirectives(headers);
  assert.equal(directives.includes("private"), true, "framework response must remain private");
  assert.equal(directives.includes("no-store"), true, "framework response must retain no-store");
  assert.equal(directives.includes("public"), false, "framework response must not become public");
  assert.equal(directives.includes("immutable"), false, "framework response must not become immutable");
  assert.equal(
    directives.some((directive) => directive.startsWith("s-maxage=")),
    false,
    "framework response must not enable shared-cache freshness",
  );
  assert.equal(
    directives.some(
      (directive) => directive.startsWith("max-age=") && directive !== "max-age=0",
    ),
    false,
    "framework response must not enable positive browser-cache freshness",
  );
}

function cacheDirectives(headers) {
  return (headers.get("cache-control") ?? "")
    .split(",")
    .map((directive) => directive.trim().toLowerCase())
    .filter(Boolean);
}
