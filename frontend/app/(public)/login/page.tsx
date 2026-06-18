import type { Metadata } from "next";
import { Suspense } from "react";
import { BrandMark } from "@/components/brand/BrandMark";
import { LoginForm } from "@/components/auth/LoginForm";
import { Spinner } from "@/components/shared/Spinner";

export const metadata: Metadata = {
  title: "Iniciar sesión",
};

const benefits = [
  "Operación clara para todo el equipo",
  "Acceso según roles y permisos",
  "Contexto preparado para múltiples sedes",
];

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-white lg:grid lg:grid-cols-[1.04fr_0.96fr]">
      <section className="relative hidden min-h-screen overflow-hidden bg-slate-950 px-12 py-10 text-white lg:flex lg:flex-col xl:px-16">
        <div className="absolute -right-28 -top-28 h-96 w-96 rounded-full bg-green-500/20 blur-3xl" />
        <div className="absolute -bottom-40 -left-28 h-[30rem] w-[30rem] rounded-full bg-emerald-700/30 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_35%,rgba(34,197,94,0.13),transparent_38%)]" />

        <div className="relative z-10">
          <BrandMark inverse />
        </div>

        <div className="relative z-10 my-auto max-w-xl py-14">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-green-300">
            Gestión Odontológica Inteligente
          </p>
          <h2 className="mt-5 text-5xl font-bold leading-[1.08] tracking-tight xl:text-6xl">
            Tu consultorio,
            <span className="block text-green-400">bien organizado.</span>
          </h2>
          <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">
            Un espacio seguro y sencillo para coordinar el trabajo clínico y
            administrativo de cada día.
          </p>

          <ul className="mt-10 space-y-4">
            {benefits.map((benefit) => (
              <li key={benefit} className="flex items-center gap-3 text-slate-200">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-500/20 text-green-300">
                  <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none">
                    <path
                      d="m5.5 10 3 3 6-6"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </span>
                {benefit}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative z-10 text-xs text-slate-500">
          © 2026 Dentia. Tecnología pensada para la práctica odontológica.
        </p>
      </section>

      <section className="flex min-h-screen flex-col bg-dentia-background px-6 py-7 sm:px-10 lg:px-14 xl:px-20">
        <div className="mb-10 lg:hidden">
          <BrandMark />
        </div>
        <div className="flex flex-1 items-center justify-center py-6">
          <Suspense
            fallback={
              <div className="flex items-center gap-3 text-slate-500">
                <Spinner className="h-6 w-6 text-dentia-primary" />
                Preparando acceso…
              </div>
            }
          >
            <LoginForm />
          </Suspense>
        </div>
        <p className="mt-8 text-center text-xs text-slate-400 lg:hidden">
          Gestión Odontológica Inteligente
        </p>
      </section>
    </main>
  );
}
