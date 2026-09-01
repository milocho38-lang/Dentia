"use client";

import { useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import {
  deleteDentistProfessionalSignature,
  fetchDentistProfessionalSignature,
  listDentists,
  uploadDentistProfessionalSignature,
  updateDentistProfessionalProfile,
  updateDentistSites,
} from "@/services/organizationService";
import type {
  DentistProfessionalProfileInput,
  DentistSiteManagement,
} from "@/types/organization";

export function DentistSiteManagementPage() {
  const { hasPermission } = useAuth();
  const canEdit = hasPermission("sites.manage");
  const [items, setItems] = useState<DentistSiteManagement[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [profiles, setProfiles] = useState<Record<string, DentistProfessionalProfileInput>>({});
  const [signatureRevision, setSignatureRevision] = useState<Record<string, number>>({});

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const response = await listDentists();
      setItems(response.items);
      setProfiles(Object.fromEntries(response.items.map((dentist) => [dentist.id, {
        name: dentist.name,
        document_type: dentist.document_type,
        document_number: dentist.document_number,
        specialty: dentist.specialty,
        professional_license: dentist.professional_license,
      }])));
    } catch {
      setError("No fue posible cargar los odontólogos.");
    } finally {
      setLoading(false);
    }
  }

  function updateProfileField(
    dentist: DentistSiteManagement,
    field: keyof DentistProfessionalProfileInput,
    value: string,
  ) {
    setProfiles((current) => ({
      ...current,
      [dentist.id]: {
        ...(current[dentist.id] ?? {
          name: dentist.name,
          document_type: dentist.document_type,
          document_number: dentist.document_number,
          specialty: dentist.specialty,
          professional_license: dentist.professional_license,
        }),
        [field]: field === "name" ? value : value || null,
      },
    }));
  }

  async function saveProfessionalProfile(dentist: DentistSiteManagement) {
    if (!canEdit || !profiles[dentist.id]) return;
    setSavingId(dentist.id);
    setError(null);
    setMessage(null);
    try {
      const updated = await updateDentistProfessionalProfile(
        dentist.id,
        profiles[dentist.id],
      );
      setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
      setProfiles((current) => ({ ...current, [updated.id]: {
        name: updated.name,
        document_type: updated.document_type,
        document_number: updated.document_number,
        specialty: updated.specialty,
        professional_license: updated.professional_license,
      } }));
      setMessage("Identidad profesional actualizada.");
    } catch {
      setError("No fue posible actualizar la identidad profesional.");
    } finally {
      setSavingId(null);
    }
  }

  async function uploadProfessionalSignature(
    dentist: DentistSiteManagement,
    file: File | undefined,
  ) {
    if (!canEdit || !file) return;
    setSavingId(dentist.id);
    setError(null);
    setMessage(null);
    try {
      const updated = await uploadDentistProfessionalSignature(dentist.id, file);
      setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
      setSignatureRevision((current) => ({ ...current, [dentist.id]: (current[dentist.id] ?? 0) + 1 }));
      setMessage("Firma profesional actualizada.");
    } catch {
      setError("No fue posible cargar la firma profesional. Usa PNG o JPEG de máximo 5 MB.");
    } finally {
      setSavingId(null);
    }
  }

  async function removeProfessionalSignature(dentist: DentistSiteManagement) {
    if (!canEdit) return;
    setSavingId(dentist.id);
    setError(null);
    setMessage(null);
    try {
      const updated = await deleteDentistProfessionalSignature(dentist.id);
      setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
      setSignatureRevision((current) => ({ ...current, [dentist.id]: (current[dentist.id] ?? 0) + 1 }));
      setMessage("Firma profesional eliminada.");
    } catch {
      setError("No fue posible eliminar la firma profesional.");
    } finally {
      setSavingId(null);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function toggleSite(dentist: DentistSiteManagement, siteId: string) {
    if (!canEdit) return;
    setSavingId(dentist.id);
    setError(null);
    setMessage(null);
    const nextIds = dentist.site_ids.includes(siteId)
      ? dentist.site_ids.filter((id) => id !== siteId)
      : [...dentist.site_ids, siteId];
    try {
      const updated = await updateDentistSites(dentist.id, nextIds);
      setItems((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setMessage("Asociación de sedes actualizada.");
    } catch {
      setError("No fue posible actualizar las sedes del odontólogo.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
          Configuración
        </p>
        <h1 className="mt-2 text-3xl font-black text-slate-950">
          Odontólogos y sedes
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Asociación operativa mínima para que un odontólogo pueda atender en
          varias sedes.
        </p>
      </header>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
      {message && <div className="mt-5"><Alert tone="info">{message}</Alert></div>}

      <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex justify-center gap-3 py-16 text-slate-500">
            <Spinner className="h-6 w-6 text-dentia-primary" />
            Cargando odontólogos…
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {items.map((dentist) => (
              <article key={dentist.id} id={`dentist-${dentist.id}`} className="scroll-mt-24 p-5 target:bg-green-50">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-black text-slate-900">
                      {dentist.name}
                    </h2>
                    <p className="mt-1 text-xs font-bold uppercase text-green-700">
                      {dentist.status}
                    </p>
                  </div>
                  {savingId === dentist.id && (
                    <span className="inline-flex items-center gap-2 text-sm text-slate-500">
                      <Spinner className="h-4 w-4" />
                      Guardando…
                    </span>
                  )}
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {dentist.sites.map((site) => (
                    <label
                      key={site.id}
                      className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 hover:bg-slate-50"
                    >
                      <input
                        type="checkbox"
                        checked={dentist.site_ids.includes(site.id)}
                        disabled={!canEdit || savingId === dentist.id}
                        onChange={() => toggleSite(dentist, site.id)}
                        className="mt-1 h-4 w-4 accent-green-700"
                      />
                      <span>
                        <span className="block font-bold text-slate-900">
                          {site.name}
                        </span>
                        <span className="block text-xs text-slate-500">
                          {site.address} · {site.timezone}
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
                <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <h3 className="font-black text-slate-900">Identidad para documentos clínicos</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    El correo proviene del usuario vinculado. La firma es propia de este perfil y nunca se comparte automáticamente con otro odontólogo.
                  </p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <label className="text-sm font-bold text-slate-700">
                      Nombre profesional
                      <input
                        value={profiles[dentist.id]?.name ?? ""}
                        disabled={!canEdit || savingId === dentist.id}
                        onChange={(event) => updateProfileField(dentist, "name", event.target.value)}
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal"
                      />
                    </label>
                    <label className="text-sm font-bold text-slate-700">
                      Tipo de documento
                      <select
                        value={profiles[dentist.id]?.document_type ?? ""}
                        disabled={!canEdit || savingId === dentist.id}
                        onChange={(event) => updateProfileField(dentist, "document_type", event.target.value)}
                        className="mt-1 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal"
                      >
                        <option value="">Seleccionar</option>
                        <option value="CC">Cédula de ciudadanía</option>
                        <option value="CE">Cédula de extranjería</option>
                        <option value="PASAPORTE">Pasaporte</option>
                        <option value="RUN">RUN</option>
                        <option value="RUT">RUT</option>
                        <option value="DNI">Documento nacional de identidad</option>
                        <option value="OTRO">Otro documento</option>
                      </select>
                    </label>
                    {(["document_number", "specialty", "professional_license"] as const).map((field) => (
                      <label key={field} className="text-sm font-bold text-slate-700">
                        {{
                          document_number: "Número de documento",
                          specialty: "Especialidad o rol clínico",
                          professional_license: "Registro profesional",
                        }[field]}
                        <input
                          value={profiles[dentist.id]?.[field] ?? ""}
                          disabled={!canEdit || savingId === dentist.id}
                          onChange={(event) => updateProfileField(dentist, field, event.target.value)}
                          className="mt-1 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal"
                        />
                      </label>
                    ))}
                  </div>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600">
                    <span><strong>Correo vinculado:</strong> {dentist.professional_email ?? "Usuario sin correo profesional vinculado"}</span>
                    <span>{dentist.has_professional_signature ? "Firma gráfica disponible" : "Firma gráfica pendiente"}</span>
                  </div>
                  <ProfessionalSignaturePreview
                    dentistId={dentist.id}
                    available={dentist.has_professional_signature}
                    revision={signatureRevision[dentist.id] ?? 0}
                  />
                  {canEdit && (
                    <div className="mt-4 flex flex-wrap gap-3">
                      <button
                        type="button"
                        disabled={savingId === dentist.id}
                        onClick={() => saveProfessionalProfile(dentist)}
                        className="min-h-11 rounded-xl bg-green-700 px-4 text-sm font-black text-white disabled:opacity-50"
                      >
                        Guardar identidad profesional
                      </button>
                      <label className="inline-flex min-h-11 cursor-pointer items-center rounded-xl border border-slate-300 bg-white px-4 text-sm font-black text-slate-700 hover:bg-slate-100">
                        {dentist.has_professional_signature ? "Reemplazar firma" : "Cargar firma"}
                        <input
                          type="file"
                          accept="image/png,image/jpeg"
                          disabled={savingId === dentist.id}
                          onChange={(event) => {
                            void uploadProfessionalSignature(dentist, event.target.files?.[0]);
                            event.currentTarget.value = "";
                          }}
                          className="sr-only"
                        />
                      </label>
                      {dentist.has_professional_signature && (
                        <button
                          type="button"
                          disabled={savingId === dentist.id}
                          onClick={() => removeProfessionalSignature(dentist)}
                          className="min-h-11 rounded-xl border border-red-200 bg-white px-4 text-sm font-black text-red-700 hover:bg-red-50 disabled:opacity-50"
                        >
                          Eliminar firma
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </article>
            ))}
            {!items.length && (
              <p className="py-14 text-center text-sm text-slate-500">
                No hay odontólogos activos para configurar.
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

function ProfessionalSignaturePreview({
  dentistId,
  available,
  revision,
}: {
  dentistId: string;
  available: boolean;
  revision: number;
}) {
  const [source, setSource] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    if (!available) {
      setSource(null);
      return () => { active = false; };
    }
    void fetchDentistProfessionalSignature(dentistId)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        if (active) setSource(objectUrl);
      })
      .catch(() => {
        if (active) setSource(null);
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [available, dentistId, revision]);

  if (!source) return null;
  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3">
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Firma profesional actual</p>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={source} alt="Firma profesional configurada" className="mt-2 max-h-24 max-w-full object-contain object-left" />
    </div>
  );
}
