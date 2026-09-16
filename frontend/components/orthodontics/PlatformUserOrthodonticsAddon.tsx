"use client";

import { useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import {
  assignPlatformOrthodonticsDentist,
  getPlatformOrthodonticsAssignments,
  revokePlatformOrthodonticsAssignment,
} from "@/services/orthodonticsService";
import type { PlatformUserSummary } from "@/types/platform";
import type {
  OrthodonticsAssignmentAction,
  OrthodonticsAssignmentList,
} from "@/types/orthodontics";

interface Props {
  companyId: string;
  user: PlatformUserSummary;
  editable: boolean;
  onChanged: () => void;
}

function updateAssignmentState(
  current: OrthodonticsAssignmentList,
  action: OrthodonticsAssignmentAction,
): OrthodonticsAssignmentList {
  return {
    entitlement: {
      ...current.entitlement,
      seats: action.seats,
    },
    items: current.items.map((item) =>
      item.dentist_id === action.assignment.dentist_id
        ? action.assignment
        : item,
    ),
  };
}

export function PlatformUserOrthodonticsAddon({
  companyId,
  user,
  editable,
  onChanged,
}: Props) {
  const [data, setData] = useState<OrthodonticsAssignmentList | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    getPlatformOrthodonticsAssignments(companyId)
      .then((loaded) => {
        if (active) setData(loaded);
      })
      .catch((caught) => {
        if (active) {
          setError(
            caught instanceof Error
              ? caught.message
              : "No fue posible cargar los cupos de Ortodoncia.",
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [companyId]);

  const assignment = useMemo(() => {
    if (!data || !user.dentist_profile) return null;
    return (
      data.items.find(
        (item) => item.dentist_id === user.dentist_profile?.id,
      ) ?? null
    );
  }, [data, user.dentist_profile]);

  if (loading || (!data && !error)) return null;
  if (data && !data.entitlement.enabled) return null;

  const dentistProfile = user.dentist_profile;
  const eligible = Boolean(
    dentistProfile &&
      dentistProfile.is_active &&
      dentistProfile.status === "Activo" &&
      user.is_active &&
      user.status === "Activo" &&
      assignment?.dentist_is_active &&
      assignment.user_is_active,
  );
  const assigned = Boolean(assignment?.assigned);
  const noSeats = Boolean(
    data && !assigned && data.entitlement.seats.available < 1,
  );

  async function toggleAssignment() {
    if (!data || !dentistProfile || !assignment || saving || !eligible) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const response = assigned
        ? await revokePlatformOrthodonticsAssignment(
            companyId,
            assignment.id as string,
          )
        : await assignPlatformOrthodonticsDentist(companyId, dentistProfile.id);
      setData((current) =>
        current ? updateAssignmentState(current, response) : current,
      );
      setMessage(response.message);
      onChanged();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "No fue posible actualizar el cupo de Ortodoncia.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="mt-6 rounded-2xl border border-green-100 bg-green-50/40 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
            Add-ons clínicos
          </p>
          <h3 className="mt-1 font-black text-slate-950">Ortodoncia</h3>
          <p className="mt-1 text-sm text-slate-500">
            El cupo habilita el módulo para este odontólogo y no modifica sus roles.
          </p>
        </div>
        <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-slate-700 shadow-sm">
          {assigned ? "Asignado" : "No asignado"}
        </span>
      </div>

      {error && (
        <div className="mt-4">
          <Alert tone="error">{error}</Alert>
        </div>
      )}
      {message && (
        <div className="mt-4">
          <Alert>{message}</Alert>
        </div>
      )}

      {data && (
        <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
          <div className="rounded-xl bg-white p-3">
            <p className="text-xs font-bold uppercase text-slate-400">Cupos contratados</p>
            <p className="mt-1 text-lg font-black">{data.entitlement.seats.seat_limit}</p>
          </div>
          <div className="rounded-xl bg-white p-3">
            <p className="text-xs font-bold uppercase text-slate-400">Cupos asignados</p>
            <p className="mt-1 text-lg font-black">{data.entitlement.seats.assigned_active}</p>
          </div>
          <div className="rounded-xl bg-white p-3">
            <p className="text-xs font-bold uppercase text-slate-400">Cupos disponibles</p>
            <p className="mt-1 text-lg font-black">{data.entitlement.seats.available}</p>
          </div>
        </div>
      )}

      {!dentistProfile ? (
        <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
          No elegible para Ortodoncia: el usuario no tiene perfil odontológico.
        </p>
      ) : !eligible ? (
        <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
          No elegible para Ortodoncia: el perfil odontológico y el usuario deben estar activos.
        </p>
      ) : (
        <label className="mt-4 flex items-start gap-3 rounded-xl border bg-white p-4 text-sm">
          <input
            type="checkbox"
            checked={assigned}
            disabled={!editable || saving || noSeats}
            onChange={() => void toggleAssignment()}
            className="mt-0.5 h-4 w-4"
          />
          <span>
            <span className="block font-black">Asignar cupo de Ortodoncia</span>
            <span className="mt-1 block text-xs text-slate-500">
              {editable
                ? "Este cambio se guarda inmediatamente y conserva el histórico al retirar el cupo."
                : "Abre Editar usuario para cambiar la asignación."}
            </span>
          </span>
        </label>
      )}

      {noSeats && (
        <p className="mt-3 text-sm font-bold text-amber-800">No hay cupos disponibles.</p>
      )}
    </section>
  );
}
