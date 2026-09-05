import type { NextConfig } from "next";

const appUrl = (process.env.NEXT_PUBLIC_APP_URL ?? "https://app.dentiapro.com").replace(/\/$/, "");

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "base-uri 'self'",
      "connect-src 'self'",
      "font-src 'self' data:",
      "form-action 'self'",
      "frame-ancestors 'none'",
      "img-src 'self' data: blob:",
      "object-src 'none'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
    ].join("; "),
  },
] as const;

const applicationRedirects = [
  "/login",
  "/dashboard",
  "/pacientes/:path*",
  "/agenda/:path*",
  "/tratamientos/:path*",
  "/finanzas/:path*",
  "/reportes/:path*",
  "/seguimientos/:path*",
  "/configuracion/:path*",
  "/cambiar-contrasena",
  "/sin-acceso",
] as const;

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  async headers() {
    return [{ source: "/:path*", headers: [...securityHeaders] }];
  },
  async redirects() {
    return [
      {
        source: "/consentimiento/:path*",
        destination: `${appUrl}/consentimiento/:path*`,
        permanent: false,
      },
      ...applicationRedirects.map((source) => ({
        source,
        destination: `${appUrl}${source}`,
        permanent: false,
      })),
    ];
  },
  images: {
    formats: ["image/avif", "image/webp"],
  },
};

export default nextConfig;
