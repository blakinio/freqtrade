import type { NextConfig } from "next";

import { invariantSecurityHeaders } from "./lib/security-headers";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: invariantSecurityHeaders(),
      },
    ];
  },
};

export default nextConfig;
