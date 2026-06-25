"use client";

import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import { useSearchParams } from "next/navigation";
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
  completeAppointment,
  confirmAppointment,
  createAppointment,
  createQuickPatient,
  generateAppointmentWhatsApp,
  getAgendaEvents,
  getAgendaOptions,
  rescheduleAppointment,
} from "@/services/agendaService";
import { ApiError } from "@/services/apiClient";
import { getPatient, searchPatients } from "@/services/patientService";
import type {
  AgendaOptions,
  Appointment,
  ConflictPayload,
  PatientOption,
} from "@/types/agenda";

const FALLBACK_TIMEZONE = "America/Bogota";
const TERMINAL_STATES = new Set([
  "Atendida",
  "Cancelada",
  "No Asistió",
  "Reprogramada",
]);

const EVENT_COLORS: Record<string, { background: string; border: string }> = {
  Programada: { background: "#0284c7", border: "#0369a1" },
  Confirmada: { background: "#16a34a", border: "#15803d" },
  Atendida: { background: "#7c3aed", border: "#6d28d9" },
  Cancelada: { background: "#dc2626", border: "#b91c1c" },
  Reprogramada: { background: "#f59e0b", border: "#d97706" },
  "No Asistió": { background: "#64748b", border: "#475569" },
};

type CalendarViewType = "timeGridDay" | "timeGridWeek" | "dayGridMonth";

function dateInTimeZone(date = new Date(), timeZone = FALLBACK_TIMEZONE) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

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

function zonedDateTimeToIso(
  date: string,
  time: string,
  timeZone = FALLBACK_TIMEZONE,
) {
  const [year, month, day] = date.split("-").map(Number);
  const [hour, minute] = time.split(":").map(Number);
  const utcGuess = new Date(Date.UTC(year, month - 1, day, hour, minute, 0));
  const firstOffset = getTimeZoneOffset(timeZone, utcGuess);
  const firstUtc = new Date(utcGuess.getTime() - firstOffset);
  const secondOffset = getTimeZoneOffset(timeZone, firstUtc);
  return new Date(utcGuess.getTime() - secondOffset).toISOString();
}

function addCalendarDays(date: string, days: number) {
  const [year, month, day] = date.split("-").map(Number);
  const value = new Date(Date.UTC(year, month - 1, day + days, 12, 0, 0));
  return value.toISOString().slice(0, 10);
}

function dayRange(date: string, timeZone = FALLBACK_TIMEZONE) {
  const start = zonedDateTimeToIso(date, "00:00", timeZone);
  return {
    start,
    end: zonedDateTimeToIso(addCalendarDays(date, 1), "00:00", timeZone),
  };
}

function calendarRange(start: string, end: string, timeZone = FALLBACK_TIMEZONE) {
  const startDate = start.slice(0, 10);
  const endDate = end.slice(0, 10);
  return {
    start: zonedDateTimeToIso(startDate, "00:00", timeZone),
    end: zonedDateTimeToIso(endDate, "00:00", timeZone),
  };
}

function wallClockFieldsFromCalendarBoundary(value: string) {
  const date = value.slice(0, 10);
  const time = value.includes("T")
    ? value.slice(11, 16)
    : "00:00";
  return { date, time };
}

function calendarBoundaryToIso(value: string, timeZone = FALLBACK_TIMEZONE) {
  const { date, time } = wallClockFieldsFromCalendarBoundary(value);
  return zonedDateTimeToIso(date, time, timeZone);
}

function isValidRange(range: { start: string; end: string }) {
  const start = Date.parse(range.start);
  const end = Date.parse(range.end);
  return Number.isFinite(start) && Number.isFinite(end) && end > start;
}

function addMinutes(
  date: string,
  time: string,
  minutes: number,
  timeZone = FALLBACK_TIMEZONE,
) {
  const value = new Date(zonedDateTimeToIso(date, time, timeZone));
  value.setUTCMinutes(value.getUTCMinutes() + minutes);
  return value.toISOString();
}

