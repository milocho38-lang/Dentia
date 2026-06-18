import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-dentia-background px-6">
      <section className="text-center">
        <p className="text-sm font-bold uppercase tracking-[0.2em] text-green-700">
          Error 404
        </p>
        <h1 className="mt-4 text-3xl font-bold text-slate-900">
          Esta página no existe
        </h1>
        <p className="mt-3 text-slate-500">
          La dirección puede haber cambiado o no estar disponible.
        </p>
        <Link
          href="/dashboard"
          className="mt-7 inline-flex min-h-11 items-center rounded-xl bg-dentia-primary px-5 py-2.5 text-sm font-bold text-white"
        >
          Ir al dashboard
        </Link>
      </section>
    </main>
  );
}
