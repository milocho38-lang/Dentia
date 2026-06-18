export function getSafeReturnUrl(value: string | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return "/dashboard";
  }
  if (value.startsWith("/login")) {
    return "/dashboard";
  }
  return value;
}
