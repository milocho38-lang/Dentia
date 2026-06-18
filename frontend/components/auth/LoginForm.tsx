"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { ForgotPasswordDialog } from "@/components/auth/ForgotPasswordDialog";
import { useAuth } from "@/hooks/useAuth";
import { getLoginErrorMessage } from "@/utils/apiErrors";
import { getSafeReturnUrl } from "@/utils/safeReturnUrl";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forgotOpen, setForgotOpen] = useState(false);
  const { login, status } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnTo = getSafeReturnUrl(searchParams.get("returnTo"));
  const sessionReason = searchParams.get("reason");

  useEffect(() => {
    if (status === "authenticated") {
      router.replace(returnTo);
    }
  }, [returnTo, router, status]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) {
      return;
    }

    setError(null);
    if (!email.trim() || !password) {
      setError("Ingresa tu correo electrónico y contraseña.");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError("Ingresa un correo electrónico válido.");
      return;
    }

    setSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      router.replace(returnTo);
    } catch (loginError) {
      setError(getLoginErrorMessage(loginError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="w-full max-w-md">
        <div className="mb-8">
          <span className="inline-flex rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-bold uppercase tracking-[0.14em] text-green-700">
            Acceso seguro
          </span>
          <h1 className="mt-5 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
            Bienvenido de nuevo
          </h1>
          <p className="mt-3 text-base leading-7 text-slate-600">
            Ingresa con tus credenciales para continuar en Dentia.
          </p>
        </div>

        {sessionReason === "session-expired" && (
          <div className="mb-5">
            <Alert tone="warning">
              Tu sesión finalizó. Inicia sesión nuevamente.
            </Alert>
          </div>
        )}

        {error && (
          <div className="mb-5">
            <Alert tone="error">{error}</Alert>
          </div>
        )}

        <form className="space-y-5" onSubmit={handleSubmit} noValidate>
          <div>
            <label
              htmlFor="email"
              className="mb-2 block text-sm font-bold text-slate-700"
            >
              Correo electrónico
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              required
              maxLength={320}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="nombre@consultorio.com"
              className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-base text-slate-900 shadow-sm transition placeholder:text-slate-400 hover:border-slate-400 focus:border-dentia-primary focus:outline-none focus:ring-4 focus:ring-green-100"
            />
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between gap-4">
              <label
                htmlFor="password"
                className="block text-sm font-bold text-slate-700"
              >
                Contraseña
              </label>
              <button
                type="button"
                onClick={() => setForgotOpen(true)}
                className="text-sm font-semibold text-green-700 transition hover:text-green-800 hover:underline"
              >
                ¿Olvidaste tu contraseña?
              </button>
            </div>
            <div className="relative">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                maxLength={256}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Ingresa tu contraseña"
                className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-14 text-base text-slate-900 shadow-sm transition placeholder:text-slate-400 hover:border-slate-400 focus:border-dentia-primary focus:outline-none focus:ring-4 focus:ring-green-100"
              />
              <button
                type="button"
                aria-label={
                  showPassword ? "Ocultar contraseña" : "Mostrar contraseña"
                }
                onClick={() => setShowPassword((current) => !current)}
                className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-slate-500 transition hover:text-slate-800"
              >
                {showPassword ? (
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
                    <path
                      d="m4 4 16 16M10.6 10.7a2 2 0 0 0 2.7 2.7M9.8 5.3A10.7 10.7 0 0 1 12 5c5.5 0 9 7 9 7a17 17 0 0 1-2.1 3M6.6 6.6C4.3 8.1 3 10.5 3 12c0 0 3.5 7 9 7 1 0 1.9-.2 2.8-.5"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
                    <path
                      d="M3 12s3.5-7 9-7 9 7 9 7-3.5 7-9 7-9-7-9-7Z"
                      stroke="currentColor"
                      strokeWidth="1.8"
                    />
                    <circle
                      cx="12"
                      cy="12"
                      r="2.5"
                      stroke="currentColor"
                      strokeWidth="1.8"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting || status === "initializing"}
            className="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-dentia-primary px-5 py-3 text-base font-bold text-white shadow-lg shadow-green-600/15 transition hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-65"
          >
            {submitting ? (
              <>
                <Spinner />
                Iniciando sesión…
              </>
            ) : (
              "Iniciar sesión"
            )}
          </button>
        </form>

        <div className="mt-7 flex items-center justify-center gap-2 text-xs text-slate-500">
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none">
            <path
              d="M7 10V8a5 5 0 0 1 10 0v2m-9 0h8a2 2 0 0 1 2 2v7H6v-7a2 2 0 0 1 2-2Z"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
          </svg>
          Sesión protegida y acceso auditado
        </div>
      </div>

      <ForgotPasswordDialog
        open={forgotOpen}
        onClose={() => setForgotOpen(false)}
      />
    </>
  );
}
