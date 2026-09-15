"use client";
import { useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { assignOrthodonticsDentist, getOrthodonticsAssignments, revokeOrthodonticsAssignment } from "@/services/orthodonticsService";
import type { OrthodonticsAssignmentList } from "@/types/orthodontics";

export function OrthodonticsAssignmentPage() {
  const [data, setData] = useState<OrthodonticsAssignmentList | null>(null);
  const [loading, setLoading] = useState(true); const [busy, setBusy] = useState<string | null>(null); const [message, setMessage] = useState<string | null>(null);
  async function load() { setLoading(true); try { setData(await getOrthodonticsAssignments()); } catch { setMessage("No fue posible cargar los cupos de Ortodoncia."); } finally { setLoading(false); } }
  useEffect(() => { void load(); }, []);
  async function toggle(dentistId: string, assignmentId: string | null) { setBusy(dentistId); setMessage(null); try { const result = assignmentId ? await revokeOrthodonticsAssignment(assignmentId) : await assignOrthodonticsDentist(dentistId); setMessage(result.message); await load(); } catch (error) { setMessage(error instanceof Error ? error.message : "No fue posible actualizar el cupo."); } finally { setBusy(null); } }
  if (loading && !data) return <div className="flex justify-center py-20"><Spinner className="h-7 w-7 text-green-700" /></div>;
  return <div className="mx-auto max-w-5xl"><p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">Configuración</p><h1 className="mt-2 text-3xl font-black">Ortodoncia</h1><p className="mt-2 text-sm text-slate-500">Asigna los cupos contratados a odontólogos activos.</p>
    {message && <div className="mt-5"><Alert>{message}</Alert></div>}{data && !data.entitlement.enabled && <div className="mt-5"><Alert>El módulo no está habilitado. Solicita su activación a Dentia.</Alert></div>}
    {data && <><div className="mt-6 grid gap-4 sm:grid-cols-3"><Stat label="Cupos" value={data.entitlement.seats.seat_limit} /><Stat label="Asignados" value={data.entitlement.seats.assigned_active} /><Stat label="Disponibles" value={data.entitlement.seats.available} /></div><section className="mt-6 overflow-hidden rounded-2xl border bg-white shadow-sm">{data.items.map((item) => { const operational = item.dentist_is_active && item.user_is_active; return <div key={item.dentist_id} className="flex flex-wrap items-center justify-between gap-4 border-b p-5 last:border-b-0"><div><p className="font-black">{item.dentist_name}</p><p className="text-sm text-slate-500">{operational ? "Odontólogo activo" : "Odontólogo inactivo"} · {item.assigned ? "Ortodoncia asignada" : "Sin asignación"}</p></div><button type="button" disabled={busy === item.dentist_id || (!item.assigned && (!data.entitlement.enabled || !operational || data.entitlement.seats.available < 1))} onClick={() => void toggle(item.dentist_id, item.id)} className="rounded-xl border px-4 py-2 text-sm font-bold disabled:opacity-40">{item.assigned ? "Retirar" : "Asignar"}</button></div>; })}</section></>}
  </div>;
}
function Stat({ label, value }: { label: string; value: number }) { return <div className="rounded-2xl border bg-white p-5"><p className="text-xs font-bold uppercase text-slate-400">{label}</p><p className="mt-2 text-2xl font-black">{value}</p></div>; }
