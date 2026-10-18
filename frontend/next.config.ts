import type { NextConfig } from "next";
import { buildConsentPortalCsp } from "./lib/consentCsp";

const backendPort = process.env.DENTIA_BACKEND_PORT;
const apiProxyTarget = backendPort
  ? `http://127.0.0.1:${backendPort}`
  : process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";
const consentPortalCsp = buildConsentPortalCsp(process.env.NODE_ENV);

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    // The backend enforces 25 MiB. Keep enough room for multipart framing so
    // the backend receives the complete body and remains the source of truth.
    proxyClientMaxBodySize: "27mb",
  },
  async headers() {
    return [
      {
        source: "/consentimiento/:path*",
        headers: [
          { key: "Cache-Control", value: "no-store, max-age=0" },
          { key: "Pragma", value: "no-cache" },
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Robots-Tag", value: "noindex, nofollow" },
          {
            key: "Content-Security-Policy",
            value: consentPortalCsp,
          },
        ],
      },
    ];
  },
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
