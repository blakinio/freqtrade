"use client";

const CSRF_COOKIE_NAMES = ["__Host-portal_csrf", "portal_fixture_csrf"] as const;
const CSRF_HEADER_NAME = "x-csrf-token";
const unsafeMethods = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export async function csrfFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const method = (init.method ?? "GET").toUpperCase();
  if (!unsafeMethods.has(method)) return fetch(input, init);

  const headers = new Headers(init.headers);
  const csrfToken = readCsrfCookie();
  if (csrfToken) headers.set(CSRF_HEADER_NAME, csrfToken);
  return fetch(input, { ...init, headers });
}

export function readCsrfCookie(): string | null {
  if (typeof document === "undefined") return null;
  const cookies = new Map(
    document.cookie
      .split(";")
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => {
        const [name, ...rest] = item.split("=");
        try {
          return [name, decodeURIComponent(rest.join("="))] as const;
        } catch {
          return [name, rest.join("=")] as const;
        }
      }),
  );
  for (const name of CSRF_COOKIE_NAMES) {
    const value = cookies.get(name);
    if (value) return value;
  }
  return null;
}
