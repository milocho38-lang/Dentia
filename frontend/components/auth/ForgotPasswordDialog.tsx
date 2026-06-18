"use client";

import { useEffect, useRef } from "react";

export function ForgotPasswordDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      closeButtonRef.current?.focus();
    }
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-5 backdrop-blur-sm"
      role="presentation"
      onMouseDown={(event) => {
        if (event.currentTarget === event.target) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="forgot-password-title"
        className="w-full max-w-md rounded-3xl border border-white/70 bg-white p-7 shadow-2xl"
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-green-50 text-dentia-primary">
          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none">
            <path
              d="M7 10V8a5 5 0 0 1 10 0v2m-9 0h8a2 2 0 0 1 2 2v7H6v-7a2 2 0 0 1 2-2Z"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <h2
          id="forgot-password-title"
          className="mt-5 text-xl font-bold text-slate-900"
        >
          Recuperación de contraseña
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          En el MVP, la recuperación es administrativa. Solicita al
          administrador de tu organización que restablezca tu contraseña y te
          entregue una credencial temporal por un canal seguro.
        </p>
        <p className="mt-3 text-sm leading-6 text-slate-500">
          Dentia no envía enlaces de recuperación por correo en esta versión.
        </p>
        <button
          ref={closeButtonRef}
          type="button"
          onClick={onClose}
          className="mt-6 min-h-11 w-full rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-bold text-white transition hover:bg-green-700"
        >
          Entendido
        </button>
      </section>
    </div>
  );
}
