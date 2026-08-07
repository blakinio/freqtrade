export type PortalNodeEnvironment = "development" | "production" | "test";

export type SecurityHeader = Readonly<{
  key: string;
  value: string;
}>;

export type BrowserSecurityContext = Readonly<{
  nonce: string;
  contentSecurityPolicy: string;
  requestHeaders: Headers;
}>;

const NONCE_PATTERN = /^[A-Za-z0-9+/_=-]+$/;

const INVARIANT_SECURITY_HEADERS: readonly SecurityHeader[] = [
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  { key: "Cross-Origin-Resource-Policy", value: "same-origin" },
  { key: "Permissions-Policy", value: "camera=(), geolocation=(), microphone=(), payment=(), usb=()" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
];

export function invariantSecurityHeaders(): SecurityHeader[] {
  return INVARIANT_SECURITY_HEADERS.map(({ key, value }) => ({ key, value }));
}

export function createContentSecurityPolicyNonce(): string {
  const bytes = new Uint8Array(18);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes));
}

export function buildContentSecurityPolicy(
  nonce: string,
  environment: PortalNodeEnvironment = normalizedNodeEnvironment(process.env.NODE_ENV),
): string {
  if (!NONCE_PATTERN.test(nonce)) {
    throw new Error("Content Security Policy nonce contains unsupported characters");
  }

  const development = environment === "development";
  const scriptSources = ["'self'", `'nonce-${nonce}'`, "'strict-dynamic'"];
  const styleSources = ["'self'", `'nonce-${nonce}'`];
  const connectSources = ["'self'"];

  if (development) {
    scriptSources.push("'unsafe-eval'");
    styleSources.push("'unsafe-inline'");
    connectSources.push(
      "http://127.0.0.1:*",
      "http://localhost:*",
      "ws://127.0.0.1:*",
      "ws://localhost:*",
    );
  }

  const directives = [
    "default-src 'self'",
    `script-src ${scriptSources.join(" ")}`,
    `style-src ${styleSources.join(" ")}`,
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    `connect-src ${connectSources.join(" ")}`,
    "worker-src 'self' blob:",
    "manifest-src 'self'",
    "media-src 'none'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-src 'none'",
    "frame-ancestors 'none'",
  ];

  if (!development) directives.push("upgrade-insecure-requests");
  return directives.join("; ");
}

export function createBrowserSecurityContext(
  originalHeaders: Headers,
  environment: PortalNodeEnvironment = normalizedNodeEnvironment(process.env.NODE_ENV),
): BrowserSecurityContext {
  const nonce = createContentSecurityPolicyNonce();
  const contentSecurityPolicy = buildContentSecurityPolicy(nonce, environment);
  const requestHeaders = new Headers(originalHeaders);
  requestHeaders.set("Content-Security-Policy", contentSecurityPolicy);
  requestHeaders.set("x-nonce", nonce);
  return { nonce, contentSecurityPolicy, requestHeaders };
}

export function applyBrowserSecurityHeaders<T extends Response>(
  response: T,
  contentSecurityPolicy?: string,
): T {
  for (const { key, value } of INVARIANT_SECURITY_HEADERS) {
    response.headers.set(key, value);
  }
  if (contentSecurityPolicy) {
    response.headers.set("Content-Security-Policy", contentSecurityPolicy);
  }
  return response;
}

function normalizedNodeEnvironment(value: string | undefined): PortalNodeEnvironment {
  if (value === "development" || value === "test") return value;
  return "production";
}
