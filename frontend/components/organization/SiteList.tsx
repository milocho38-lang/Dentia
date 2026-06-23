"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { listSites } from "@/services/organizationService";
import type { Site } from "@/types/organization";

export function SiteList() {
  const { hasPermission } = useAuth();
  const [items, setItems] = useState<Site[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setItems((await listSites(search, status)).items); }
    catch { setError("No fue posible cargar las sedes."); }
    finally { setLoading(false); }
  }, [search, status]);
  useEffect(() => { load(); }, [load]);

  return <div className="mx-auto max-w-7xl">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">Configuración</p><h1 className="mt-2 text-3xl font-black">Sedes</h1><p className="mt-2 text-sm text-slate-500">Ubicaciones, estado e impacto operativo.</p></div>{hasPermission("sites.manage") && <Link href="/configuracion/sedes/nueva" className="rounded-xl bg-green-700 px-5 py-3 font-bold text-white">+ Nueva sede</Link>}</header>
    <form onSubmit={(e:FormEvent)=>{e.preventDefault();load();}} className="mt-6 grid gap-3 rounded-2xl border bg-white p-4 sm:grid-cols-[1fr_220px_auto]"><input value={search} onChange={(e)=>setSearch(e.target.value)} placeholder="Buscar sede" className="min-h-11 rounded-xl border px-3"/><select value={status} onChange={(e)=>setStatus(e.target.value)} className="min-h-11 rounded-xl border bg-white px-3"><option value="">Todas</option><option>Activa</option><option>Inactiva</option></select><button className="rounded-xl border px-5 font-bold">Buscar</button></form>
    {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
    <section className="mt-5 overflow-hidden rounded-2xl border bg-white shadow-sm">{loading ? <div className="flex justify-center py-16"><Spinner className="h-7 w-7 text-green-700"/></div> : <div className="overflow-x-auto"><table className="min-w-full divide-y"><thead className="bg-slate-50"><tr>{["Sede","Estado","Usuarios","Odontólogos","Citas futuras","Seguimientos",""].map(x=><th key={x} className="px-5 py-3 text-left text-xs font-bold uppercase text-slate-500">{x}</th>)}</tr></thead><tbody className="divide-y">{items.map(site=><tr key={site.id}><td className="px-5 py-4"><p className="font-bold">{site.name}</p><p className="text-xs text-slate-500">{site.address} · {site.city}</p></td><td className="px-5 py-4"><span className={`rounded-full px-2 py-1 text-xs font-bold ${site.status==="Activa"?"bg-green-100 text-green-800":"bg-slate-200 text-slate-700"}`}>{site.status}</span></td><td className="px-5 py-4">{site.assigned_users}</td><td className="px-5 py-4">{site.dentists}</td><td className="px-5 py-4">{site.future_appointments}</td><td className="px-5 py-4">{site.open_followups}</td><td className="px-5 py-4 text-right"><Link href={`/configuracion/sedes/${site.id}`} className="font-bold text-green-700">Ver</Link></td></tr>)}</tbody></table>{!items.length&&<p className="py-14 text-center text-sm text-slate-500">No hay sedes para los filtros seleccionados.</p>}</div>}</section>
  </div>;
}