function dateTimeFieldsFromCalendar(value: string, fallbackTime = "08:00") {
  const date = value.slice(0, 10);
  const match = value.match(/T(\d{2}:\d{2})/);
  return { date, time: match?.[1] ?? fallbackTime };
}

function localTime(value: string, timeZone = FALLBACK_TIMEZONE) {
  return new Intl.DateTimeFormat("es-CO", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function localDate(value: string, timeZone = FALLBACK_TIMEZONE) {
  return new Intl.DateTimeFormat("es-CO", {
    timeZone,
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
  const searchParams = useSearchParams();
  const preselectedPatientId = searchParams.get("patient_id");
  const shouldOpenNewAppointment = searchParams.get("new") === "1";
  const { hasPermission, user } = useAuth();
  const [date, setDate] = useState(dateInTimeZone());
  const [calendarView, setCalendarView] =
    useState<CalendarViewType>("timeGridDay");
  const [visibleRange, setVisibleRange] = useState(() =>
    dayRange(dateInTimeZone()),
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
  const [preselectedPatient, setPreselectedPatient] =
    useState<PatientOption | null>(null);
  const activeTimeZone = useMemo(() => {
    const selectedSite = options?.sites.find((site) => site.id === siteId);
    return selectedSite?.timezone ?? options?.timezone ?? FALLBACK_TIMEZONE;
  }, [options, siteId]);

  const loadEvents = useCallback(async () => {
    const range = {
      start: visibleRange.start,
      end: visibleRange.end,
    };
    if (!isValidRange(range)) {
      setError("El rango de consulta no es válido.");
      setEvents([]);
      return;
    }
    try {
      setError(null);
      const items = await getAgendaEvents(
        range.start,
        range.end,
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
    Promise.all([
      getAgendaOptions(),
      preselectedPatientId ? getPatient(preselectedPatientId) : null,
    ])
      .then(([loaded, patient]) => {
        setOptions(loaded);
        setSiteId(loaded.active_site_id ?? "");
        if (loaded.dentists.length === 1) {
          setDentistId(loaded.dentists[0].id);
        }
        if (patient) {
          setPreselectedPatient({
            id: patient.id,
            full_name: patient.full_name,
            document_type: patient.document_type,
            document: patient.document,
            mobile: patient.mobile,
          });
          if (shouldOpenNewAppointment) {
            setNewOpen(true);
          }
        }
      })
      .catch(() => setError("No fue posible cargar las opciones de agenda."))
      .finally(() => setLoading(false));
  }, [preselectedPatientId, shouldOpenNewAppointment]);

  useEffect(() => {
    if (user?.active_site_id) {
      setSiteId(user.active_site_id);
    }
  }, [user?.active_site_id]);

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
        backgroundColor: appointment.is_overbook
          ? "#f97316"
          : EVENT_COLORS[appointment.status]?.background ?? "#334155",
        borderColor: appointment.is_overbook
          ? "#ea580c"
          : EVENT_COLORS[appointment.status]?.border ?? "#1e293b",
        textColor: "#ffffff",
        extendedProps: { appointment },
      })),
    [events],
  );

  function openAtTime(arg: DateClickArg) {
    if (!hasPermission("appointments.create")) return;
    const selected = dateTimeFieldsFromCalendar(arg.dateStr);
    setDate(selected.date);
    setNewStartTime(selected.time);
    setNewOpen(true);
  }

  function handleDatesSet(arg: DatesSetArg) {
    const range = {
      start: calendarBoundaryToIso(arg.startStr, activeTimeZone),
      end: calendarBoundaryToIso(arg.endStr, activeTimeZone),
    };
    setCalendarView(
      arg.view.type === "dayGridMonth"
        ? "dayGridMonth"
        : arg.view.type === "timeGridWeek"
          ? "timeGridWeek"
          : "timeGridDay",
    );
    setDate(dateInTimeZone(arg.view.calendar.getDate(), activeTimeZone));
    if (!isValidRange(range)) {
      setError("El rango de consulta no es válido.");
      return;
    }
    setVisibleRange((current) => {
      if (current.start === range.start && current.end === range.end) {
        return current;
      }
      return range;
    });
  }

  function changeView(view: CalendarViewType) {
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
    const showSite = siteId === "";
    return (
      <div className="overflow-hidden px-1 py-0.5 text-xs leading-tight">
        <div className="truncate font-bold">
          {showSite ? `[${appointment.site_name}] ` : ""}
          {appointment.patient_name}
        </div>
        <div className="mt-0.5 truncate opacity-90">
          {appointment.appointment_type_name}
          {!showSite && ` · ${appointment.site_name}`}
        </div>
        <span className="mt-1 inline-flex rounded bg-white/90 px-1.5 py-0.5 text-[10px] font-extrabold uppercase text-slate-800">
          {appointment.status}
        </span>
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
            Horario en {activeTimeZone} · intervalos de 15 minutos
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
              <button
                type="button"
                onClick={() => changeView("dayGridMonth")}
                aria-pressed={calendarView === "dayGridMonth"}
                className={`min-h-10 rounded-lg px-4 text-sm font-bold transition ${
                  calendarView === "dayGridMonth"
                    ? "bg-white text-green-800 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Mes
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
                plugins={[timeGridPlugin, dayGridPlugin, interactionPlugin]}
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
                timeZone={activeTimeZone}
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
          preselectedPatient={preselectedPatient}
          canOverbook={hasPermission("appointments.overbook")}
          timeZone={activeTimeZone}
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
          canComplete={hasPermission("appointments.complete")}
          timeZone={activeTimeZone}
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
  preselectedPatient,
  canOverbook,
  timeZone,
  onClose,
  onCreated,
}: {
  open: boolean;
  date: string;
  initialTime: string;
  options: AgendaOptions;
  defaultDentistId: string;
  defaultSiteId: string;
  preselectedPatient: PatientOption | null;
  canOverbook: boolean;
  timeZone: string;
  onClose: () => void;
  onCreated: () => Promise<void>;
}) {
  const [patientId, setPatientId] = useState(preselectedPatient?.id ?? "");
  const [patientSearch, setPatientSearch] = useState(
    preselectedPatient?.full_name ?? "",
  );
  const [patients, setPatients] = useState<PatientOption[]>(
    preselectedPatient ? [preselectedPatient] : [],
  );
  const [searchingPatients, setSearchingPatients] = useState(false);
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

  useEffect(() => {
    if (!open) return;
    setAppointmentDate(date);
    setTime(initialTime);
    setError(null);
    setConflict(null);
    setOverbookReason("");
    setDentistId(defaultDentistId || options.dentists[0]?.id || "");
    setSiteId(defaultSiteId || options.sites[0]?.id || "");
    if (preselectedPatient) {
      setPatientId(preselectedPatient.id);
      setPatientSearch(preselectedPatient.full_name);
      setPatients([preselectedPatient]);
    }
    if (!typeId && options.appointment_types[0]) {
      setTypeId(options.appointment_types[0].id);
      setDuration(options.appointment_types[0].suggested_duration_minutes);
    }
  }, [
    date,
    defaultDentistId,
    defaultSiteId,
    initialTime,
    open,
    options,
    preselectedPatient,
    typeId,
  ]);

  useEffect(() => {
    if (!open || patientSearch.trim().length < 2) return;
    const timeout = window.setTimeout(async () => {
      setSearchingPatients(true);
      try {
        const response = await searchPatients(patientSearch.trim());
        setPatients(
          response.items.map((patient) => ({
            id: patient.id,
            full_name: patient.full_name,
            document_type: patient.document_type,
            document: patient.document,
            mobile: patient.mobile,
          })),
        );
      } finally {
        setSearchingPatients(false);
      }
    }, 300);
    return () => window.clearTimeout(timeout);
  }, [open, patientSearch]);

  const availableDentists = options.dentists.filter(
    (dentist) => !siteId || dentist.site_ids.includes(siteId),
  );
  const selectedSiteTimezone =
    options.sites.find((site) => site.id === siteId)?.timezone ?? timeZone;

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
        starts_at: zonedDateTimeToIso(
          appointmentDate,
          time,
          selectedSiteTimezone,
        ),
        ends_at: addMinutes(
          appointmentDate,
          time,
          duration,
          selectedSiteTimezone,
        ),
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
                {localTime(item.starts_at, selectedSiteTimezone)}–
                {localTime(item.ends_at, selectedSiteTimezone)} ·{" "}
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
            <input
              value={patientSearch}
              onChange={(event) => {
                setPatientSearch(event.target.value);
                setPatientId("");
              }}
              placeholder="Busca por nombre, documento o celular"
              className="min-h-12 min-w-0 flex-1 rounded-xl border border-slate-300 px-3"
            />
            <button
              type="button"
              onClick={() => setQuickPatient((current) => !current)}
              className="rounded-xl border border-green-200 px-3 text-sm font-bold text-green-700"
            >
              + Nuevo
            </button>
          </div>
          {searchingPatients && (
            <p className="mt-2 text-xs text-slate-500">Buscando pacientes…</p>
          )}
          {!patientId && patients.length > 0 && (
            <div className="mt-2 max-h-44 overflow-y-auto rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
              {patients.map((patient) => (
                <button
                  key={patient.id}
                  type="button"
                  onClick={() => {
                    setPatientId(patient.id);
                    setPatientSearch(patient.full_name);
                  }}
                  className="block w-full rounded-lg px-3 py-2 text-left hover:bg-slate-50"
                >
                  <span className="block text-sm font-bold text-slate-800">
                    {patient.full_name}
                  </span>
                  <span className="text-xs text-slate-500">
                    {patient.document_type === "Sin documento"
                      ? "Sin documento"
                      : `${patient.document_type} ${patient.document ?? ""}`}{" "}
                    · {patient.mobile}
                  </span>
                </button>
              ))}
            </div>
          )}
          {patientId && (
            <p className="mt-2 text-xs font-bold text-green-700">
              Paciente seleccionado
            </p>
          )}
        </label>

        {quickPatient && (
          <QuickPatientForm
            onCreated={(patient) => {
              setPatients([patient]);
              setPatientId(patient.id);
              setPatientSearch(patient.full_name);
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
            }}
            options={availableDentists.map((item) => ({
              value: item.id,
              label: item.name,
            }))}
          />
          <FieldSelect
            label="Sede"
            value={siteId}
            onChange={(value) => {
              setSiteId(value);
              const dentist = options.dentists.find(
                (item) => item.id === dentistId,
              );
              if (dentist && !dentist.site_ids.includes(value)) {
                setDentistId("");
              }
            }}
            options={options.sites.map((item) => ({
              value: item.id,
              label: `${item.name} · ${item.address}`,
            }))}
          />
          {siteId && availableDentists.length === 0 && (
            <div className="rounded-xl bg-amber-50 p-3 text-sm font-bold text-amber-800 sm:col-span-2">
              No hay odontólogos asociados a esta sede.
            </div>
          )}
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
  const [documentType, setDocumentType] = useState("Otro");
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
          document_type: documentType,
          document: documentType === "Sin documento" ? null : document,
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
        <label>
          <span className="mb-1 block text-xs font-bold text-slate-600">
            Tipo de documento
          </span>
          <select
            value={documentType}
            onChange={(event) => setDocumentType(event.target.value)}
            className="min-h-10 w-full rounded-lg border border-slate-300 bg-white px-3"
          >
            {["CC", "TI", "RC", "CE", "Pasaporte", "Otro", "Sin documento"].map(
              (type) => <option key={type}>{type}</option>,
            )}
          </select>
        </label>
        <label>
          <span className="mb-1 block text-xs font-bold text-slate-600">
            Documento
          </span>
          <input
            value={document}
            disabled={documentType === "Sin documento"}
            onChange={(event) => setDocument(event.target.value)}
            className="min-h-10 w-full rounded-lg border border-slate-300 bg-white px-3 disabled:bg-slate-100"
          />
        </label>
        <label>
          <span className="mb-1 block text-xs font-bold text-slate-600">
            Celular
          </span>
          <input
            value={mobile}
            onChange={(event) => setMobile(event.target.value)}
            className="min-h-10 w-full rounded-lg border border-slate-300 bg-white px-3"
          />
        </label>
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
  canComplete,
  timeZone,
  onClose,
  onChanged,
}: {
  appointment: Appointment;
  options: AgendaOptions;
  canUpdate: boolean;
  canCancel: boolean;
  canOverbook: boolean;
  canComplete: boolean;
  timeZone: string;
  onClose: () => void;
  onChanged: (appointment: Appointment) => Promise<void>;
}) {
  const [action, setAction] = useState<"confirm" | "cancel" | "reschedule" | "complete" | null>(null);
  const [method, setMethod] = useState("WhatsApp");
  const [reason, setReason] = useState("");
  const appointmentTimeZone =
    options.sites.find((site) => site.id === appointment.site_id)?.timezone ??
    timeZone;
  const [date, setDate] = useState(
    dateInTimeZone(new Date(appointment.starts_at), appointmentTimeZone),
  );
  const [time, setTime] = useState(
    localTime(appointment.starts_at, appointmentTimeZone),
  );
  const [siteId, setSiteId] = useState(appointment.site_id);
  const [dentistId, setDentistId] = useState(appointment.dentist_id);
  const [saving, setSaving] = useState(false);
  const [whatsappBusy, setWhatsappBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [conflict, setConflict] = useState<ConflictPayload | null>(null);
  const [overbookReason, setOverbookReason] = useState("");
  const [attentionDescription, setAttentionDescription] = useState("");
  const [medications, setMedications] = useState("");
  const [requiresFollowup, setRequiresFollowup] = useState(false);
  const [followupDate, setFollowupDate] = useState("");
  const [followupReason, setFollowupReason] = useState("");
  const duration = Math.round(
    (new Date(appointment.ends_at).getTime() -
      new Date(appointment.starts_at).getTime()) /
      60000,
  );
  const terminal = TERMINAL_STATES.has(appointment.status);
  const rescheduleTimeZone =
    options.sites.find((site) => site.id === siteId)?.timezone ??
    appointmentTimeZone;
  const availableDentists = options.dentists.filter(
    (dentist) => !siteId || dentist.site_ids.includes(siteId),
  );

  async function run(isOverbook = false) {
    setSaving(true);
    setError(null);
    setInfo(null);
    setConflict(null);
    try {
      let updated: Appointment;
      if (action === "confirm") {
        updated = await confirmAppointment(appointment.id, method);
      } else if (action === "cancel") {
        updated = await cancelAppointment(appointment.id, reason);
      } else if (action === "complete") {
        const completed = await completeAppointment(appointment.id, {
          attention_description: attentionDescription,
          prescribed_medications: medications.trim() || null,
          requires_followup: requiresFollowup,
          recommended_followup_date: requiresFollowup ? followupDate : null,
          followup_reason: requiresFollowup ? followupReason : null,
        });
        updated = { ...appointment, status: completed.appointment_status };
      } else {
        updated = await rescheduleAppointment(appointment.id, {
          site_id: siteId,
          dentist_id: dentistId,
          starts_at: zonedDateTimeToIso(date, time, rescheduleTimeZone),
          ends_at: addMinutes(date, time, duration, rescheduleTimeZone),
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

  async function sendConfirmationWhatsApp() {
    setWhatsappBusy(true);
    setError(null);
    setInfo(null);
    try {
      const response = await generateAppointmentWhatsApp(appointment.id);
      window.open(response.url, "_blank", "noopener,noreferrer");
      setInfo(
        "Enlace de WhatsApp generado. La cita conserva su estado hasta que confirmes manualmente en Dentia.",
      );
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.detail ?? caught.message
          : "No fue posible generar WhatsApp.",
      );
    } finally {
      setWhatsappBusy(false);
    }
  }

  return (
    <Modal open title="Detalle de la cita" onClose={onClose}>
      <div className="space-y-5">
        {error && <Alert tone="error">{error}</Alert>}
        {info && <Alert tone="info">{info}</Alert>}
        {conflict && (
          <Alert tone="warning">
            <strong>{conflict.message}</strong>
            {conflict.conflicts.map((item) => (
              <p key={item.id} className="mt-1 text-xs">
                {localTime(item.starts_at, appointmentTimeZone)} · {item.patient_name}
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
            {localDate(appointment.starts_at, appointmentTimeZone)}
          </p>
          <p className="mt-1 font-bold text-slate-800">
            {localTime(appointment.starts_at, appointmentTimeZone)}–
            {localTime(appointment.ends_at, appointmentTimeZone)}
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
              <>
                <button
                  disabled={whatsappBusy}
                  onClick={sendConfirmationWhatsApp}
                  className="rounded-xl bg-green-600 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-60"
                >
                  {whatsappBusy ? "Generando…" : "Enviar WhatsApp de confirmación"}
                </button>
                <button onClick={() => setAction("confirm")} className="rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white">
                  Confirmar cita
                </button>
              </>
            )}
            {canUpdate && (
              <button onClick={() => setAction("reschedule")} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-bold text-slate-700">
                Reprogramar
              </button>
            )}
            {canComplete && (
              <button onClick={() => setAction("complete")} className="rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-bold text-white">
                Finalizar atención
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
              <FieldSelect label="Sede" value={siteId} onChange={(value) => {
                setSiteId(value);
                const dentist = options.dentists.find((item) => item.id === dentistId);
                if (dentist && !dentist.site_ids.includes(value)) setDentistId("");
              }} options={options.sites.map((item) => ({ value: item.id, label: `${item.name} · ${item.address}` }))} />
              <FieldSelect label="Odontólogo" value={dentistId} onChange={setDentistId} options={availableDentists.map((item) => ({ value: item.id, label: item.name }))} />
              {siteId && availableDentists.length === 0 && (
                <div className="rounded-xl bg-amber-50 p-3 text-sm font-bold text-amber-800 sm:col-span-2">
                  No hay odontólogos asociados a esta sede.
                </div>
              )}
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

        {action === "complete" && (
          <ActionBox title="Finalizar atención">
            <Alert tone="warning">
              Este registro no reemplaza la historia clínica ni una fórmula médica formal.
            </Alert>
            <label className="block">
              <span className="mb-2 block text-sm font-bold text-slate-700">Descripción de la atención</span>
              <textarea value={attentionDescription} onChange={(event) => setAttentionDescription(event.target.value)} rows={4} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-bold text-slate-700">Medicamentos formulados (informativo)</span>
              <textarea value={medications} onChange={(event) => setMedications(event.target.value)} rows={3} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
            </label>
            <label className="flex items-center gap-3 text-sm font-bold text-slate-700">
              <input type="checkbox" checked={requiresFollowup} onChange={(event) => setRequiresFollowup(event.target.checked)} className="h-4 w-4 accent-green-600" />
              Requiere próximo control
            </label>
            {requiresFollowup && (
              <div className="grid gap-3">
                <label>
                  <span className="mb-2 block text-sm font-bold text-slate-700">Fecha recomendada</span>
                  <input type="date" value={followupDate} onChange={(event) => setFollowupDate(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3" />
                </label>
                <label>
                  <span className="mb-2 block text-sm font-bold text-slate-700">Motivo del próximo control</span>
                  <input value={followupReason} onChange={(event) => setFollowupReason(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3" />
                </label>
              </div>
            )}
            <ActionButtons
              saving={saving}
              disabled={
                attentionDescription.trim().length < 2 ||
                (requiresFollowup && (!followupDate || followupReason.trim().length < 2))
              }
              onBack={() => setAction(null)}
              onSave={() => run(false)}
              label="Finalizar atención"
            />
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
