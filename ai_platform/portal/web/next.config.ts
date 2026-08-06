import type { NextConfig } from "next";

import { privateNoStoreResponseHeaders } from "./lib/response-cache-policy";
import { invariantSecurityHeaders } from "./lib/security-headers";

const dynamicResponseSource =
  "/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: invariantSecurityHeaders(),
      },
      {
        source: dynamicResponseSource,
        headers: privateNoStoreResponseHeaders(),
      },
    ];
  },
};

export default nextConfig;
