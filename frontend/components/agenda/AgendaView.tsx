"use client";

import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { DateClickArg } from "@fullcalendar/interaction";
import type {
  DatesSetArg,
  EventClickArg,
  EventContentArg,
} from "@fullcalendar/core";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Modal } from "@/components/shared/Modal";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import {
  cancelAppointment,
  confirmAppointment,
  createAppointment,
  createQuickPatient,
  getAgendaEvents,
  getAgendaOptions,
  rescheduleAppointment,
} from "@/services/agendaService";
import { ApiError } from "@/services/apiClient";
import type {
  AgendaOptions,
  Appointment,
  ConflictPayload,
  PatientOption,
} from "@/types/agenda";

const BOGOTA_OFFSET = "-05:00";
const TERMINAL_STATES = new Set([
  "Atendida",
  "Cancelada",
  "No Asistió",
  "Reprogramada",
]);

function bogotaDate(date = new Date()) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Bogota",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function dayRange(date: string) {
  const start = `${date}T00:00:00${BOGOTA_OFFSET}`;
  const next = new Date(`${date}T12:00:00${BOGOTA_OFFSET}`);
  next.setUTCDate(next.getUTCDate() + 1);
  return {
    start,
    end: `${bogotaDate(next)}T00:00:00${BOGOTA_OFFSET}`,
  };
}

function calendarRange(start: string, end: string) {
  const startDate = start.slice(0, 10);
  const endDate = end.slice(0, 10);
  return {
    start: `${startDate}T00:00:00${BOGOTA_OFFSET}`,
    end: `${endDate}T00:00:00${BOGOTA_OFFSET}`,
  };
}

function toIso(date: string, time: string) {
  return `${date}T${time}:00${BOGOTA_OFFSET}`;
}

function addMinutes(date: string, time: string, minutes: number) {
  const value = new Date(toIso(date, time));
  value.setMinutes(value.getMinutes() + minutes);
  return value.toISOString();
}

