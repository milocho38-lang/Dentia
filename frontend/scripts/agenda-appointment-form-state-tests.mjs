import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  applyAppointmentType,
  initializeAppointmentSchedule,
} from "../lib/appointmentFormState.ts";

const initialType = { id: "initial", suggested_duration_minutes: 30 };
const secondType = { id: "second", suggested_duration_minutes: 45 };
const thirdType = { id: "third", suggested_duration_minutes: 60 };

let createSchedule = initializeAppointmentSchedule(
  { appointmentDate: "", time: "", typeId: "", duration: 30 },
  "2026-09-30",
  "07:15",
  initialType,
);
createSchedule = {
  ...createSchedule,
  appointmentDate: "2026-10-02",
  time: "10:30",
};
createSchedule = applyAppointmentType(createSchedule, secondType);

assert.equal(createSchedule.appointmentDate, "2026-10-02");
assert.equal(createSchedule.time, "10:30");
assert.equal(createSchedule.typeId, "second");
assert.equal(createSchedule.duration, 45);

createSchedule = applyAppointmentType(createSchedule, thirdType);
assert.equal(createSchedule.appointmentDate, "2026-10-02");
assert.equal(createSchedule.time, "10:30");
assert.equal(createSchedule.typeId, "third");
assert.equal(createSchedule.duration, 60);

const existingAppointmentSchedule = applyAppointmentType(
  {
    appointmentDate: "2026-10-04",
    time: "14:45",
    typeId: "initial",
    duration: 30,
  },
  secondType,
);
assert.equal(existingAppointmentSchedule.appointmentDate, "2026-10-04");
assert.equal(existingAppointmentSchedule.time, "14:45");
assert.equal(existingAppointmentSchedule.duration, 45);

const agendaView = readFileSync(
  new URL("../components/agenda/AgendaView.tsx", import.meta.url),
  "utf8",
);
const appointmentFormStart = agendaView.indexOf("function AppointmentForm(");
const appointmentFormEnd = agendaView.indexOf("function QuickPatientForm(");
const appointmentForm = agendaView.slice(appointmentFormStart, appointmentFormEnd);
const initializationEffectStart = appointmentForm.indexOf("useEffect(() => {");
const patientSearchEffectStart = appointmentForm.indexOf(
  "useEffect(() => {",
  initializationEffectStart + 1,
);
const initializationEffect = appointmentForm.slice(
  initializationEffectStart,
  patientSearchEffectStart,
);

assert.match(appointmentForm, /const modalWasOpen = useRef\(false\)/);
assert.match(appointmentForm, /if \(modalWasOpen\.current\) return/);
assert.match(appointmentForm, /applyAppointmentType\(current, type\)/);
assert.doesNotMatch(
  initializationEffect,
  /typeId/,
  "appointment type must not retrigger slot initialization",
);

console.log("agenda-appointment-form-state-tests OK");
