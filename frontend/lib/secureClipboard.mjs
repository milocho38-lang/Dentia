function currentEnvironment(environment) {
  return {
    navigatorRef: environment.navigatorRef ?? globalThis.navigator,
    documentRef: environment.documentRef ?? globalThis.document,
    isSecureContext:
      environment.isSecureContext ?? globalThis.isSecureContext === true,
  };
}

export async function copyTextSecurely(value, environment = {}) {
  const { navigatorRef, documentRef, isSecureContext } =
    currentEnvironment(environment);
  const writeText = navigatorRef?.clipboard?.writeText;

  if (isSecureContext && typeof writeText === "function") {
    try {
      await writeText.call(navigatorRef.clipboard, value);
      return true;
    } catch {
      // Safari and browser permissions can reject even in a secure context.
    }
  }

  if (!documentRef?.body || typeof documentRef.createElement !== "function") {
    return false;
  }

  const textarea = documentRef.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "");
  textarea.setAttribute("aria-hidden", "true");
  Object.assign(textarea.style, {
    position: "fixed",
    insetInlineStart: "-9999px",
    top: "0",
    opacity: "0",
  });

  try {
    documentRef.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    textarea.setSelectionRange?.(0, value.length);
    return documentRef.execCommand?.("copy") === true;
  } catch {
    return false;
  } finally {
    textarea.remove();
  }
}