function localTime(value: string) {
  return new Intl.DateTimeFormat("es-CO", {
    timeZone: "America/Bogota",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function localDate(value: string) {
  return new Intl.DateTimeFormat("es-CO", {
    timeZone: "America/Bogota",
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date(value));
}

function statusClasses(status: string) {
  const styles: Record<string, string> = {
    Programada: "bg-sky-100 text-sky-800",
    Confirmada: "bg-emerald-100 text-emerald-800",
    Atendida: "bg-violet-100 text-violet-800",
    Cancelada: "bg-red-100 text-red-800",
    "No Asistió": "bg-slate-200 text-slate-700",
    Reprogramada: "bg-amber-100 text-amber-800",
  };
  return styles[status] ?? "bg-slate-100 text-slate-700";
}

function conflictFrom(error: unknown) {
  if (!(error instanceof ApiError) || error.status !== 409) return null;
  const payload = error.payload;
  if (
    payload &&
    typeof payload === "object" &&
    "message" in payload &&
    "conflicts" in payload
  ) {
    return payload as ConflictPayload;
  }
  return null;
}

export function AgendaView() {
  const calendarRef = useRef<FullCalendar | null>(null);
  const { hasPermission } = useAuth();
  const [date, setDate] = useState(bogotaDate());
  const [calendarView, setCalendarView] = useState<
    "timeGridDay" | "timeGridWeek"
  >("timeGridDay");
  const [visibleRange, setVisibleRange] = useState(() =>
    dayRange(bogotaDate()),
  );
  const [options, setOptions] = useState<AgendaOptions | null>(null);
  const [events, setEvents] = useState<Appointment[]>([]);
  const [dentistId, setDentistId] = useState("");
  const [siteId, setSiteId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newOpen, setNewOpen] = useState(false);
  const [newStartTime, setNewStartTime] = useState("08:00");
  const [selected, setSelected] = useState<Appointment | null>(null);

  const loadEvents = useCallback(async () => {
    try {
      setError(null);
      const items = await getAgendaEvents(
        visibleRange.start,
        visibleRange.end,
        dentistId || undefined,
        siteId || undefined,
      );
      setEvents(items);
    } catch (loadError) {
      setError(
        loadError instanceof ApiError
          ? loadError.detail ?? loadError.message
          : "No fue posible cargar la agenda.",
      );
    }
  }, [dentistId, siteId, visibleRange.end, visibleRange.start]);

  useEffect(() => {
    getAgendaOptions()
      .then((loaded) => {
        setOptions(loaded);
        if (loaded.dentists.length === 1) {
          setDentistId(loaded.dentists[0].id);
        }
      })
      .catch(() => setError("No fue posible cargar las opciones de agenda."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!options) return;
    loadEvents();
  }, [loadEvents, options]);

  const calendarEvents = useMemo(
    () =>
      events.map((appointment) => ({
        id: appointment.id,
        title: appointment.patient_name,
        start: appointment.starts_at,
        end: appointment.ends_at,
        backgroundColor: appointment.is_overbook ? "#f97316" : "#16a34a",
        borderColor: appointment.is_overbook ? "#ea580c" : "#15803d",
        textColor: "#ffffff",
        extendedProps: { appointment },
      })),
    [events],
  );

  function openAtTime(arg: DateClickArg) {
    if (!hasPermission("appointments.create")) return;
    setDate(bogotaDate(arg.date));
    setNewStartTime(localTime(arg.date.toISOString()));
    setNewOpen(true);
  }

  function handleDatesSet(arg: DatesSetArg) {
    const range = calendarRange(arg.startStr, arg.endStr);
    setCalendarView(
      arg.view.type === "timeGridWeek" ? "timeGridWeek" : "timeGridDay",
    );
    setDate(bogotaDate(arg.view.calendar.getDate()));
    setVisibleRange((current) => {
      if (current.start === range.start && current.end === range.end) {
        return current;
      }
      return range;
    });
  }

  function changeView(view: "timeGridDay" | "timeGridWeek") {
    calendarRef.current?.getApi().changeView(view);
  }

  function navigateCalendar(action: "today" | "prev" | "next") {
    calendarRef.current?.getApi()[action]();
  }

  function goToDate(value: string) {
    setDate(value);
    calendarRef.current?.getApi().gotoDate(value);
  }

  function renderEvent(arg: EventContentArg) {
    const appointment = arg.event.extendedProps
      .appointment as Appointment;
    return (
      <div className="overflow-hidden px-1 py-0.5 text-xs leading-tight">
        <div className="truncate font-bold">{appointment.patient_name}</div>
        <div className="mt-0.5 truncate opacity-90">
          {appointment.appointment_type_name} · {appointment.site_name}
        </div>
        {appointment.is_overbook && (
          <span className="mt-1 inline-flex rounded bg-white/90 px-1.5 py-0.5 text-[10px] font-extrabold uppercase text-orange-700">
            Sobrecupo
          </span>
        )}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-[420px] items-center justify-center gap-3 text-slate-500">
        <Spinner className="h-7 w-7 text-dentia-primary" />
        Preparando la agenda…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.16em] text-green-700">
            Operación diaria
          </p>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-900">
            Agenda
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Horario en America/Bogota · intervalos de 15 minutos
          </p>
        </div>
        {hasPermission("appointments.create") && (
          <button
            type="button"
            onClick={() => setNewOpen(true)}
            className="min-h-12 rounded-xl bg-dentia-primary px-5 font-bold text-white shadow-sm hover:bg-green-700"
          >
            + Nueva cita
          </button>
        )}
      </header>

      {error && <Alert tone="error">{error}</Alert>}

      <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
        <div className="mb-5 flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div
              className="inline-flex rounded-xl border border-slate-200 bg-slate-50 p-1"
              aria-label="Vista de agenda"
            >
              <button
                type="button"
                onClick={() => changeView("timeGridDay")}
                aria-pressed={calendarView === "timeGridDay"}
                className={`min-h-10 rounded-lg px-4 text-sm font-bold transition ${
                  calendarView === "timeGridDay"
                    ? "bg-white text-green-800 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Día
              </button>
              <button
                type="button"
                onClick={() => changeView("timeGridWeek")}
                aria-pressed={calendarView === "timeGridWeek"}
                className={`min-h-10 rounded-lg px-4 text-sm font-bold transition ${
                  calendarView === "timeGridWeek"
                    ? "bg-white text-green-800 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Semana
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => navigateCalendar("today")}
                className="min-h-10 rounded-xl border border-slate-300 px-4 text-sm font-bold text-slate-700 hover:bg-slate-50"
              >
                Hoy
              </button>
              <button
                type="button"
                onClick={() => navigateCalendar("prev")}
                className="min-h-10 rounded-xl border border-slate-300 px-4 text-sm font-bold text-slate-700 hover:bg-slate-50"
              >
                ← Anterior
              </button>
              <button
                type="button"
                onClick={() => navigateCalendar("next")}
                className="min-h-10 rounded-xl border border-slate-300 px-4 text-sm font-bold text-slate-700 hover:bg-slate-50"
              >
                Siguiente →
              </button>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-[minmax(170px,0.7fr)_1fr_1fr]">
          <label>
            <span className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-slate-500">
              Fecha
            </span>
            <input
              type="date"
              value={date}
              onChange={(event) => goToDate(event.target.value)}
              className="min-h-11 w-full rounded-xl border border-slate-300 px-3"
            />
          </label>
          <label>
            <span className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-slate-500">
              Odontólogo
            </span>
            <select
              value={dentistId}
              onChange={(event) => setDentistId(event.target.value)}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
            >
              <option value="">Todos</option>
              {options?.dentists.map((dentist) => (
                <option key={dentist.id} value={dentist.id}>
                  {dentist.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-slate-500">
              Sede
            </span>
            <select
              value={siteId}
              onChange={(event) => setSiteId(event.target.value)}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
            >
              <option value="">Todas las sedes</option>
              {options?.sites.map((site) => (
                <option key={site.id} value={site.id}>
                  {site.name}
                </option>
              ))}
            </select>
          </label>
          </div>
        </div>

        {options?.dentists.length === 0 ? (
          <Alert tone="warning">
            No hay un perfil de odontólogo asociado a tus sedes.
          </Alert>
        ) : (
          <div className="dentia-calendar min-w-0 overflow-x-auto">
            <div className="min-w-[680px]">
              <FullCalendar
                ref={calendarRef}
                plugins={[timeGridPlugin, interactionPlugin]}
                initialView="timeGridDay"
                initialDate={date}
                headerToolbar={false}
                allDaySlot={false}
                slotMinTime="06:00:00"
                slotMaxTime="21:00:00"
                slotDuration="00:15:00"
                slotLabelInterval="01:00"
                height="auto"
                locale="es"
                timeZone="America/Bogota"
                nowIndicator
                editable={false}
                selectable={hasPermission("appointments.create")}
                events={calendarEvents}
                dateClick={openAtTime}
                eventClick={(arg: EventClickArg) =>
                  setSelected(
                    arg.event.extendedProps.appointment as Appointment,
                  )
                }
                eventContent={renderEvent}
                datesSet={handleDatesSet}
              />
            </div>
          </div>
        )}
      </section>

      {options && (
        <AppointmentForm
          open={newOpen}
          date={date}
          initialTime={newStartTime}
          options={options}
          defaultDentistId={dentistId}
          defaultSiteId={siteId}
          canOverbook={hasPermission("appointments.overbook")}
          onClose={() => setNewOpen(false)}
          onCreated={async () => {
            setNewOpen(false);
            setOptions(await getAgendaOptions());
            await loadEvents();
          }}
        />
      )}

      {selected && options && (
        <AppointmentDetail
          appointment={selected}
          options={options}
          canUpdate={hasPermission("appointments.update")}
          canCancel={hasPermission("appointments.cancel")}
          canOverbook={hasPermission("appointments.overbook")}
          onClose={() => setSelected(null)}
          onChanged={async (appointment) => {
            setSelected(appointment);
            await loadEvents();
          }}
        />
      )}
    </div>
  );
}

function AppointmentForm({
  open,
  date,
  initialTime,
  options,
  defaultDentistId,
  defaultSiteId,
  canOverbook,
  onClose,
  onCreated,
}: {
  open: boolean;
  date: string;
  initialTime: string;
  options: AgendaOptions;
  defaultDentistId: string;
  defaultSiteId: string;
  canOverbook: boolean;
  onClose: () => void;
  onCreated: () => Promise<void>;
}) {
  const [patientId, setPatientId] = useState("");
  const [dentistId, setDentistId] = useState(defaultDentistId);
  const [siteId, setSiteId] = useState(defaultSiteId);
  const [typeId, setTypeId] = useState("");
  const [appointmentDate, setAppointmentDate] = useState(date);
  const [time, setTime] = useState(initialTime);
  const [duration, setDuration] = useState(30);
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState<ConflictPayload | null>(null);
  const [overbookReason, setOverbookReason] = useState("");
  const [quickPatient, setQuickPatient] = useState(false);
  const [patients, setPatients] = useState(options.patients);

  useEffect(() => {
    if (!open) return;
    setAppointmentDate(date);
    setTime(initialTime);
    setDentistId(defaultDentistId || options.dentists[0]?.id || "");
    setSiteId(defaultSiteId || options.sites[0]?.id || "");
    if (!typeId && options.appointment_types[0]) {
      setTypeId(options.appointment_types[0].id);
      setDuration(options.appointment_types[0].suggested_duration_minutes);
    }
  }, [date, defaultDentistId, defaultSiteId, initialTime, open, options, typeId]);

  const selectedDentist = options.dentists.find(
    (dentist) => dentist.id === dentistId,
  );
  const availableSites = options.sites.filter(
    (site) => !selectedDentist || selectedDentist.site_ids.includes(site.id),
  );

  async function save(isOverbook = false) {
    setError(null);
    setConflict(null);
    if (!patientId || !dentistId || !siteId || !typeId || !reason.trim()) {
      setError("Completa paciente, odontólogo, sede, tipo y motivo.");
      return;
    }
    setSaving(true);
    try {
      await createAppointment({
        patient_id: patientId,
        dentist_id: dentistId,
        site_id: siteId,
        appointment_type_id: typeId,
        starts_at: toIso(appointmentDate, time),
        ends_at: addMinutes(appointmentDate, time, duration),
        reason: reason.trim(),
        is_overbook: isOverbook,
        overbook_reason: isOverbook ? overbookReason.trim() : null,
      });
      await onCreated();
    } catch (saveError) {
      const foundConflict = conflictFrom(saveError);
      if (foundConflict) {
        setConflict(foundConflict);
      } else {
        setError(
          saveError instanceof ApiError
            ? saveError.detail ?? saveError.message
            : "No fue posible crear la cita.",
        );
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open={open} title="Nueva cita" onClose={onClose}>
      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          save(false);
        }}
      >
        {error && <Alert tone="error">{error}</Alert>}
        {conflict && (
          <Alert tone="warning">
            <p className="font-bold">{conflict.message}</p>
            {conflict.conflicts.map((item) => (
              <p key={item.id} className="mt-1 text-xs">
                {localTime(item.starts_at)}–{localTime(item.ends_at)} ·{" "}
                {item.patient_name}
              </p>
            ))}
          </Alert>
        )}

        <label className="block">
          <span className="mb-2 block text-sm font-bold text-slate-700">
            Paciente
          </span>
          <div className="flex gap-2">
            <select
              value={patientId}
              onChange={(event) => setPatientId(event.target.value)}
              className="min-h-12 min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-3"
            >
              <option value="">Selecciona un paciente</option>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.full_name} · {patient.document}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setQuickPatient((current) => !current)}
              className="rounded-xl border border-green-200 px-3 text-sm font-bold text-green-700"
            >
              + Nuevo
            </button>
          </div>
        </label>

        {quickPatient && (
          <QuickPatientForm
            onCreated={(patient) => {
              setPatients((current) => [...current, patient]);
              setPatientId(patient.id);
              setQuickPatient(false);
            }}
          />
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <FieldSelect
            label="Odontólogo"
            value={dentistId}
            onChange={(value) => {
              setDentistId(value);
              const dentist = options.dentists.find((item) => item.id === value);
              if (dentist && !dentist.site_ids.includes(siteId)) {
                setSiteId(dentist.site_ids[0] ?? "");
              }
            }}
            options={options.dentists.map((item) => ({
              value: item.id,
              label: item.name,
            }))}
          />
          <FieldSelect
            label="Sede"
            value={siteId}
            onChange={setSiteId}
            options={availableSites.map((item) => ({
              value: item.id,
              label: item.name,
            }))}
          />
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">
              Fecha
            </span>
            <input
              type="date"
              value={appointmentDate}
              onChange={(event) => setAppointmentDate(event.target.value)}
              className="min-h-12 w-full rounded-xl border border-slate-300 px-3"
            />
          </label>
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">
              Hora
            </span>
            <input
              type="time"
              step={900}
              value={time}
              onChange={(event) => setTime(event.target.value)}
              className="min-h-12 w-full rounded-xl border border-slate-300 px-3"
            />
          </label>
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">
              Tipo de cita
            </span>
            <select
              value={typeId}
              onChange={(event) => {
                setTypeId(event.target.value);
                const type = options.appointment_types.find(
                  (item) => item.id === event.target.value,
                );
                if (type) setDuration(type.suggested_duration_minutes);
              }}
              className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3"
            >
              {options.appointment_types.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
          </label>
          <FieldSelect
            label="Duración"
            value={String(duration)}
            onChange={(value) => setDuration(Number(value))}
            options={[15, 30, 45, 60, 75, 90, 120].map((value) => ({
              value: String(value),
              label: `${value} minutos`,
            }))}
          />
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-bold text-slate-700">
            Motivo
          </span>
          <input
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            maxLength={300}
            className="min-h-12 w-full rounded-xl border border-slate-300 px-3"
            placeholder="Ej. valoración inicial"
          />
        </label>

        {conflict?.can_overbook && canOverbook && (
          <label className="block">
            <span className="mb-2 block text-sm font-bold text-orange-800">
              Justificación del sobrecupo
            </span>
            <input
              value={overbookReason}
              onChange={(event) => setOverbookReason(event.target.value)}
              className="min-h-12 w-full rounded-xl border border-orange-300 px-3"
              placeholder="Motivo para autorizar el cruce"
            />
          </label>
        )}

        <div className="flex flex-wrap justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="min-h-11 rounded-xl border border-slate-300 px-4 font-bold text-slate-700"
          >
            Cancelar
          </button>
          {conflict?.can_overbook && canOverbook && (
            <button
              type="button"
              disabled={saving || !overbookReason.trim()}
              onClick={() => save(true)}
              className="min-h-11 rounded-xl bg-orange-600 px-4 font-bold text-white disabled:opacity-50"
            >
              Crear sobrecupo
            </button>
          )}
          <button
            type="submit"
            disabled={saving}
            className="flex min-h-11 items-center gap-2 rounded-xl bg-dentia-primary px-5 font-bold text-white disabled:opacity-60"
          >
            {saving && <Spinner className="h-4 w-4" />}
            Guardar cita
          </button>
        </div>
      </form>
    </Modal>
  );
}

function QuickPatientForm({
  onCreated,
}: {
  onCreated: (patient: PatientOption) => void;
}) {
  const [firstNames, setFirstNames] = useState("");
  const [lastNames, setLastNames] = useState("");
  const [document, setDocument] = useState("");
  const [mobile, setMobile] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      onCreated(
        await createQuickPatient({
          first_names: firstNames,
          last_names: lastNames,
          document,
          mobile,
        }),
      );
    } catch (submitError) {
      setError(
        submitError instanceof ApiError
          ? submitError.detail ?? submitError.message
          : "No fue posible crear el paciente.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-2xl border border-green-200 bg-green-50/60 p-4">
      <p className="font-bold text-green-900">Paciente rápido</p>
      {error && <div className="mt-3"><Alert tone="error">{error}</Alert></div>}
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {[
          ["Nombres", firstNames, setFirstNames],
          ["Apellidos", lastNames, setLastNames],
          ["Documento", document, setDocument],
          ["Celular", mobile, setMobile],
        ].map(([label, value, setter]) => (
          <label key={label as string}>
            <span className="mb-1 block text-xs font-bold text-slate-600">
              {label as string}
            </span>
            <input
              value={value as string}
              onChange={(event) =>
                (setter as (value: string) => void)(event.target.value)
              }
              className="min-h-10 w-full rounded-lg border border-slate-300 bg-white px-3"
            />
          </label>
        ))}
      </div>
      <button
        type="button"
        disabled={saving}
        onClick={submit}
        className="mt-3 min-h-10 rounded-lg bg-green-700 px-4 text-sm font-bold text-white disabled:opacity-60"
      >
        Guardar paciente
      </button>
    </div>
  );
}

function AppointmentDetail({
  appointment,
  options,
  canUpdate,
  canCancel,
  canOverbook,
  onClose,
  onChanged,
}: {
  appointment: Appointment;
  options: AgendaOptions;
  canUpdate: boolean;
  canCancel: boolean;
  canOverbook: boolean;
  onClose: () => void;
  onChanged: (appointment: Appointment) => Promise<void>;
}) {
  const [action, setAction] = useState<"confirm" | "cancel" | "reschedule" | null>(null);
  const [method, setMethod] = useState("WhatsApp");
  const [reason, setReason] = useState("");
  const [date, setDate] = useState(bogotaDate(new Date(appointment.starts_at)));
  const [time, setTime] = useState(localTime(appointment.starts_at));
  const [siteId, setSiteId] = useState(appointment.site_id);
  const [dentistId, setDentistId] = useState(appointment.dentist_id);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState<ConflictPayload | null>(null);
  const [overbookReason, setOverbookReason] = useState("");
  const duration = Math.round(
    (new Date(appointment.ends_at).getTime() -
      new Date(appointment.starts_at).getTime()) /
      60000,
  );
  const terminal = TERMINAL_STATES.has(appointment.status);

  async function run(isOverbook = false) {
    setSaving(true);
    setError(null);
    setConflict(null);
    try {
      let updated: Appointment;
      if (action === "confirm") {
        updated = await confirmAppointment(appointment.id, method);
      } else if (action === "cancel") {
        updated = await cancelAppointment(appointment.id, reason);
      } else {
        updated = await rescheduleAppointment(appointment.id, {
          site_id: siteId,
          dentist_id: dentistId,
          starts_at: toIso(date, time),
          ends_at: addMinutes(date, time, duration),
          reason,
          is_overbook: isOverbook,
          overbook_reason: isOverbook ? overbookReason : null,
        });
      }
      setAction(null);
      await onChanged(updated);
    } catch (actionError) {
      const foundConflict = conflictFrom(actionError);
      if (foundConflict) setConflict(foundConflict);
      else {
        setError(
          actionError instanceof ApiError
            ? actionError.detail ?? actionError.message
            : "No fue posible completar la acción.",
        );
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open title="Detalle de la cita" onClose={onClose}>
      <div className="space-y-5">
        {error && <Alert tone="error">{error}</Alert>}
        {conflict && (
          <Alert tone="warning">
            <strong>{conflict.message}</strong>
            {conflict.conflicts.map((item) => (
              <p key={item.id} className="mt-1 text-xs">
                {localTime(item.starts_at)} · {item.patient_name}
              </p>
            ))}
          </Alert>
        )}
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-2xl font-black text-slate-900">
              {appointment.patient_name}
            </h3>
            <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${statusClasses(appointment.status)}`}>
              {appointment.status}
            </span>
            {appointment.is_overbook && (
              <span className="rounded-full bg-orange-100 px-2.5 py-1 text-xs font-extrabold text-orange-800">
                Sobrecupo
              </span>
            )}
          </div>
          <p className="mt-3 text-sm capitalize text-slate-600">
            {localDate(appointment.starts_at)}
          </p>
          <p className="mt-1 font-bold text-slate-800">
            {localTime(appointment.starts_at)}–{localTime(appointment.ends_at)}
          </p>
        </div>
        <dl className="grid gap-3 rounded-2xl bg-slate-50 p-4 text-sm sm:grid-cols-2">
          <div><dt className="text-slate-500">Tipo</dt><dd className="font-bold">{appointment.appointment_type_name}</dd></div>
          <div><dt className="text-slate-500">Sede</dt><dd className="font-bold">{appointment.site_name}</dd></div>
          <div><dt className="text-slate-500">Odontólogo</dt><dd className="font-bold">{appointment.dentist_name}</dd></div>
          <div><dt className="text-slate-500">Motivo</dt><dd className="font-bold">{appointment.reason}</dd></div>
        </dl>

        {!terminal && !action && (
          <div className="flex flex-wrap gap-2">
            {canUpdate && appointment.status === "Programada" && (
              <button onClick={() => setAction("confirm")} className="rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white">
                Confirmar
              </button>
            )}
            {canUpdate && (
              <button onClick={() => setAction("reschedule")} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-bold text-slate-700">
                Reprogramar
              </button>
            )}
            {canCancel && (
              <button onClick={() => setAction("cancel")} className="rounded-xl border border-red-200 px-4 py-2.5 text-sm font-bold text-red-700">
                Cancelar cita
              </button>
            )}
          </div>
        )}

        {action === "confirm" && (
          <ActionBox title="Confirmar cita">
            <FieldSelect
              label="Medio de confirmación"
              value={method}
              onChange={setMethod}
              options={["WhatsApp", "Llamada", "Presencial"].map((value) => ({ value, label: value }))}
            />
            <ActionButtons saving={saving} onBack={() => setAction(null)} onSave={() => run(false)} label="Confirmar" />
          </ActionBox>
        )}

        {action === "cancel" && (
          <ActionBox title="Cancelar cita">
            <label className="block">
              <span className="mb-2 block text-sm font-bold text-slate-700">Motivo de cancelación</span>
              <input value={reason} onChange={(event) => setReason(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3" />
            </label>
            <ActionButtons saving={saving} disabled={reason.trim().length < 2} onBack={() => setAction(null)} onSave={() => run(false)} label="Cancelar cita" danger />
          </ActionBox>
        )}

        {action === "reschedule" && (
          <ActionBox title="Nueva fecha y hora">
            <div className="grid gap-3 sm:grid-cols-2">
              <label>
                <span className="mb-2 block text-sm font-bold text-slate-700">Fecha</span>
                <input type="date" value={date} onChange={(event) => setDate(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3" />
              </label>
              <label>
                <span className="mb-2 block text-sm font-bold text-slate-700">Hora</span>
                <input type="time" step={900} value={time} onChange={(event) => setTime(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3" />
              </label>
              <FieldSelect label="Odontólogo" value={dentistId} onChange={setDentistId} options={options.dentists.map((item) => ({ value: item.id, label: item.name }))} />
              <FieldSelect label="Sede" value={siteId} onChange={setSiteId} options={options.sites.filter((site) => options.dentists.find((item) => item.id === dentistId)?.site_ids.includes(site.id)).map((item) => ({ value: item.id, label: item.name }))} />
            </div>
            <label className="block">
              <span className="mb-2 block text-sm font-bold text-slate-700">Motivo de reprogramación</span>
              <input value={reason} onChange={(event) => setReason(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3" />
            </label>
            {conflict?.can_overbook && canOverbook && (
              <label className="block">
                <span className="mb-2 block text-sm font-bold text-orange-800">Justificación del sobrecupo</span>
                <input value={overbookReason} onChange={(event) => setOverbookReason(event.target.value)} className="min-h-11 w-full rounded-xl border border-orange-300 px-3" />
              </label>
            )}
            <div className="flex flex-wrap justify-end gap-2">
              <button onClick={() => setAction(null)} className="rounded-xl border border-slate-300 px-4 py-2.5 font-bold text-slate-700">Volver</button>
              {conflict?.can_overbook && canOverbook && (
                <button disabled={!overbookReason.trim() || saving} onClick={() => run(true)} className="rounded-xl bg-orange-600 px-4 py-2.5 font-bold text-white disabled:opacity-50">Reprogramar como sobrecupo</button>
              )}
              <button disabled={reason.trim().length < 2 || saving} onClick={() => run(false)} className="rounded-xl bg-dentia-primary px-4 py-2.5 font-bold text-white disabled:opacity-50">Reprogramar</button>
            </div>
          </ActionBox>
        )}
      </div>
    </Modal>
  );
}

function FieldSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label>
      <span className="mb-2 block text-sm font-bold text-slate-700">{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3">
        <option value="">Selecciona</option>
        {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    </label>
  );
}

function ActionBox({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <h4 className="font-black text-slate-900">{title}</h4>
      {children}
    </div>
  );
}

function ActionButtons({
  saving,
  disabled,
  onBack,
  onSave,
  label,
  danger,
}: {
  saving: boolean;
  disabled?: boolean;
  onBack: () => void;
  onSave: () => void;
  label: string;
  danger?: boolean;
}) {
  return (
    <div className="flex justify-end gap-2">
      <button onClick={onBack} className="rounded-xl border border-slate-300 px-4 py-2.5 font-bold text-slate-700">Volver</button>
      <button disabled={saving || disabled} onClick={onSave} className={`rounded-xl px-4 py-2.5 font-bold text-white disabled:opacity-50 ${danger ? "bg-red-600" : "bg-dentia-primary"}`}>{label}</button>
    </div>
  );
}
