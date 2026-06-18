"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/services/apiClient";

export default function ChangePasswordPage() {
  const { changePassword, user } = useAuth();
  const router = useRouter();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (newPassword.length < 12) {
      setError("La nueva contraseña debe tener al menos 12 caracteres.");
      return;
    }
    if (newPassword !== confirmation) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setSaving(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmation,
      });
      router.replace("/dashboard");
    } catch (changeError) {
      setError(
        changeError instanceof ApiError
          ? changeError.detail ?? changeError.message
          : "No fue posible cambiar la contraseña.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <section className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm sm:p-9">
        <span className="inline-flex rounded-full bg-amber-50 px-3 py-1 text-xs font-bold uppercase tracking-wide text-amber-700">
          Acción requerida
        </span>
        <h1 className="mt-5 text-3xl font-bold text-slate-950">
          Cambia tu contraseña
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          {user?.must_change_password
            ? "Debes definir una contraseña personal antes de continuar."
            : "Actualiza la contraseña de tu cuenta."}
        </p>
        {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
        <form onSubmit={handleSubmit} className="mt-7 space-y-5">
          {[
            {
              label: "Contraseña actual",
              value: currentPassword,
              setter: setCurrentPassword,
              autoComplete: "current-password",
            },
            {
              label: "Nueva contraseña",
              value: newPassword,
              setter: setNewPassword,
              autoComplete: "new-password",
            },
            {
              label: "Confirmar nueva contraseña",
              value: confirmation,
              setter: setConfirmation,
              autoComplete: "new-password",
            },
          ].map((field) => (
            <label key={field.label} className="block">
              <span className="mb-2 block text-sm font-bold text-slate-700">
                {field.label}
              </span>
              <input
                type="password"
                value={field.value}
                autoComplete={field.autoComplete}
                onChange={(event) => field.setter(event.target.value)}
                className="min-h-12 w-full rounded-xl border border-slate-300 px-4 focus:border-dentia-primary focus:outline-none focus:ring-4 focus:ring-green-100"
              />
            </label>
          ))}
          <p className="text-xs leading-5 text-slate-500">
            Mínimo 12 caracteres. Puedes usar espacios y caracteres Unicode.
          </p>
          <button
            disabled={saving}
            className="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-dentia-primary px-5 font-bold text-white hover:bg-green-700 disabled:opacity-60"
          >
            {saving && <Spinner className="h-5 w-5" />}
            Guardar contraseña
          </button>
        </form>
      </section>
    </div>
  );
}
