"use client";

import { useState } from "react";
import { Modal } from "@/components/shared/Modal";

export function TemporaryPasswordDialog({
  password,
  onClose,
}: {
  password: string | null;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);
  return (
    <Modal
      open={Boolean(password)}
      title="Contraseña temporal"
      onClose={onClose}
    >
      <p className="text-sm leading-6 text-slate-600">
        Esta contraseña se muestra una sola vez. Entrégala al usuario por un
        canal seguro; deberá cambiarla al iniciar sesión.
      </p>
      <div className="mt-5 rounded-2xl border border-green-200 bg-green-50 p-4">
        <code className="break-all text-base font-bold text-green-900">
          {password}
        </code>
      </div>
      <button
        type="button"
        onClick={async () => {
          if (password) await navigator.clipboard.writeText(password);
          setCopied(true);
        }}
        className="mt-4 min-h-11 w-full rounded-xl bg-dentia-primary px-4 font-bold text-white hover:bg-green-700"
      >
        {copied ? "Copiada" : "Copiar contraseña"}
      </button>
      <button
        type="button"
        onClick={onClose}
        className="mt-3 min-h-11 w-full rounded-xl border border-slate-300 px-4 font-bold text-slate-700 hover:bg-slate-50"
      >
        Ya la guardé
      </button>
    </Modal>
  );
}
