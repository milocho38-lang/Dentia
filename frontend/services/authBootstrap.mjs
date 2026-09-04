export const AUTH_REDIRECT_ONLY_PATHS = Object.freeze(["/"]);

export function shouldBootstrapAuth(pathname) {
  return !AUTH_REDIRECT_ONLY_PATHS.includes(pathname);
}
