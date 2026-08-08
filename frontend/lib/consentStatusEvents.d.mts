export type ConsentSignedEvent = { type: "dentia:consent-signed"; acceptanceId: string };
export declare const CONSENT_STATUS_CHANNEL: string;
export declare const CONSENT_SIGNED_EVENT: "dentia:consent-signed";
export declare function publishConsentSigned(acceptanceId: string, scope?: typeof globalThis): void;
export declare function subscribeConsentSigned(callback: (event: ConsentSignedEvent) => void, scope?: typeof globalThis): () => void;
