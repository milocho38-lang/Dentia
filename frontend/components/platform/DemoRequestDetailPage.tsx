"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { persistAndRefetchDemoRequest } from "@/lib/demoRequestMutation.mjs";
import {
  addDemoRequestNote,
  assignDemoRequest,
  getDemoRequest,
  listDemoRequestOwners,
  scheduleDemoRequest,
  updateDemoRequestStatus,
} from "@/services/demoRequestService";
import type { DemoRequestDetail, DemoRequestOwner, DemoRequestStatus } from "@/types/demoRequest";
import { DEMO_STATUS_LABELS, PRACTICE_LABELS, formatDemoDate } from "./DemoRequestsPage";

export function DemoRequestDetailPage({ demoRequestId }: { demoRequestId: string }) {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("platform.demo_requests.manage");
  const [item, setItem] = useState<DemoRequestDetail | null>(null);
  const [owners, setOwners] = useState<DemoRequestOwner[]>([]);
  const [ownerId, setOwnerId] = useState("");
  const [scheduleAt, setScheduleAt] = useState("");
  const [timezone, setTimezone] = useState("America/Bogota");
  const [meetingUrl, setMeetingUrl] = useState("");
  const [scheduleNote, setScheduleNote] = useState("");
  const [note, setNote] = useState("");
  const [statusReason, setStatusReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  function applyDetail(detail: DemoRequestDetail) {
    setItem(detail);
    setOwnerId(detail.assigned_to?.id ?? "");
    setTimezone(detail.timezone ?? "America/Bogota");
    setMeetingUrl(detail.meeting_url ?? "");
  }

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [detail, ownerResponse] = await Promise.all([
        getDemoRequest(demoRequestId),
        listDemoRequestOwners(),
      ]);
      applyDetail(detail);
      setOwners(ownerResponse.items);
    } catch {
      setError("No fue posible cargar la solicitud de demo.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [demoRequestId]);

  async function mutate(
    action: () => Promise<DemoRequestDetail>,
    successMessage: string,
  ): Promise<boolean> {
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const persisted = await persistAndRefetchDemoRequest(
        action,
        () => getDemoRequest(demoRequestId),
      );
      applyDetail(persisted);
      setSuccess(successMessage);
      return true;
    } catch {
      setError("No fue posible guardar el cambio. Recarga la solicitud e intenta nuevamente.");
      return false;
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner className="h-8 w-8 text-green-700" /></div>;
  if (!item) return <div className="mx-auto max-w-4xl">{error && <Alert tone="error">{error}</Alert>}</div>;

  const statusActions: Array<{ status: DemoRequestStatus; label: string }> =
    item.status === "NEW"
      ? [{ status: "CONTACTED", label: "Marcar como contactado" }, { status: "NOT_CONTINUING", label: "No continúa" }]
      : item.status === "CONTACTED"
        ? [{ status: "NOT_CONTINUING", label: "No continúa" }]
        : item.status === "DEMO_SCHEDULED"
          ? [{ status: "DEMO_COMPLETED", label: "Marcar demo realizada" }, { status: "NOT_CONTINUING", label: "No continúa" }]
          : item.status === "DEMO_COMPLETED"
            ? [{ status: "CONVERTED", label: "Marcar convertido" }, { status: "NOT_CONTINUING", label: "No continúa" }]
            : [];

  return (
    <div className="mx-auto max-w-6xl">
      <Link href="/administracion/solicitudes-demo" className="text-sm font-bold text-green-700">← Volver a solicitudes</Link>
      <header className="mt-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">Solicitud de demo</p>
          <h1 className="mt-2 text-3xl font-black">{item.first_name} {item.last_name}</h1>
          <p className="mt-2 text-sm text-slate-500">Recibida {formatDemoDate(item.created_at)}</p>
        </div>
        <span className="self-start rounded-full bg-green-50 px-3 py-2 text-sm font-bold text-green-800">{DEMO_STATUS_LABELS[item.status]}</span>
      </header>
      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
      {success && <div className="mt-5"><Alert>{success}</Alert></div>}

      <div className="mt-6 grid gap-5 lg:grid-cols-[1fr_1fr]">
        <div className="space-y-5">
          <Card title="Datos de contacto">
            <Definition label="Email" value={item.email} />
            <Definition label="WhatsApp / teléfono" value={item.phone} />
            <Definition label="País / ciudad" value={`${item.country} · ${item.city}`} />
          </Card>
          <Card title="Datos comerciales">
            <Definition label="Tipo de práctica" value={PRACTICE_LABELS[item.practice_type]} />
            <Definition label="Número de odontólogos" value={String(item.dentist_count)} />
            <Definition label="Fuente" value={item.source === "WEBSITE" ? "Website" : item.source} />
            <Definition label="Mensaje original" value={item.message ?? "Sin mensaje"} preserve />
            <Definition label="Autorización de contacto" value={`${formatDemoDate(item.consent_at)} · ${item.consent_version}`} />
          </Card>
          <Card title="Notas internas">
            {item.notes.length ? (
              <div className="space-y-3">
                {item.notes.map((entry) => (
                  <article key={entry.id} className="rounded-xl bg-slate-50 p-3">
                    <p className="whitespace-pre-wrap text-sm text-slate-700">{entry.text}</p>
                    <p className="mt-2 text-xs text-slate-500">{entry.author.name} · {formatDemoDate(entry.created_at)}</p>
                  </article>
                ))}
              </div>
            ) : <p className="text-sm text-slate-500">Aún no hay notas internas.</p>}
            {canManage && (
              <form
                className="mt-4"
                onSubmit={async (event) => {
                  event.preventDefault();
                  if (!note.trim()) return;
                  const saved = await mutate(
                    () => addDemoRequestNote(item.id, note, item.row_version),
                    "Nota interna guardada.",
                  );
                  if (saved) setNote("");
                }}
              >
                <label className="text-sm font-bold">Agregar nota interna</label>
                <p className="mt-1 text-xs text-slate-500">Se guarda como un registro independiente y no reemplaza el motivo de cierre.</p>
                <textarea value={note} onChange={(event) => setNote(event.target.value)} className="mt-1 min-h-28 w-full rounded-xl border p-3" maxLength={2000} />
                <button type="submit" disabled={busy || !note.trim()} className="mt-2 min-h-10 rounded-xl bg-green-700 px-4 font-bold text-white disabled:opacity-50">Guardar nota interna</button>
              </form>
            )}
          </Card>
        </div>

        <div className="space-y-5">
          <Card title="Seguimiento">
            <Definition label="Contactado" value={formatDemoDate(item.contacted_at)} />
            <Definition label="Demo agendada" value={formatDemoDate(item.scheduled_at)} />
            <Definition label="Zona horaria" value={item.timezone ?? "—"} />
            <Definition label="Enlace de reunión" value={item.meeting_url ?? "—"} />
            <Definition label="Conversión" value={formatDemoDate(item.converted_at)} />
          </Card>

          {canManage && (
            <Card title="Responsable">
              <select value={ownerId} onChange={(event) => setOwnerId(event.target.value)} className="min-h-11 w-full rounded-xl border bg-white px-3">
                <option value="">Sin asignar</option>
                {owners.map((owner) => <option key={owner.id} value={owner.id}>{owner.name} · {owner.email}</option>)}
              </select>
              <button type="button" disabled={busy} onClick={() => mutate(() => assignDemoRequest(item.id, ownerId || null, item.row_version), "Responsable actualizado.")} className="mt-3 min-h-10 rounded-xl border px-4 font-bold text-slate-700 disabled:opacity-50">Guardar responsable</button>
            </Card>
          )}

          {canManage && item.status !== "CONVERTED" && item.status !== "NOT_CONTINUING" && (
            <Card title="Agendar demo">
              <form
                className="space-y-3"
                onSubmit={async (event: FormEvent) => {
                  event.preventDefault();
                  if (!scheduleAt || !ownerId) return;
                  const saved = await mutate(() => scheduleDemoRequest(item.id, {
                    // datetime-local intentionally has no offset: the backend
                    // interprets it in the explicitly selected IANA timezone.
                    scheduled_at: scheduleAt,
                    timezone,
                    meeting_url: meetingUrl || null,
                    assigned_to_user_id: ownerId,
                    note: scheduleNote || null,
                    row_version: item.row_version,
                  }), "Demo agendada.");
                  if (saved) setScheduleNote("");
                }}
              >
                <Field label="Fecha y hora"><input type="datetime-local" required value={scheduleAt} onChange={(event) => setScheduleAt(event.target.value)} className="min-h-11 w-full rounded-xl border px-3" /></Field>
                <Field label="Zona horaria"><select value={timezone} onChange={(event) => setTimezone(event.target.value)} className="min-h-11 w-full rounded-xl border bg-white px-3"><option value="America/Bogota">America/Bogota</option><option value="America/Santiago">America/Santiago</option></select></Field>
                <Field label="Enlace de reunión (opcional)"><input type="url" value={meetingUrl} onChange={(event) => setMeetingUrl(event.target.value)} className="min-h-11 w-full rounded-xl border px-3" placeholder="https://" /></Field>
                <Field label="Nota de agenda (opcional)"><textarea value={scheduleNote} onChange={(event) => setScheduleNote(event.target.value)} className="min-h-20 w-full rounded-xl border p-3" /></Field>
                {!ownerId && <p className="text-xs text-amber-700">Selecciona y guarda un responsable.</p>}
                <button type="submit" disabled={busy || !scheduleAt || !ownerId} className="min-h-10 rounded-xl bg-green-700 px-4 font-bold text-white disabled:opacity-50">Agendar demo</button>
              </form>
            </Card>
          )}

          {canManage && statusActions.length > 0 && (
            <Card title="Actualizar estado">
              <label className="text-sm font-bold">Motivo del cambio de estado (opcional)</label>
              <p className="mt-1 text-xs text-slate-500">Este motivo se registra con la transición. Para seguimiento general usa “Agregar nota interna”.</p>
              <textarea value={statusReason} onChange={(event) => setStatusReason(event.target.value)} className="mt-1 min-h-20 w-full rounded-xl border p-3" maxLength={1000} />
              <div className="mt-3 flex flex-wrap gap-2">
                {statusActions.map((action) => (
                  <button
                    type="button"
                    key={action.status}
                    disabled={busy}
                    onClick={async () => {
                      const saved = await mutate(
                        () => updateDemoRequestStatus(item.id, action.status, item.row_version, statusReason),
                        action.status === "CONTACTED"
                          ? "Contacto registrado."
                          : "Estado actualizado.",
                      );
                      if (saved) setStatusReason("");
                    }}
                    className="min-h-10 rounded-xl border px-4 font-bold text-slate-700 disabled:opacity-50"
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-2xl border bg-white p-5 shadow-sm"><h2 className="text-lg font-black text-slate-950">{title}</h2><div className="mt-4 space-y-3">{children}</div></section>;
}

function Definition({ label, value, preserve = false }: { label: string; value: string; preserve?: boolean }) {
  return <div><dt className="text-xs font-bold uppercase tracking-wide text-slate-400">{label}</dt><dd className={`mt-1 text-sm text-slate-700 ${preserve ? "whitespace-pre-wrap" : ""}`}>{value}</dd></div>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label><span className="mb-1 block text-sm font-bold">{label}</span>{children}</label>;
}
