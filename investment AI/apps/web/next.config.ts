import type { NextConfig } from "next";
import path from "node:path";

const backend = process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname),
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: false },
  async rewrites() {
    return [
      { source: "/api/v1/:path*", destination: `${backend}/api/v1/:path*` },
      { source: "/health", destination: `${backend}/health` },
      { source: "/ready", destination: `${backend}/ready` },
    ];
  },
};

export default nextConfig;
