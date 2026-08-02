"use client";

import { useEffect, useRef, useState } from "react";
import { Modal } from "@/components/shared/Modal";
import { copyTextSecurely } from "@/lib/secureClipboard.mjs";

export function TemporaryPasswordDialog({
  password,
  onClose,
}: {
  password: string | null;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const [manualCopy, setManualCopy] = useState(false);
  const passwordInputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    setCopied(false);
    setManualCopy(false);
  }, [password]);
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
        <input
          ref={passwordInputRef}
          readOnly
          value={password ?? ""}
          aria-label="Contraseña temporal"
          className="w-full bg-transparent text-base font-bold text-green-900 outline-none"
        />
      </div>
      <button
        type="button"
        onClick={async () => {
          if (!password) return;
          const success = await copyTextSecurely(password);
          setCopied(success);
          setManualCopy(!success);
        }}
        className="mt-4 min-h-11 w-full rounded-xl bg-dentia-primary px-4 font-bold text-white hover:bg-green-700"
      >
        {copied ? "Copiada" : "Copiar contraseña"}
      </button>
      {manualCopy && (
        <div className="mt-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
          <p>No fue posible copiar automáticamente. Seleccione la contraseña para copiarla.</p>
          <button
            type="button"
            onClick={() => {
              passwordInputRef.current?.focus();
              passwordInputRef.current?.select();
            }}
            className="mt-2 font-bold underline"
          >
            Seleccionar contraseña
          </button>
        </div>
      )}
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
