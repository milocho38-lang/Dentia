"use client";

export function Modal({
  open,
  title,
  children,
  onClose,
}: {
  open: boolean;
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-5 backdrop-blur-sm">
      <button
        aria-label="Cerrar diálogo"
        className="absolute inset-0"
        onClick={onClose}
      />
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className="relative z-10 max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-3xl bg-white p-7 shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4">
          <h2 id="modal-title" className="text-xl font-bold text-slate-900">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 hover:bg-slate-100"
            aria-label="Cerrar"
          >
            ×
          </button>
        </div>
        <div className="mt-5">{children}</div>
      </section>
    </div>
  );
}
