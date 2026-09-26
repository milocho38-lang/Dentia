"use client";

import { useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import {
  getPlatformPeriodontogramPilot,
  updatePlatformPeriodontogramPilot,
  updatePlatformPeriodontogramPilotDentist,
} from "@/services/periodontogramPilotService";
import type { PeriodontogramPilot } from "@/types/periodontogramPilot";

function messageFor(error: unknown) {
  return error instanceof Error
    ? error.message
    : "No fue posible actualizar el piloto de Periodontograma.";
}

export function PlatformPeriodontogramPilotCard({
  companyId,
}: {
  companyId: string;
}) {
  const [pilot, setPilot] = useState<PeriodontogramPilot | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    getPlatformPeriodontogramPilot(companyId)
      .then(setPilot)
      .catch(() => setError("No fue posible cargar el piloto de Periodontograma."));
  }, [companyId]);

  async function toggleCompany() {
    if (!pilot) return;
    setBusy("company");
    setError(null);
    setMessage(null);
    try {
      const updated = await updatePlatformPeriodontogramPilot(
        companyId,
        !pilot.enabled,
      );
      setPilot(updated);
      setMessage(
        updated.enabled
          ? "Piloto de Periodontograma habilitado para la empresa."
          : "Piloto deshabilitado. El histórico clínico permanece intacto.",
      );
    } catch (updateError) {
      setError(messageFor(updateError));
    } finally {
      setBusy(null);
    }
  }

  async function toggleDentist(dentistId: string, enabled: boolean) {
    setBusy(dentistId);
    setError(null);
    setMessage(null);
    try {
      const updated = await updatePlatformPeriodontogramPilotDentist(
        companyId,
        dentistId,
        enabled,
      );
      setPilot(updated);
      setMessage(
        enabled
          ? "Odontólogo autorizado para el piloto."
          : "Autorización revocada. El histórico clínico permanece intacto.",
      );
    } catch (updateError) {
      setError(messageFor(updateError));
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="mt-6 rounded-2xl border bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
            Piloto clínico
          </p>
          <h2 className="mt-1 font-black">Periodontograma</h2>
          <p className="mt-1 text-sm text-slate-500">
            Acceso controlado por empresa y odontólogo. No corresponde a un cupo comercial.
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold">
          {pilot?.enabled ? "Habilitado" : "Deshabilitado"}
        </span>
      </div>

      {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
      {message && <div className="mt-4"><Alert>{message}</Alert></div>}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border p-4">
        <div>
          <p className="font-bold">Habilitar para la empresa</p>
          <p className="text-sm text-slate-500">
            Además, cada odontólogo debe autorizarse explícitamente.
          </p>
        </div>
        <button
          type="button"
          disabled={!pilot || busy !== null}
          onClick={() => void toggleCompany()}
          className="min-h-11 rounded-xl border px-4 font-bold disabled:opacity-50"
        >
          {busy === "company"
            ? "Guardando…"
            : pilot?.enabled
              ? "Deshabilitar"
              : "Habilitar"}
        </button>
      </div>

      {pilot && (
        <div className="mt-4 overflow-hidden rounded-xl border">
          <div className="border-b bg-slate-50 px-4 py-3">
            <h3 className="text-sm font-black">Odontólogos autorizados</h3>
          </div>
          {pilot.dentists.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">
              La empresa no tiene perfiles odontológicos.
            </p>
          ) : (
            <div className="divide-y">
              {pilot.dentists.map((dentist) => {
                const operational =
                  dentist.dentist_is_active && dentist.user_is_active;
                const disabled =
                  busy !== null ||
                  (!dentist.authorized && (!pilot.enabled || !operational));
                return (
                  <div
                    key={dentist.dentist_id}
                    className="flex flex-wrap items-center justify-between gap-3 p-4"
                  >
                    <div>
                      <p className="font-bold">{dentist.dentist_name}</p>
                      <p className="text-sm text-slate-500">
                        {!operational
                          ? "No elegible: odontólogo o usuario inactivo"
                          : dentist.authorized
                            ? "Autorizado"
                            : "No autorizado"}
                      </p>
                    </div>
                    <button
                      type="button"
                      disabled={disabled}
                      onClick={() =>
                        void toggleDentist(
                          dentist.dentist_id,
                          !dentist.authorized,
                        )
                      }
                      className="min-h-11 rounded-xl border px-4 text-sm font-bold disabled:opacity-50"
                    >
                      {busy === dentist.dentist_id
                        ? "Guardando…"
                        : dentist.authorized
                          ? "Revocar"
                          : "Autorizar"}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
