const MESSAGES = {
  DECLARATIONS_INCOMPLETE: "Debe confirmar todas las declaraciones antes de continuar.",
  IDENTITY_MISMATCH: "El nombre escrito no coincide con el consentimiento. Revíselo o contacte a la clínica.",
  SIGNATURE_INVALID: "No fue posible validar la firma. Límpiela, vuelva a dibujarla e intente nuevamente.",
  SESSION_INVALID: "La sesión venció o dejó de estar disponible. Solicite un nuevo acceso a la clínica.",
  REQUEST_STALE: "La solicitud cambió o dejó de estar vigente. Revise nuevamente el documento.",
  REQUEST_INVALID: "La solicitud está incompleta. Revise los datos e intente nuevamente.",
  TECHNICAL_ERROR: "No fue posible completar el envío. Sus datos permanecen en esta pantalla.",
};

export class PublicConsentRequestError extends Error {
  constructor(status, code = "TECHNICAL_ERROR") {
    super(MESSAGES[code] || MESSAGES.TECHNICAL_ERROR);
    this.name = "PublicConsentRequestError";
    this.status = status;
    this.code = code in MESSAGES ? code : "TECHNICAL_ERROR";
  }
}

export function publicConsentRequestError(status, body) {
  const structuredCode = body?.detail && typeof body.detail === "object" && !Array.isArray(body.detail)
    ? body.detail.code
    : body?.code;
  if (typeof structuredCode === "string") return new PublicConsentRequestError(status, structuredCode);
  if ([401, 403, 404].includes(status)) return new PublicConsentRequestError(status, "SESSION_INVALID");
  if (status === 409) return new PublicConsentRequestError(status, "REQUEST_STALE");
  if (status === 422) return new PublicConsentRequestError(status, "REQUEST_INVALID");
  return new PublicConsentRequestError(status);
}

export function acceptanceErrorMessage(error) {
  return error instanceof PublicConsentRequestError ? error.message : MESSAGES.TECHNICAL_ERROR;
}
