export function buildConsentPortalCsp(nodeEnv: string | undefined): string {
  const scriptSources = ["'self'", "'unsafe-inline'"];

  // Next dev requires dynamic evaluation for its development runtime and Fast Refresh.
  // Never reuse this relaxation outside NODE_ENV=development.
  if (nodeEnv === "development") scriptSources.push("'unsafe-eval'");

  return [
    "default-src 'self'",
    `script-src ${scriptSources.join(" ")}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "connect-src 'self'",
    "frame-ancestors 'none'",
    "base-uri 'none'",
    "form-action 'self'",
  ].join("; ");
}
