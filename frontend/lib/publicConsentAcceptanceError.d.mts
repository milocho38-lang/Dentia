export class PublicConsentRequestError extends Error {
  status: number;
  code: string;
  constructor(status: number, code?: string);
}
export function publicConsentRequestError(status: number, body: unknown): PublicConsentRequestError;
export function acceptanceErrorMessage(error: unknown): string;
