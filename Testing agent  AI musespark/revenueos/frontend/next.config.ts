import type { NextConfig } from "next";

const backend = process.env.BACKEND_URL ?? "http://localhost:8000";

const config: NextConfig = {
  // Docker builds set this. A plain `next start` needs the default output.
  output: process.env.NEXT_STANDALONE ? "standalone" : undefined,
  poweredByHeader: false,
  // Copilot answers can take a while, so allow more than the default proxy timeout.
  experimental: { proxyTimeout: 120_000 },
  // Browser calls go to /api on the same origin, which keeps the auth cookie first-party.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backend}/:path*` }];
  },
};

export default config;
