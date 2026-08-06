import type { NextConfig } from "next";

import { privateNoStoreResponseHeaders } from "./lib/response-cache-policy";
import { invariantSecurityHeaders } from "./lib/security-headers";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [...invariantSecurityHeaders(), ...privateNoStoreResponseHeaders()],
      },
    ];
  },
};

export default nextConfig;
