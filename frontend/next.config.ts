import type { NextConfig } from "next";

const backendPort = process.env.DENTIA_BACKEND_PORT;
const apiProxyTarget = backendPort
  ? `http://127.0.0.1:${backendPort}`
  : process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
