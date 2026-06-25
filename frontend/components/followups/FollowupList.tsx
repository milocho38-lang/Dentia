"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Modal } from "@/components/shared/Modal";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { getAgendaOptions } from "@/services/agendaService";
import { ApiError } from "@/services/apiClient";
import {
  closeFollowup, generateFollowupWhatsApp, getFollowup,
  getFollowupDashboard, listFollowups, registerFollowupContact,
  reopenFollowup, scheduleFollowupAppointment,
} from "@/services/followupService";
import type { AgendaOptions } from "@/types/agenda";
import type { Followup, FollowupDashboard } from "@/types/followup";

const FALLBACK_TIMEZONE = "America/Bogota";

function getTimeZoneOffset(timeZone: string, date: Date) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(date);
  const values = Object.fromEntries(
    parts
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, Number(part.value)]),
  );
  const asUtc = Date.UTC(
    values.year,
    values.month - 1,
    values.day,
    values.hour === 24 ? 0 : values.hour,
    values.minute,
    values.second,
  );
  return asUtc - date.getTime();
}

function zonedDateTimeToIso(date: string, time: string, timeZone: string) {
  const [year, month, day] = date.split("-").map(Number);
  const [hour, minute] = time.split(":").map(Number);
  const utcGuess = new Date(Date.UTC(year, month - 1, day, hour, minute, 0));
  const firstOffset = getTimeZoneOffset(timeZone, utcGuess);
  const firstUtc = new Date(utcGuess.getTime() - firstOffset);
  const secondOffset = getTimeZoneOffset(timeZone, firstUtc);
  return new Date(utcGuess.getTime() - secondOffset).toISOString();
}

function formatDate(value: string | null, time = false) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    ...(time ? { timeStyle: "short" as const } : {}),
  }).format(new Date(value));
}

