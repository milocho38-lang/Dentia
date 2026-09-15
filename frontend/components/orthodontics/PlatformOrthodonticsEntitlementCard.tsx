"use client";
import { FormEvent, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { getPlatformOrthodonticsEntitlement, updatePlatformOrthodonticsEntitlement } from "@/services/orthodonticsService";
import type { OrthodonticsEntitlement } from "@/types/orthodontics";

export function PlatformOrthodonticsEntitlementCard({ companyId }: { companyId: string }) {
  const [value, setValue] = useState<OrthodonticsEntitlement | null>(null);
  const [enabled, setEnabled] = useState(false);
  const [seatLimit, setSeatLimit] = useState(0);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  useEffect(() => { getPlatformOrthodonticsEntitlement(companyId).then((loaded) => { setValue(loaded); setEnabled(loaded.enabled); setSeatLimit(loaded.seats.seat_limit); }).catch(() => setMessage("No fue posible cargar la habilitación de Ortodoncia.")); }, [companyId]);
  async function submit(event: FormEvent) { event.preventDefault(); setSaving(true); setMessage(null); try { const updated = await updatePlatformOrthodonticsEntitlement(companyId, enabled, seatLimit); setValue(updated); setMessage("Configuración de Ortodoncia actualizada."); } catch (error) { setMessage(error instanceof Error ? error.message : "No fue posible actualizar Ortodoncia."); } finally { setSaving(false); } }
  return <form onSubmit={submit} className="mt-6 rounded-2xl border bg-white p-5 shadow-sm">
    <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">Add-on</p><h2 className="mt-1 font-black">Ortodoncia</h2><p className="mt-1 text-sm text-slate-500">Habilitación comercial y cupos por odontólogo.</p></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold">{value?.enabled ? "Activo" : "Desactivado"}</span></div>
    {message && <div className="mt-4"><Alert>{message}</Alert></div>}
    <div className="mt-4 grid gap-4 sm:grid-cols-3 sm:items-end"><label className="flex min-h-11 items-center gap-3 rounded-xl border px-3 text-sm font-bold"><input type="checkbox" checked={enabled} onChange={(event) => setEnabled(event.target.checked)} />Módulo habilitado</label><label className="text-sm font-bold">Cupos<input type="number" min={enabled ? 1 : 0} max={10000} value={seatLimit} onChange={(event) => setSeatLimit(Number(event.target.value))} className="mt-1 min-h-11 w-full rounded-xl border px-3 font-normal" /></label><button disabled={saving || (enabled && seatLimit < 1)} className="min-h-11 rounded-xl bg-green-700 px-4 font-bold text-white disabled:opacity-50">{saving ? "Guardando…" : "Guardar Ortodoncia"}</button></div>
    {value && <p className="mt-3 text-sm text-slate-500">{value.seats.assigned_active} de {value.seats.seat_limit} cupos asignados.</p>}
  </form>;
}
