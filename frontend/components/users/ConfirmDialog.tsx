"use client";

import { Modal } from "@/components/shared/Modal";
import { Spinner } from "@/components/shared/Spinner";

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  busy,
  tone = "danger",
  onClose,
  onConfirm,
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  busy: boolean;
  tone?: "danger" | "primary";
  onClose: () => void;
  onConfirm: () => void;
}) {
  return (
    <Modal open={open} title={title} onClose={onClose}>
      <p className="text-sm leading-6 text-slate-600">{description}</p>
      <div className="mt-6 flex justify-end gap-3">
        <button
          type="button"
          onClick={onClose}
          className="min-h-11 rounded-xl border border-slate-300 px-4 font-bold text-slate-700"
        >
          Cancelar
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={onConfirm}
          className={`flex min-h-11 items-center gap-2 rounded-xl px-4 font-bold text-white disabled:opacity-60 ${
            tone === "danger" ? "bg-red-600" : "bg-dentia-primary"
          }`}
        >
          {busy && <Spinner className="h-4 w-4" />}
          {confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
