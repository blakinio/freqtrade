import {
  PortalIdentityConfigurationError,
  fixtureIdentityMode,
  localHttpIdentityMode,
} from "@/lib/identity";

const FROZEN_PUBLIC_PORTAL_ORIGIN = "https://quant.molehill.cloud";

export function portalPublicOrigin(requestOrigin: string): string {
  const configured = process.env.PORTAL_PUBLIC_ORIGIN?.trim();
  const candidate =
    configured ||
    (process.env.PORTAL_ENVIRONMENT === "production"
      ? FROZEN_PUBLIC_PORTAL_ORIGIN
      : requestOrigin);

  let url: URL;
  try {
    url = new URL(candidate);
  } catch {
    throw new PortalIdentityConfigurationError("PORTAL_PUBLIC_ORIGIN must be an absolute URL");
  }

  const localTest = fixtureIdentityMode() || localHttpIdentityMode();
  const allowedProtocol =
    url.protocol === "https:" ||
    (localTest && url.protocol === "http:" && isPrivateLocalHostname(url.hostname));
  if (!allowedProtocol) {
    throw new PortalIdentityConfigurationError(
      "PORTAL_PUBLIC_ORIGIN must use HTTPS outside local test mode",
    );
  }
  if (
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new PortalIdentityConfigurationError(
      "PORTAL_PUBLIC_ORIGIN must contain only scheme and authority",
    );
  }
  if (!configured && process.env.PORTAL_ENVIRONMENT !== "production" && !localTest) {
    throw new PortalIdentityConfigurationError("PORTAL_PUBLIC_ORIGIN is required");
  }
  return url.origin;
}

function isPrivateLocalHostname(hostname: string): boolean {
  if (hostname === "localhost" || hostname.endsWith(".localhost")) return true;
  if (hostname === "::1" || hostname.startsWith("127.") || hostname === "0.0.0.0") return true;
  if (hostname.startsWith("10.") || hostname.startsWith("192.168.")) return true;
  const match = /^172\.(\d{1,2})\./.exec(hostname);
  return match !== null && Number(match[1]) >= 16 && Number(match[1]) <= 31;
}