export function FollowupList() {
  const [items, setItems] = useState<Followup[]>([]);
  const [summary, setSummary] = useState<FollowupDashboard | null>(null);
  const { user } = useAuth();
  const [classification, setClassification] = useState("");
  const [siteId, setSiteId] = useState(user?.active_site_id ?? "");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Followup | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: "1", page_size: "100" });
    if (classification) params.set("classification", classification);
    if (search.trim()) params.set("search", search.trim());
    if (siteId) params.set("site_id", siteId);
    try {
      const [list, dashboard] = await Promise.all([
        listFollowups(`?${params.toString()}`),
        getFollowupDashboard(siteId || undefined),
      ]);
      setItems(list.items);
      setSummary(dashboard);
    } catch {
      setError("No fue posible cargar los seguimientos.");
    } finally {
      setLoading(false);
    }
  }, [classification, search, siteId]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    setSiteId(user?.active_site_id ?? "");
  }, [user?.active_site_id]);

  return (
    <div className="mx-auto max-w-7xl">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">Operación</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-950">Seguimiento de pacientes</h1>
        <p className="mt-2 text-sm text-slate-500">Controles pendientes, próximos, vencidos y con cita futura.</p>
      </header>

      {summary && (
        <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Pendientes", summary.pending, "bg-sky-50 text-sky-800"],
            ["Próximos", summary.upcoming, "bg-amber-50 text-amber-800"],
            ["Vencidos", summary.overdue, "bg-red-50 text-red-800"],
            ["Con cita", summary.scheduled, "bg-green-50 text-green-800"],
          ].map(([label, value, style]) => (
            <article key={String(label)} className={`rounded-2xl p-5 ${style}`}>
              <p className="text-sm font-bold">{label}</p>
              <p className="mt-2 text-3xl font-black">{value}</p>
            </article>
          ))}
        </section>
      )}

      <form onSubmit={(event) => { event.preventDefault(); load(); }} className="mt-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-[1fr_220px_220px_auto]">
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar paciente" className="min-h-11 rounded-xl border border-slate-300 px-4" />
        <select value={siteId} onChange={(event) => setSiteId(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-4">
          <option value="">Todas mis sedes</option>
          {user?.sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
        </select>
        <select value={classification} onChange={(event) => setClassification(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-4">
          <option value="">Todas las clasificaciones</option>
          <option>Pendiente por contactar</option>
          <option>Próximo a vencer</option>
          <option>Vencido</option>
          <option>Con cita futura</option>
          <option>Aún no requiere contacto</option>
          <option>Cerrado</option>
        </select>
        <button className="rounded-xl border border-slate-300 px-5 font-bold">Buscar</button>
      </form>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
      <section className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex justify-center gap-3 py-16 text-slate-500"><Spinner className="h-6 w-6 text-dentia-primary" />Cargando seguimientos…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50"><tr>
                {["Paciente", "Control", "Motivo", "Odontólogo", "Clasificación", ""].map((heading) => <th key={heading} className="px-5 py-3 text-left text-xs font-bold uppercase text-slate-500">{heading}</th>)}
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.id}>
                    <td className="px-5 py-4"><p className="font-bold">{item.patient_name}</p><p className="text-xs text-slate-500">{item.contact_mobile}</p></td>
                    <td className="px-5 py-4 text-sm">{formatDate(item.followup_date)}</td>
                    <td className="max-w-xs px-5 py-4 text-sm text-slate-600">{item.reason}</td>
                    <td className="px-5 py-4 text-sm">{item.dentist_name}</td>
                    <td className="px-5 py-4"><span className={`rounded-full px-2.5 py-1 text-xs font-bold ${item.classification === "Vencido" ? "bg-red-100 text-red-800" : item.classification === "Próximo a vencer" ? "bg-amber-100 text-amber-800" : item.classification === "Con cita futura" ? "bg-green-100 text-green-800" : "bg-sky-100 text-sky-800"}`}>{item.classification}</span></td>
                    <td className="px-5 py-4 text-right"><button onClick={async () => setSelected(await getFollowup(item.id))} className="text-sm font-bold text-green-700">Gestionar</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!items.length && <p className="py-14 text-center text-sm text-slate-500">No hay seguimientos para los filtros seleccionados.</p>}
          </div>
        )}
      </section>

      {selected && (
        <FollowupDetail
          item={selected}
          onClose={() => setSelected(null)}
          onChanged={async () => { setSelected(await getFollowup(selected.id)); await load(); }}
        />
      )}
    </div>
  );
}

