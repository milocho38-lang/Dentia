export const CONSENT_STATUS_CHANNEL = "dentia-consent-status";
export const CONSENT_SIGNED_EVENT = "dentia:consent-signed";

export function publishConsentSigned(acceptanceId, scope = globalThis) {
  if (!acceptanceId) return;
  const event = { type: CONSENT_SIGNED_EVENT, acceptanceId };
  if (typeof scope.BroadcastChannel === "function") {
    const channel = new scope.BroadcastChannel(CONSENT_STATUS_CHANNEL);
    channel.postMessage(event);
    channel.close();
  }
  if (scope.opener && scope.opener !== scope && typeof scope.opener.postMessage === "function") {
    scope.opener.postMessage(event, scope.location?.origin ?? "*");
  }
}

export function subscribeConsentSigned(callback, scope = globalThis) {
  let channel = null;
  const deliver = (event) => {
    const value = event?.data ?? event;
    if (value?.type === CONSENT_SIGNED_EVENT && typeof value.acceptanceId === "string") callback(value);
  };
  if (typeof scope.BroadcastChannel === "function") {
    channel = new scope.BroadcastChannel(CONSENT_STATUS_CHANNEL);
    channel.addEventListener("message", deliver);
  }
  const onWindowMessage = (event) => {
    if (event.origin === scope.location?.origin) deliver(event);
  };
  scope.addEventListener?.("message", onWindowMessage);
  return () => {
    channel?.removeEventListener("message", deliver);
    channel?.close();
    scope.removeEventListener?.("message", onWindowMessage);
  };
}
