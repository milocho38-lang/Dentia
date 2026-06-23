"use client";

import { FormEvent, useMemo, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { ApiError } from "@/services/apiClient";
import type {
  DuplicateErrorPayload,
  Patient,
  PatientInput,
  ResponsibleInput,
} from "@/types/patient";

const DOCUMENT_TYPES = [
  "CC",
  "TI",
  "RC",
  "CE",
  "Pasaporte",
  "Otro",
  "Sin documento",
];

const EMPTY_RESPONSIBLE: ResponsibleInput = {
  name: "",
  document_type: "CC",
  document: "",
  relationship: "",
  mobile: "",
  email: "",
  is_primary: true,
};

function patientIsMinor(birthDate: string) {
  if (!birthDate) return false;
  const birth = new Date(`${birthDate}T12:00:00`);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  if (
    today.getMonth() < birth.getMonth() ||
    (today.getMonth() === birth.getMonth() &&
      today.getDate() < birth.getDate())
  ) {
    age -= 1;
  }
  return age < 18;
}

function duplicatePayload(error: unknown) {
  if (!(error instanceof ApiError) || error.status !== 409) return null;
  const payload = error.payload;
  if (
    payload &&
    typeof payload === "object" &&
    "duplicates" in payload &&
    "message" in payload
  ) {
    return payload as DuplicateErrorPayload;
  }
  return null;
}

export function PatientForm({
  patient,
  submitLabel,
  onSubmit,
}: {
  patient?: Patient;
  submitLabel: string;
  onSubmit: (data: PatientInput) => Promise<void>;
}) {
  const editing = Boolean(patient);
  const [firstNames, setFirstNames] = useState(patient?.first_names ?? "");
  const [lastNames, setLastNames] = useState(patient?.last_names ?? "");
  const [documentType, setDocumentType] = useState(
    patient?.document_type ?? "CC",
  );
  const [document, setDocument] = useState(patient?.document ?? "");
  const [mobile, setMobile] = useState(patient?.mobile ?? "");
  const [birthDate, setBirthDate] = useState(patient?.birth_date ?? "");
  const [sex, setSex] = useState(patient?.sex ?? "");
  const [email, setEmail] = useState(patient?.email ?? "");
  const [alternatePhone, setAlternatePhone] = useState(
    patient?.alternate_phone ?? "",
  );
  const [address, setAddress] = useState(patient?.address ?? "");
  const [city, setCity] = useState(patient?.city ?? "");
  const [department, setDepartment] = useState(patient?.department ?? "");
  const [emergencyName, setEmergencyName] = useState(
    patient?.emergency_contact_name ?? "",
  );
  const [emergencyMobile, setEmergencyMobile] = useState(
    patient?.emergency_contact_mobile ?? "",
  );
  const [notes, setNotes] = useState(
    patient?.administrative_notes ?? "",
  );
  const [includeResponsible, setIncludeResponsible] = useState(false);
  const [responsible, setResponsible] = useState<ResponsibleInput>({
    ...EMPTY_RESPONSIBLE,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicateWarning, setDuplicateWarning] =
    useState<DuplicateErrorPayload | null>(null);

  const minor = useMemo(() => patientIsMinor(birthDate), [birthDate]);
  const showResponsible = !editing && (minor || includeResponsible);

  function buildPayload(acknowledge = false): PatientInput {
    return {
      first_names: firstNames.trim(),
      last_names: lastNames.trim(),
      document_type: documentType,
      document:
        documentType === "Sin documento" ? null : document.trim() || null,
      mobile: mobile.trim(),
      birth_date: birthDate,
      sex: sex || null,
      email: email.trim() || null,
      alternate_phone: alternatePhone.trim() || null,
      address: address.trim() || null,
      city: city.trim() || null,
      department: department.trim() || null,
      emergency_contact_name: emergencyName.trim() || null,
      emergency_contact_mobile: emergencyMobile.trim() || null,
      administrative_notes: notes.trim() || null,
      acknowledge_duplicate_warning: acknowledge,
      responsibles: showResponsible
        ? [
            {
              ...responsible,
              name: responsible.name.trim(),
              document:
                responsible.document_type === "Sin documento"
                  ? null
                  : responsible.document?.trim() || null,
              relationship: responsible.relationship.trim(),
              mobile: responsible.mobile.trim(),
              email: responsible.email?.trim() || null,
              is_primary: true,
            },
          ]
        : [],
    };
  }

  async function save(acknowledge = false) {
    setError(null);
    setDuplicateWarning(null);
    if (
      !firstNames.trim() ||
      !lastNames.trim() ||
      !mobile.trim() ||
      !birthDate
    ) {
      setError("Completa nombres, apellidos, celular y fecha de nacimiento.");
      return;
    }
    if (documentType !== "Sin documento" && !document.trim()) {
      setError("Ingresa el documento o selecciona Sin documento.");
      return;
    }
    if (
      showResponsible &&
      (!responsible.name.trim() ||
        !responsible.relationship.trim() ||
        !responsible.mobile.trim())
    ) {
      setError("Completa los datos obligatorios del responsable principal.");
      return;
    }
    setSaving(true);
    try {
      await onSubmit(buildPayload(acknowledge));
    } catch (submitError) {
      const duplicate = duplicatePayload(submitError);
      if (duplicate) {
        setDuplicateWarning(duplicate);
      } else {
        setError(
          submitError instanceof ApiError
            ? submitError.detail ?? submitError.message
            : "No fue posible guardar el paciente.",
        );
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      className="space-y-6"
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        save(false);
      }}
    >
      {error && <Alert tone="error">{error}</Alert>}
      {duplicateWarning && (
        <Alert tone="warning">
          <p className="font-bold">{duplicateWarning.message}</p>
          {[...duplicateWarning.duplicates.exact, ...duplicateWarning.duplicates.approximate].map(
            (candidate) => (
              <p key={candidate.id} className="mt-2 text-sm">
                {candidate.full_name} · {candidate.document_type}{" "}
                {candidate.document ?? ""} · {candidate.reasons.join(", ")}
              </p>
            ),
          )}
          {!duplicateWarning.duplicates.exact.length && (
            <button
              type="button"
              onClick={() => save(true)}
              className="mt-3 rounded-lg bg-amber-700 px-4 py-2 text-sm font-bold text-white"
            >
              Confirmar y continuar
            </button>
          )}
        </Alert>
      )}

      <FormSection title="Identificación">
        <div className="grid gap-5 sm:grid-cols-2">
          <TextField label="Nombres" value={firstNames} onChange={setFirstNames} />
          <TextField label="Apellidos" value={lastNames} onChange={setLastNames} />
          <SelectField
            label="Tipo de documento"
            value={documentType}
            onChange={(value) => {
              setDocumentType(value);
              if (value === "Sin documento") setDocument("");
            }}
            options={DOCUMENT_TYPES}
          />
          <TextField
            label="Documento"
            value={document}
            onChange={setDocument}
            disabled={documentType === "Sin documento"}
          />
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">
              Fecha de nacimiento
            </span>
            <input
              type="date"
              value={birthDate}
              onChange={(event) => setBirthDate(event.target.value)}
              className="min-h-12 w-full rounded-xl border border-slate-300 px-4"
            />
          </label>
          <SelectField
            label="Sexo (opcional)"
            value={sex}
            onChange={setSex}
            options={["", "femenino", "masculino", "otro", "no informa"]}
            emptyLabel="No registrado"
          />
        </div>
      </FormSection>

      <FormSection title="Contacto">
        <div className="grid gap-5 sm:grid-cols-2">
          <TextField label="Celular" value={mobile} onChange={setMobile} />
          <TextField
            label="Teléfono alternativo"
            value={alternatePhone}
            onChange={setAlternatePhone}
          />
          <TextField label="Correo" value={email} onChange={setEmail} type="email" />
          <TextField label="Ciudad" value={city} onChange={setCity} />
          <TextField
            label="Departamento"
            value={department}
            onChange={setDepartment}
          />
          <TextField label="Dirección" value={address} onChange={setAddress} />
        </div>
      </FormSection>

      <FormSection title="Contacto de emergencia">
        <div className="grid gap-5 sm:grid-cols-2">
          <TextField
            label="Nombre"
            value={emergencyName}
            onChange={setEmergencyName}
          />
          <TextField
            label="Celular"
            value={emergencyMobile}
            onChange={setEmergencyMobile}
          />
        </div>
      </FormSection>

      {!editing && (
        <FormSection title="Responsable o acudiente">
          {!minor && (
            <label className="flex items-center gap-3 text-sm font-bold text-slate-700">
              <input
                type="checkbox"
                checked={includeResponsible}
                onChange={(event) => setIncludeResponsible(event.target.checked)}
                className="h-4 w-4 accent-green-600"
              />
              Registrar responsable para adulto dependiente
            </label>
          )}
          {minor && (
            <Alert tone="warning">
              El paciente es menor de edad y requiere un responsable principal.
            </Alert>
          )}
          {showResponsible && (
            <div className="mt-5 grid gap-5 sm:grid-cols-2">
              <TextField
                label="Nombre completo"
                value={responsible.name}
                onChange={(value) =>
                  setResponsible((current) => ({ ...current, name: value }))
                }
              />
              <TextField
                label="Parentesco"
                value={responsible.relationship}
                onChange={(value) =>
                  setResponsible((current) => ({
                    ...current,
                    relationship: value,
                  }))
                }
              />
              <SelectField
                label="Tipo de documento"
                value={responsible.document_type}
                onChange={(value) =>
                  setResponsible((current) => ({
                    ...current,
                    document_type: value,
                    document:
                      value === "Sin documento" ? null : current.document,
                  }))
                }
                options={DOCUMENT_TYPES}
              />
              <TextField
                label="Documento"
                value={responsible.document ?? ""}
                disabled={responsible.document_type === "Sin documento"}
                onChange={(value) =>
                  setResponsible((current) => ({
                    ...current,
                    document: value,
                  }))
                }
              />
              <TextField
                label="Celular"
                value={responsible.mobile}
                onChange={(value) =>
                  setResponsible((current) => ({ ...current, mobile: value }))
                }
              />
              <TextField
                label="Correo"
                type="email"
                value={responsible.email ?? ""}
                onChange={(value) =>
                  setResponsible((current) => ({ ...current, email: value }))
                }
              />
            </div>
          )}
        </FormSection>
      )}

      <FormSection title="Observaciones administrativas">
        <p className="mb-3 text-xs text-slate-500">
          No registres antecedentes, diagnósticos ni información clínica.
        </p>
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={4}
          maxLength={3000}
          className="w-full rounded-xl border border-slate-300 px-4 py-3"
        />
      </FormSection>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={saving}
          className="flex min-h-12 items-center gap-2 rounded-xl bg-dentia-primary px-6 font-bold text-white disabled:opacity-60"
        >
          {saving && <Spinner className="h-5 w-5" />}
          {submitLabel}
        </button>
      </div>
    </form>
  );
}

function FormSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-bold text-slate-900">{title}</h2>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function TextField({
  label,
  value,
  onChange,
  type = "text",
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  disabled?: boolean;
}) {
  return (
    <label>
      <span className="mb-2 block text-sm font-bold text-slate-700">{label}</span>
      <input
        type={type}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-12 w-full rounded-xl border border-slate-300 px-4 disabled:bg-slate-100"
      />
    </label>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  emptyLabel,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  emptyLabel?: string;
}) {
  return (
    <label>
      <span className="mb-2 block text-sm font-bold text-slate-700">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4"
      >
        {options.map((option) => (
          <option key={option || "empty"} value={option}>
            {option || emptyLabel}
          </option>
        ))}
      </select>
    </label>
  );
}
