"use client";
/* eslint-disable @next/next/no-img-element -- authenticated object URLs cannot use the Next image optimizer */

import { useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import {
  downloadConsentPaperFinal, downloadConsentPaperPrint, finalizeConsentPaper, getConsentPaperPacket,
  prepareConsentPaperPacket, previewConsentPaperPage, recordConsentPaperSigned, removeConsentPaperPage,
  reorderConsentPaperPages, uploadConsentPaperPages, viewConsentPaperFinal,
} from "@/services/consentInstanceService";
import type { ConsentPaperPacket } from "@/types/consentInstance";

const checks = [
  ["all_pages_present", "Confirmo que cargué todas las páginas del documento firmado."],
  ["correct_order", "Confirmo que las páginas están en el orden correcto."],
  ["legible", "Confirmo que el contenido es legible."],
  ["signature_page_included", "Confirmo que la página con la firma manuscrita está incluida y visible."],
  ["matches_printed_packet", "Confirmo que la copia digital corresponde al consentimiento impreso identificado por Dentia."],
  ["physical_original_retained", "Confirmo que el original físico será conservado conforme a la política documental de la clínica."],
] as const;

function openBlob(blob:Blob){const url=URL.createObjectURL(blob);window.open(url,"_blank","noopener,noreferrer");window.setTimeout(()=>URL.revokeObjectURL(url),60_000);}

export function ConsentPaperPanel({instanceId,channel,canRead,canPrepare,canRecord,canUpload,canFinalize,onChanged}:{instanceId:string;channel:string|null;canRead:boolean;canPrepare:boolean;canRecord:boolean;canUpload:boolean;canFinalize:boolean;onChanged:()=>Promise<void>|void}){
  const [packet,setPacket]=useState<ConsentPaperPacket|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState<string|null>(null);
  const [verification,setVerification]=useState<Record<string,boolean>>({});
  const [previews,setPreviews]=useState<Record<string,string>>({});
  const allChecked=checks.every(([key])=>verification[key]);
  const load=async()=>{if(!canRead||channel!=="PAPER")return;try{setPacket(await getConsentPaperPacket(instanceId));}catch{setPacket(null);}};
  useEffect(()=>{void load();},[instanceId,channel,canRead]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(()=>{let active=true;const urls:string[]=[];if(!packet?.pages.length){setPreviews({});return;}void Promise.all(packet.pages.map(async page=>{const blob=await previewConsentPaperPage(instanceId,page.id);const url=URL.createObjectURL(blob);urls.push(url);return [page.id,url] as const;})).then(rows=>{if(active)setPreviews(Object.fromEntries(rows));}).catch(()=>setError("No fue posible cargar una miniatura."));return()=>{active=false;urls.forEach(url=>URL.revokeObjectURL(url));};},[instanceId,packet?.pages]);
  const step=useMemo(()=>!packet?1:packet.status==="PRINTED"?2:packet.status==="SIGNED_PENDING_DIGITIZATION"?3:packet.status==="DIGITIZING"?4:5,[packet]);
  async function run(action:()=>Promise<ConsentPaperPacket>){setBusy(true);setError(null);try{const next=await action();setPacket(next);await onChanged();}catch(caught){setError(caught instanceof Error?caught.message:"No fue posible completar la acción.");}finally{setBusy(false);}}
  async function move(index:number,direction:number){if(!packet)return;const ids=packet.pages.map(x=>x.id),target=index+direction;if(target<0||target>=ids.length)return;[ids[index],ids[target]]=[ids[target],ids[index]];await run(()=>reorderConsentPaperPages(instanceId,ids));}
  return <section className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
    <div><p className="text-xs font-black uppercase text-emerald-700">Firma en papel</p><h4 className="text-lg font-black text-slate-950">Documento manuscrito y copia digitalizada</h4><p className="text-sm text-slate-600">El original físico permanece bajo custodia de la clínica. Dentia conserva una copia digitalizada sellada.</p></div>
    <div className="my-4 grid gap-2 text-xs font-bold sm:grid-cols-5">{["Preparar e imprimir","Registrar firma","Digitalizar","Verificar","Finalizar"].map((label,index)=><span key={label} className={`rounded-lg p-2 text-center ${step===index+1?"bg-emerald-700 text-white":"bg-white text-slate-500"}`}>{index+1}. {label}</span>)}</div>
    {error&&<Alert tone="error">{error}</Alert>}
    {!packet&&channel!=="PAPER"&&canPrepare&&<div className="space-y-3"><Alert tone="info">Al preparar el packet se revocará cualquier enlace electrónico activo. El documento impreso quedará congelado y no podrá regenerarse silenciosamente.</Alert><button disabled={busy} onClick={()=>void run(()=>prepareConsentPaperPacket(instanceId))} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">Elegir firma en papel y preparar packet</button></div>}
    {packet&&<div className="space-y-4">
      <div className="grid gap-2 rounded-xl bg-white p-3 text-sm sm:grid-cols-3"><p><strong>Estado</strong><br/>{packet.status==="PRINTED"?"Preparado para firma manuscrita":packet.status==="SIGNED_PENDING_DIGITIZATION"?"Firmado en papel — pendiente de digitalización":packet.status==="DIGITIZING"?"Digitalización en preparación":"Firmado en papel — copia digitalizada"}</p><p><strong>Páginas</strong><br/>{packet.uploaded_page_count} cargadas de {packet.expected_page_count} esperadas</p><p><strong>Código de integridad</strong><br/><span className="break-all font-mono text-xs">{packet.final_pdf_sha256??packet.print_sha256}</span></p></div>
      <div className="flex flex-wrap gap-2"><button disabled={busy||!canRead} onClick={()=>void downloadConsentPaperPrint(instanceId).then(openBlob)} className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-black">Ver packet para imprimir</button>{packet.status==="PRINTED"&&canRecord&&<button disabled={busy} onClick={()=>void run(()=>recordConsentPaperSigned(instanceId))} className="rounded-xl bg-dentia-primary px-4 py-2 text-sm font-black text-white">Registrar “Firmado en papel”</button>}{packet.status==="FINALIZED"&&canRead&&<><button disabled={busy} onClick={()=>void viewConsentPaperFinal(instanceId).then(openBlob)} className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-black">Ver copia digitalizada</button><button disabled={busy} onClick={()=>void downloadConsentPaperFinal(instanceId).then(openBlob)} className="rounded-xl bg-dentia-primary px-4 py-2 text-sm font-black text-white">Descargar copia digitalizada</button></>}</div>
      {["SIGNED_PENDING_DIGITIZATION","DIGITIZING"].includes(packet.status)&&canUpload&&<label className="block rounded-xl border border-dashed border-emerald-400 bg-white p-4 text-sm font-bold">Agregar PDF, JPEG o PNG<input type="file" accept="application/pdf,image/jpeg,image/png" disabled={busy} onChange={event=>{const file=event.target.files?.[0];if(file)void run(()=>uploadConsentPaperPages(instanceId,file));event.currentTarget.value="";}} className="mt-2 block w-full text-sm font-normal"/><span className="mt-1 block text-xs font-normal text-slate-500">Máximo 15 MB por archivo, 50 páginas y 50 MB por expediente.</span></label>}
      {packet.pages.length>0&&<div><h5 className="mb-2 font-black">Páginas cargadas en orden</h5><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{packet.pages.map((page,index)=><article key={page.id} className="rounded-xl border bg-white p-3"><div className="aspect-[.77] overflow-hidden rounded-lg bg-slate-100">{previews[page.id]?<img src={previews[page.id]} alt={`Vista previa de la página ${index+1}`} className="h-full w-full object-contain"/>:<div className="grid h-full place-items-center text-xs text-slate-500">Cargando…</div>}</div><div className="mt-2 flex items-center justify-between"><strong>Página {index+1}</strong>{packet.status==="DIGITIZING"&&<span className="flex gap-1"><button aria-label="Mover página arriba" disabled={index===0||busy} onClick={()=>void move(index,-1)} className="rounded border px-2">↑</button><button aria-label="Mover página abajo" disabled={index===packet.pages.length-1||busy} onClick={()=>void move(index,1)} className="rounded border px-2">↓</button><button aria-label="Eliminar página" disabled={busy} onClick={()=>void run(()=>removeConsentPaperPage(instanceId,page.id))} className="rounded border border-red-200 px-2 text-red-700">×</button></span>}</div></article>)}</div></div>}
      {packet.status==="DIGITIZING"&&<div className="space-y-2 rounded-xl border bg-white p-4"><h5 className="font-black">Verificación humana obligatoria</h5>{checks.map(([key,label])=><label key={key} className="flex items-start gap-2 text-sm"><input type="checkbox" checked={Boolean(verification[key])} onChange={event=>setVerification(current=>({...current,[key]:event.target.checked}))}/><span>{label}</span></label>)}{packet.uploaded_page_count!==packet.expected_page_count&&<Alert tone="warning">No puedes finalizar: deben existir exactamente {packet.expected_page_count} páginas.</Alert>}{canFinalize&&<button disabled={busy||!allChecked||packet.uploaded_page_count!==packet.expected_page_count} onClick={()=>void run(()=>finalizeConsentPaper(instanceId,verification))} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">Finalizar copia digital</button>}</div>}
    </div>}
  </section>;
}
