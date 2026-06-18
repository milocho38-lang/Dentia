"use client";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-dentia-background px-6">
      <section className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-600">
          <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none">
            <path
              d="M12 8v5m0 3h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <h1 className="mt-5 text-2xl font-bold text-slate-900">
          No pudimos cargar esta pantalla
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Ocurrió un problema inesperado. Puedes intentar nuevamente.
        </p>
        <button
          type="button"
          onClick={reset}
          className="mt-6 min-h-11 rounded-xl bg-dentia-primary px-5 py-2.5 text-sm font-bold text-white transition hover:bg-green-700"
        >
          Reintentar
        </button>
      </section>
    </main>
  );
}
