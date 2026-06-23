"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import {
  createSite, deactivateSite, getSite, getSiteImpact,
  reactivateSite, updateSite,
} from "@/services/organizationService";
import type { Site, SiteImpact, SiteInput } from "@/types/organization";
import {
  SiteDeactivateDialog, SiteImpactDialog, SiteReactivateDialog,
} from "./SiteDialogs";

const empty: SiteInput = { name:"", address:"", city:"", phone:null, timezone:null };

export function SiteForm({ siteId, mode }: { siteId?: string; mode: "create" | "edit" | "detail" }) {
  const router=useRouter(); const {hasPermission}=useAuth();
  const [site,setSite]=useState<Site|null>(null);
  const [data,setData]=useState<SiteInput>(empty);
  const [loading,setLoading]=useState(Boolean(siteId));
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [impact,setImpact]=useState<SiteImpact|null>(null);
  const [impactOpen,setImpactOpen]=useState(false);
  const [deactivateOpen,setDeactivateOpen]=useState(false);
  const [reactivateOpen,setReactivateOpen]=useState(false);

  useEffect(()=>{if(!siteId)return;getSite(siteId).then(loaded=>{setSite(loaded);setData({name:loaded.name,address:loaded.address,city:loaded.city,phone:loaded.phone,timezone:loaded.timezone});}).catch(()=>setError("No fue posible cargar la sede.")).finally(()=>setLoading(false));},[siteId]);
  async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError(null);try{const saved=siteId?await updateSite(siteId,data):await createSite(data);router.push(`/configuracion/sedes/${saved.id}`);}catch(caught){setError(caught instanceof Error?caught.message:"No fue posible guardar la sede.");}finally{setBusy(false);}}
  async function showImpact(){if(!siteId)return;setImpact(await getSiteImpact(siteId));setImpactOpen(true);}
  async function reload(){if(siteId)setSite(await getSite(siteId));}

  if(loading)return <div className="flex justify-center py-20"><Spinner className="h-7 w-7 text-green-700"/></div>;
  const editable=mode!=="detail";
  return <div className="mx-auto max-w-5xl"><header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[.16em] text-green-700">Configuración</p><h1 className="mt-2 text-3xl font-black">{mode==="create"?"Nueva sede":site?.name??"Sede"}</h1><p className="mt-2 text-sm text-slate-500">{mode==="detail"?"Información e impacto operativo.":"Datos de ubicación y zona horaria."}</p></div>{mode==="detail"&&site&&hasPermission("sites.manage")&&<Link href={`/configuracion/sedes/${site.id}/editar`} className="rounded-xl border px-5 py-3 font-bold">Editar</Link>}</header>
    {error&&<div className="mt-5"><Alert tone="error">{error}</Alert></div>}
    <form onSubmit={submit} className="mt-6 space-y-5 rounded-3xl border bg-white p-6 shadow-sm"><div className="grid gap-4 sm:grid-cols-2"><Field label="Nombre" value={data.name} disabled={!editable} onChange={value=>setData({...data,name:value})}/><Field label="Ciudad" value={data.city} disabled={!editable} onChange={value=>setData({...data,city:value})}/><div className="sm:col-span-2"><Field label="Dirección" value={data.address} disabled={!editable} onChange={value=>setData({...data,address:value})}/></div><Field label="Teléfono" value={data.phone??""} disabled={!editable} onChange={value=>setData({...data,phone:value||null})}/><label><span className="mb-1 block text-sm font-bold">Zona horaria</span><select disabled={!editable} value={data.timezone??""} onChange={e=>setData({...data,timezone:e.target.value||null})} className="min-h-11 w-full rounded-xl border bg-white px-3 disabled:bg-slate-50"><option value="">Heredar de empresa</option><option>America/Bogota</option><option>America/Lima</option><option>America/Mexico_City</option><option>America/New_York</option></select></label></div>{site&&<div className="grid gap-3 sm:grid-cols-4">{[["Estado",site.status],["Usuarios",site.assigned_users],["Citas futuras",site.future_appointments],["Seguimientos",site.open_followups]].map(([label,value])=><div key={String(label)} className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 font-black">{value}</p></div>)}</div>}
      {editable?<div className="flex justify-end gap-2"><Link href={siteId?`/configuracion/sedes/${siteId}`:"/configuracion/sedes"} className="rounded-xl border px-5 py-3 font-bold">Cancelar</Link><button disabled={busy||!data.name.trim()||!data.address.trim()||!data.city.trim()} className="rounded-xl bg-green-700 px-5 py-3 font-bold text-white disabled:opacity-50">{busy?"Guardando…":"Guardar"}</button></div>:site&&hasPermission("sites.manage")&&<div className="flex flex-wrap justify-end gap-2"><button type="button" onClick={showImpact} className="rounded-xl border px-4 py-2 font-bold">Ver impacto</button>{site.status==="Activa"?<button type="button" onClick={async()=>{setImpact(await getSiteImpact(site.id));setDeactivateOpen(true);}} className="rounded-xl border border-red-200 px-4 py-2 font-bold text-red-700">Inactivar</button>:<button type="button" onClick={()=>setReactivateOpen(true)} className="rounded-xl bg-green-700 px-4 py-2 font-bold text-white">Reactivar</button>}</div>}
    </form>
    <SiteImpactDialog open={impactOpen} impact={impact} onClose={()=>setImpactOpen(false)}/>
    <SiteDeactivateDialog open={deactivateOpen} onClose={()=>setDeactivateOpen(false)} onConfirm={async reason=>{if(!siteId)return;try{await deactivateSite(siteId,reason);setDeactivateOpen(false);await reload();}catch(caught){setDeactivateOpen(false);setError(caught instanceof Error?caught.message:"No fue posible inactivar.");}}}/>
    <SiteReactivateDialog open={reactivateOpen} onClose={()=>setReactivateOpen(false)} onConfirm={async reason=>{if(!siteId)return;await reactivateSite(siteId,reason);setReactivateOpen(false);await reload();}}/>
  </div>;
}

function Field({label,value,disabled,onChange}:{label:string;value:string;disabled:boolean;onChange:(value:string)=>void}){return <label><span className="mb-1 block text-sm font-bold">{label}</span><input disabled={disabled} value={value} onChange={e=>onChange(e.target.value)} className="min-h-11 w-full rounded-xl border px-3 disabled:bg-slate-50"/></label>;}
