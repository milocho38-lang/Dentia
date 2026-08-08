export interface WebCryptoUuidSource {
  randomUUID?: () => `${string}-${string}-${string}-${string}-${string}`;
  getRandomValues?: <T extends ArrayBufferView | null>(array: T) => T;
}

export class SecureRandomUuidUnavailableError extends Error {}
export function secureRandomUuid(cryptoSource?: WebCryptoUuidSource): string;