function FollowupDetail({ item, onClose, onChanged }: { item: Followup; onClose: () => void; onChanged: () => Promise<void> }) {
  const { hasPermission } = useAuth();
  const [action, setAction] = useState<"contact" | "schedule" | "close" | null>(null);
  const [type, setType] = useState("Llamada");
  const [result, setResult] = useState("Contactado");
  const [observation, setObservation] = useState("");
  const [nextContact, setNextContact] = useState("");
  const [closeStatus, setCloseStatus] = useState("Cerrado sin cita");
  const [options, setOptions] = useState<AgendaOptions | null>(null);
  const [dentistId, setDentistId] = useState(item.dentist_id);
  const [siteId, setSiteId] = useState(item.site_id);
  const [typeId, setTypeId] = useState("");
  const [dateValue, setDateValue] = useState("");
  const [timeValue, setTimeValue] = useState("09:00");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const availableDentists = (options?.dentists ?? []).filter(
    (dentist) => !siteId || dentist.site_ids.includes(siteId),
  );

  useEffect(() => {
    if (action === "schedule" && !options) {
      getAgendaOptions().then((loaded) => {
        setOptions(loaded);
        setTypeId(loaded.appointment_types[0]?.id ?? "");
      });
    }
  }, [action, options]);

  async function run() {
    setBusy(true); setError(null);
    try {
      if (action === "contact") {
        await registerFollowupContact(item.id, {
          management_type: type, result, observation: observation || null,
          next_contact_at: nextContact ? new Date(nextContact).toISOString() : null,
        });
      } else if (action === "schedule") {
        const selectedSiteTimezone =
          options?.sites.find((site) => site.id === siteId)?.timezone ??
          options?.timezone ??
          FALLBACK_TIMEZONE;
        const starts = zonedDateTimeToIso(
          dateValue,
          timeValue,
          selectedSiteTimezone,
        );
        const duration = options?.appointment_types.find((item) => item.id === typeId)
          ?.suggested_duration_minutes ?? 30;
        const end = new Date(starts); end.setMinutes(end.getMinutes() + duration);
        await scheduleFollowupAppointment(item.id, {
          dentist_id: dentistId, site_id: siteId, appointment_type_id: typeId,
          starts_at: starts, ends_at: end.toISOString(), reason: item.reason,
        });
      } else if (action === "close") {
        await closeFollowup(item.id, observation, closeStatus);
      }
      setAction(null); await onChanged();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.detail ?? caught.message : "No fue posible completar la gestión.");
    } finally { setBusy(false); }
  }

  async function openWhatsApp() {
    try {
      const response = await generateFollowupWhatsApp(item.id);
      window.open(response.url, "_blank", "noopener,noreferrer");
      await onChanged();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.detail ?? caught.message : "No fue posible generar WhatsApp.");
    }
  }

  return (
    <Modal open title="Detalle de seguimiento" onClose={onClose}>
      <div className="space-y-5">
        {error && <Alert tone="error">{error}</Alert>}
        <div><h3 className="text-xl font-black">{item.patient_name}</h3><p className="mt-1 text-sm text-slate-500">{item.contact_mobile} · {item.site_name}</p></div>
        <dl className="grid gap-3 rounded-2xl bg-slate-50 p-4 text-sm sm:grid-cols-2">
          <div><dt className="text-slate-500">Control recomendado</dt><dd className="font-bold">{formatDate(item.followup_date)}</dd></div>
          <div><dt className="text-slate-500">Clasificación</dt><dd className="font-bold">{item.classification}</dd></div>
          <div className="sm:col-span-2"><dt className="text-slate-500">Motivo</dt><dd className="font-bold">{item.reason}</dd></div>
        </dl>
        {item.attention_description && (
          <div className="rounded-2xl border border-violet-100 bg-violet-50 p-4 text-sm">
            <p className="font-bold text-violet-900">Resumen de atención</p>
            <p className="mt-2 text-violet-800">{item.attention_description}</p>
            {item.prescribed_medications && <p className="mt-2 text-violet-800"><strong>Medicamentos:</strong> {item.prescribed_medications}</p>}
          </div>
        )}
        {!action && (
          <div className="flex flex-wrap gap-2">
            {hasPermission("followups.contact") && <><button onClick={() => setAction("contact")} className="rounded-xl border border-slate-300 px-4 py-2 font-bold">Registrar contacto</button><button onClick={openWhatsApp} className="rounded-xl bg-green-600 px-4 py-2 font-bold text-white">WhatsApp</button></>}
            {hasPermission("followups.manage") && hasPermission("appointments.create") && item.status !== "Cita programada" && <button onClick={() => setAction("schedule")} className="rounded-xl bg-dentia-primary px-4 py-2 font-bold text-white">Programar cita</button>}
            {hasPermission("followups.manage") && !["Cerrado sin cita", "No desea continuar"].includes(item.status) && <button onClick={() => setAction("close")} className="rounded-xl border border-red-200 px-4 py-2 font-bold text-red-700">Cerrar</button>}
            {hasPermission("followups.manage") && ["Cerrado sin cita", "No desea continuar"].includes(item.status) && <button onClick={async () => { await reopenFollowup(item.id); await onChanged(); }} className="rounded-xl bg-sky-600 px-4 py-2 font-bold text-white">Reabrir</button>}
          </div>
        )}
        {action === "contact" && <Action title="Registrar contacto"><Select label="Medio" value={type} onChange={setType} values={["WhatsApp", "Llamada", "Presencial"]}/><Select label="Resultado" value={result} onChange={setResult} values={["Contactado", "No respondió", "Número inválido", "Contactar después", "No desea continuar"]}/><Input label="Observación" value={observation} onChange={setObservation}/><label><span className="mb-1 block text-sm font-bold">Próximo contacto</span><input type="datetime-local" value={nextContact} onChange={(event) => setNextContact(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3"/></label><Buttons busy={busy} onCancel={() => setAction(null)} onSave={run}/></Action>}
        {action === "close" && <Action title="Cerrar seguimiento"><Select label="Resultado" value={closeStatus} onChange={setCloseStatus} values={["Cerrado sin cita", "No desea continuar"]}/><Input label="Motivo" value={observation} onChange={setObservation}/><Buttons busy={busy} disabled={observation.trim().length < 2} onCancel={() => setAction(null)} onSave={run}/></Action>}
        {action === "schedule" && options && <Action title="Programar cita"><Select label="Sede" value={siteId} onChange={(value)=>{setSiteId(value); const dentist=options.dentists.find((x)=>x.id===dentistId); if (dentist && !dentist.site_ids.includes(value)) setDentistId("");}} options={options.sites.map((x) => ({value:x.id,label:`${x.name} · ${x.address}`}))}/><Select label="Odontólogo" value={dentistId} onChange={setDentistId} options={availableDentists.map((x) => ({value:x.id,label:x.name}))}/>{siteId && availableDentists.length === 0 && <Alert tone="warning">No hay odontólogos asociados a esta sede.</Alert>}<Select label="Tipo" value={typeId} onChange={setTypeId} options={options.appointment_types.map((x) => ({value:x.id,label:x.name}))}/><div className="grid gap-3 sm:grid-cols-2"><label><span className="mb-1 block text-sm font-bold">Fecha</span><input type="date" value={dateValue} onChange={(event) => setDateValue(event.target.value)} className="min-h-11 w-full rounded-xl border px-3"/></label><label><span className="mb-1 block text-sm font-bold">Hora</span><input type="time" step={900} value={timeValue} onChange={(event) => setTimeValue(event.target.value)} className="min-h-11 w-full rounded-xl border px-3"/></label></div><Buttons busy={busy} disabled={!dateValue || !typeId || !siteId || !dentistId} onCancel={() => setAction(null)} onSave={run}/></Action>}
        <div><h4 className="font-bold">Historial de gestiones</h4>{item.managements.map((management) => <div key={management.id} className="mt-2 rounded-xl border p-3 text-sm"><strong>{management.management_type} · {management.result}</strong><p className="text-xs text-slate-500">{formatDate(management.occurred_at, true)}</p>{management.observation && <p className="mt-1">{management.observation}</p>}</div>)}{!item.managements.length && <p className="mt-2 text-sm text-slate-500">Sin gestiones registradas.</p>}</div>
      </div>
    </Modal>
  );
}

function Action({title,children}:{title:string;children:React.ReactNode}) { return <div className="space-y-3 rounded-2xl bg-slate-50 p-4"><h4 className="font-black">{title}</h4>{children}</div>; }
function Input({label,value,onChange}:{label:string;value:string;onChange:(v:string)=>void}) { return <label><span className="mb-1 block text-sm font-bold">{label}</span><input value={value} onChange={(e)=>onChange(e.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3"/></label>; }
function Select({label,value,onChange,values,options}:{label:string;value:string;onChange:(v:string)=>void;values?:string[];options?:{value:string;label:string}[]}) { const opts=options??(values??[]).map(x=>({value:x,label:x})); return <label><span className="mb-1 block text-sm font-bold">{label}</span><select value={value} onChange={(e)=>onChange(e.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3">{opts.map(x=><option key={x.value} value={x.value}>{x.label}</option>)}</select></label>; }
function Buttons({busy,disabled,onCancel,onSave}:{busy:boolean;disabled?:boolean;onCancel:()=>void;onSave:()=>void}) { return <div className="flex justify-end gap-2"><button onClick={onCancel} className="rounded-xl border px-4 py-2 font-bold">Cancelar</button><button disabled={busy||disabled} onClick={onSave} className="rounded-xl bg-dentia-primary px-4 py-2 font-bold text-white disabled:opacity-50">Guardar</button></div>; }
