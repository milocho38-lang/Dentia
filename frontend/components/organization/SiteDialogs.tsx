"use client";

import { useState } from "react";
import { Modal } from "@/components/shared/Modal";
import type { SiteImpact } from "@/types/organization";

export function SiteImpactDialog({ open, impact, onClose }: { open: boolean; impact: SiteImpact | null; onClose: () => void }) {
  return <Modal open={open} title="Impacto de inactivación" onClose={onClose}>{impact && <div className="space-y-4 text-sm"><div className="grid grid-cols-2 gap-3">{[["Citas futuras",impact.future_appointments],["Usuarios asignados",impact.assigned_users],["Sin alternativa",impact.users_without_alternative],["Sesiones activas",impact.active_sessions],["Odontólogos",impact.dentists],["Seguimientos abiertos",impact.open_followups]].map(([label,value])=><div key={String(label)} className="rounded-xl bg-slate-50 p-3"><p className="text-slate-500">{label}</p><p className="mt-1 text-xl font-black">{value}</p></div>)}</div>{impact.blocking_reasons.length>0&&<div className="rounded-xl bg-red-50 p-4 text-red-800"><p className="font-bold">La sede no puede inactivarse:</p><ul className="mt-2 list-disc pl-5">{impact.blocking_reasons.map(reason=><li key={reason}>{reason}</li>)}</ul></div>}</div>}</Modal>;
}

function ActionDialog({ open, title, actionLabel, tone, onClose, onConfirm }: { open:boolean; title:string; actionLabel:string; tone:string; onClose:()=>void; onConfirm:(reason:string)=>Promise<void> }) {
  const [reason,setReason]=useState(""); const [busy,setBusy]=useState(false);
  return <Modal open={open} title={title} onClose={onClose}><label><span className="mb-1 block text-sm font-bold">Motivo</span><textarea value={reason} onChange={e=>setReason(e.target.value)} className="min-h-28 w-full rounded-xl border p-3"/></label><div className="mt-4 flex justify-end gap-2"><button onClick={onClose} className="rounded-xl border px-4 py-2 font-bold">Cancelar</button><button disabled={busy||reason.trim().length<2} onClick={async()=>{setBusy(true);try{await onConfirm(reason);}finally{setBusy(false);}}} className={`rounded-xl px-4 py-2 font-bold text-white disabled:opacity-50 ${tone}`}>{busy?"Procesando…":actionLabel}</button></div></Modal>;
}

export function SiteDeactivateDialog(props: { open:boolean; onClose:()=>void; onConfirm:(reason:string)=>Promise<void> }) {
  return <ActionDialog {...props} title="Inactivar sede" actionLabel="Inactivar" tone="bg-red-700"/>;
}

export function SiteReactivateDialog(props: { open:boolean; onClose:()=>void; onConfirm:(reason:string)=>Promise<void> }) {
  return <ActionDialog {...props} title="Reactivar sede" actionLabel="Reactivar" tone="bg-green-700"/>;
}
