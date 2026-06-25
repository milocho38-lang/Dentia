"use client";

import { FormEvent, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { getCompany, updateCompany } from "@/services/organizationService";
import type { Company, CompanyInput } from "@/types/organization";

const empty: CompanyInput = {
  name: "",
  company_type: null,
  tax_id: null,
  phone: null,
  email: null,
  address: null,
  city: null,
  country: "Colombia",
  timezone: "America/Bogota",
};

export function CompanySettingsPage() {
  const { hasPermission } = useAuth();
  const [company, setCompany] = useState<Company | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCompany()
      .then(setCompany)
      .catch(() => setError("No fue posible cargar la empresa."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-20"><Spinner className="h-7 w-7 text-green-700" /></div>;
  if (!company) return <Alert tone="error">{error ?? "Empresa no disponible."}</Alert>;

  return (
    <div className="mx-auto max-w-5xl">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">Configuración</p>
        <h1 className="mt-2 text-3xl font-black">Empresa</h1>
        <p className="mt-2 text-sm text-slate-500">Identidad, contacto y zona horaria de la organización.</p>
      </header>
      {!company.profile_complete && <div className="mt-5"><Alert tone="warning">El perfil empresarial aún tiene información pendiente.</Alert></div>}
      <CompanyForm company={company} canEdit={hasPermission("company.update")} onSaved={setCompany} />
    </div>
  );
}

export function CompanyForm({ company, canEdit, onSaved }: { company: Company; canEdit: boolean; onSaved: (company: Company) => void }) {
  const [data, setData] = useState<CompanyInput>({ ...empty, name: company.name, company_type: company.company_type, tax_id: company.tax_id, phone: company.phone, email: company.email, address: company.address, city: company.city, country: company.country, timezone: company.timezone });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage(null);
    try {
      const saved = await updateCompany(data);
      onSaved(saved); setMessage("Empresa actualizada correctamente.");
    } catch { setMessage("No fue posible guardar la empresa."); }
    finally { setBusy(false); }
  }

  const field = (key: keyof CompanyInput, label: string, type = "text") => <label><span className="mb-1 block text-sm font-bold">{label}</span><input type={type} disabled={!canEdit} value={data[key] ?? ""} onChange={(e) => setData((current) => ({ ...current, [key]: e.target.value || null }))} className="min-h-11 w-full rounded-xl border border-slate-300 px-3 disabled:bg-slate-50" /></label>;
  return <form onSubmit={submit} className="mt-6 space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
    {message && <Alert tone={message.startsWith("Empresa") ? "info" : "error"}>{message}</Alert>}
    <div className="grid gap-4 sm:grid-cols-2">{field("name", "Nombre comercial")}<label><span className="mb-1 block text-sm font-bold">Tipo de empresa</span><select disabled={!canEdit} value={data.company_type ?? ""} onChange={(e) => setData({...data, company_type:e.target.value || null})} className="min-h-11 w-full rounded-xl border bg-white px-3"><option value="">Seleccionar</option><option>Profesional independiente</option><option>Consultorio</option><option>Clínica</option></select></label>{field("tax_id", "NIT")}{field("phone", "Teléfono")}{field("email", "Correo", "email")}{field("city", "Ciudad")}{field("country", "País")}<div className="sm:col-span-2">{field("address", "Dirección")}</div><label><span className="mb-1 block text-sm font-bold">Zona horaria</span><select disabled={!canEdit} value={data.timezone} onChange={(e)=>setData({...data,timezone:e.target.value})} className="min-h-11 w-full rounded-xl border bg-white px-3"><option>America/Bogota</option><option>America/Santiago</option><option>America/Lima</option><option>America/Mexico_City</option><option>America/New_York</option></select></label><label><span className="mb-1 block text-sm font-bold">Slug técnico</span><input disabled value={company.slug} className="min-h-11 w-full rounded-xl border bg-slate-50 px-3 text-slate-500"/></label></div>
    {canEdit && <div className="flex justify-end"><button disabled={busy || data.name.trim().length < 2} className="rounded-xl bg-green-700 px-5 py-3 font-bold text-white disabled:opacity-50">{busy ? "Guardando…" : "Guardar cambios"}</button></div>}
  </form>;
}
