"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import type React from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import {
  deleteBrandingAsset,
  fetchBrandingAsset,
  getBranding,
  updateBranding,
  uploadBrandingAsset,
} from "@/services/organizationService";
import type { Branding, BrandingInput } from "@/types/organization";

const defaults: BrandingInput = {
  name: "",
  legal_name: null,
  company_type: null,
  tax_id: null,
  address: null,
  city: null,
  department: null,
  country: null,
  phone: null,
  mobile: null,
  email: null,
  website: null,
  social_media: null,
  primary_dentist_name: null,
  professional_specialty: null,
  professional_license: null,
  university: null,
  experience_years: null,
  header_text: null,
  footer_text: null,
  legal_observations: null,
  cancellation_policy: null,
  thank_you_message: null,
  payment_receipt_title: "COMPROBANTE DE PAGO",
  primary_color: "#16a34a",
  secondary_color: "#0f766e",
  button_color: "#16a34a",
  heading_color: "#0f172a",
};

function toInput(branding: Branding): BrandingInput {
  return {
    name: branding.name,
    legal_name: branding.legal_name,
    company_type: branding.company_type,
    tax_id: branding.tax_id,
    address: branding.address,
    city: branding.city,
    department: branding.department,
    country: branding.country,
    phone: branding.phone,
    mobile: branding.mobile,
    email: branding.email,
    website: branding.website,
    social_media: branding.social_media,
    primary_dentist_name: branding.primary_dentist_name,
    professional_specialty: branding.professional_specialty,
    professional_license: branding.professional_license,
    university: branding.university,
    experience_years: branding.experience_years,
    header_text: branding.header_text,
    footer_text: branding.footer_text,
    legal_observations: branding.legal_observations,
    cancellation_policy: branding.cancellation_policy,
    thank_you_message: branding.thank_you_message,
    payment_receipt_title: branding.payment_receipt_title,
    primary_color: branding.primary_color,
    secondary_color: branding.secondary_color,
    button_color: branding.button_color,
    heading_color: branding.heading_color,
  };
}

function parseSocialMedia(value: string): Record<string, string> | null {
  const lines = value.split("\n").map((line) => line.trim()).filter(Boolean);
  if (!lines.length) return null;
  return lines.reduce<Record<string, string>>((accumulator, line) => {
    const [key, ...rest] = line.split(":");
    const value = rest.join(":").trim();
    if (key.trim() && value) accumulator[key.trim()] = value;
    return accumulator;
  }, {});
}

function formatSocialMedia(value: Record<string, string> | null): string {
  if (!value) return "";
  return Object.entries(value).map(([key, item]) => `${key}: ${item}`).join("\n");
}

export function BrandingSettingsPage() {
  const { hasPermission } = useAuth();
  const canEdit = hasPermission("branding.update");
  const [branding, setBranding] = useState<Branding | null>(null);
  const [data, setData] = useState<BrandingInput>(defaults);
  const [socialText, setSocialText] = useState("");
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [signaturePreview, setSignaturePreview] = useState<string | null>(null);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [signatureFile, setSignatureFile] = useState<File | null>(null);
  const [deleteLogo, setDeleteLogo] = useState(false);
  const [deleteSignature, setDeleteSignature] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadAsset = useCallback(async (kind: "logo" | "signature", exists: boolean) => {
    if (!exists) return null;
    try {
      const blob = await fetchBrandingAsset(kind);
      return URL.createObjectURL(blob);
    } catch {
      return null;
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const loaded = await getBranding();
      setBranding(loaded);
      setData(toInput(loaded));
      setSocialText(formatSocialMedia(loaded.social_media));
      const [logo, signature] = await Promise.all([
        loadAsset("logo", Boolean(loaded.logo_url)),
        loadAsset("signature", Boolean(loaded.signature_url)),
      ]);
      setLogoPreview((current) => {
        if (current) URL.revokeObjectURL(current);
        return logo;
      });
      setSignaturePreview((current) => {
        if (current) URL.revokeObjectURL(current);
        return signature;
      });
    } catch {
      setError("No fue posible cargar la personalización.");
    } finally {
      setLoading(false);
    }
  }, [loadAsset]);

  useEffect(() => {
    load();
    return () => {
      if (logoPreview) URL.revokeObjectURL(logoPreview);
      if (signaturePreview) URL.revokeObjectURL(signaturePreview);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load]);

  function update<K extends keyof BrandingInput>(key: K, value: BrandingInput[K]) {
    setData((current) => ({ ...current, [key]: value }));
  }

  function previewFile(kind: "logo" | "signature", file: File | null) {
    const setPreview = kind === "logo" ? setLogoPreview : setSignaturePreview;
    const setFile = kind === "logo" ? setLogoFile : setSignatureFile;
    const setDelete = kind === "logo" ? setDeleteLogo : setDeleteSignature;
    setFile(file);
    setDelete(false);
    setPreview((current) => {
      if (current) URL.revokeObjectURL(current);
      return file ? URL.createObjectURL(file) : null;
    });
  }

  function markDelete(kind: "logo" | "signature") {
    if (kind === "logo") {
      setLogoFile(null);
      setDeleteLogo(true);
      setLogoPreview((current) => {
        if (current) URL.revokeObjectURL(current);
        return null;
      });
    } else {
      setSignatureFile(null);
      setDeleteSignature(true);
      setSignaturePreview((current) => {
        if (current) URL.revokeObjectURL(current);
        return null;
      });
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      let saved = await updateBranding({
        ...data,
        social_media: parseSocialMedia(socialText),
      });
      if (deleteLogo && saved.logo_url) saved = await deleteBrandingAsset("logo");
      if (deleteSignature && saved.signature_url) saved = await deleteBrandingAsset("signature");
      if (logoFile) saved = await uploadBrandingAsset("logo", logoFile);
      if (signatureFile) saved = await uploadBrandingAsset("signature", signatureFile);
      setBranding(saved);
      setData(toInput(saved));
      setSocialText(formatSocialMedia(saved.social_media));
      setLogoFile(null);
      setSignatureFile(null);
      setDeleteLogo(false);
      setDeleteSignature(false);
      setSuccess("Personalización guardada.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible guardar la personalización.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="flex justify-center py-20"><Spinner className="h-7 w-7 text-dentia-primary" /></div>;
  }

  if (!branding) {
    return <Alert tone="error">{error ?? "Personalización no disponible."}</Alert>;
  }

  const field = (key: keyof BrandingInput, label: string, type = "text") => (
    <label>
      <span className="mb-1 block text-sm font-bold text-slate-700">{label}</span>
      <input
        type={type}
        disabled={!canEdit}
        value={(data[key] as string | number | null) ?? ""}
        onChange={(event) => {
          const value = event.target.value;
          update(key, (type === "number" ? (value ? Number(value) : null) : value || null) as never);
        }}
        className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm disabled:bg-slate-50"
      />
    </label>
  );

  const textarea = (key: keyof BrandingInput, label: string, rows = 3) => (
    <label>
      <span className="mb-1 block text-sm font-bold text-slate-700">{label}</span>
      <textarea
        rows={rows}
        disabled={!canEdit}
        value={(data[key] as string | null) ?? ""}
        onChange={(event) => update(key, (event.target.value || null) as never)}
        className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50"
      />
    </label>
  );

  return (
    <form onSubmit={submit} className="mx-auto max-w-7xl space-y-6">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">Configuración</p>
        <h1 className="mt-2 text-3xl font-black text-slate-950">Personalización</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">
          Configura la identidad visual y los textos institucionales que usará Dentia en documentos futuros.
        </p>
      </header>
      {error && <Alert tone="error">{error}</Alert>}
      {success && <Alert tone="info">{success}</Alert>}

      <Card title="Información general">
        <div className="grid gap-4 md:grid-cols-2">
          {field("name", "Nombre comercial")}
          {field("legal_name", "Razón social")}
          <label>
            <span className="mb-1 block text-sm font-bold text-slate-700">Tipo de empresa</span>
            <select
              disabled={!canEdit}
              value={data.company_type ?? ""}
              onChange={(event) => update("company_type", event.target.value || null)}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm disabled:bg-slate-50"
            >
              <option value="">Seleccionar</option>
              <option>Profesional independiente</option>
              <option>Consultorio</option>
              <option>Clínica</option>
            </select>
          </label>
          {field("tax_id", "NIT / RUT")}
          {field("phone", "Teléfono")}
          {field("mobile", "Celular")}
          {field("email", "Correo", "email")}
          {field("website", "Sitio web", "url")}
          {field("city", "Ciudad")}
          {field("department", "Departamento / Región")}
          {field("country", "País")}
          <div className="md:col-span-2">{field("address", "Dirección principal")}</div>
          <label className="md:col-span-2">
            <span className="mb-1 block text-sm font-bold text-slate-700">Redes sociales</span>
            <textarea
              rows={3}
              disabled={!canEdit}
              placeholder={"Instagram: https://...\nFacebook: https://..."}
              value={socialText}
              onChange={(event) => setSocialText(event.target.value)}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50"
            />
            <span className="mt-1 block text-xs text-slate-500">Una red por línea con formato Nombre: URL.</span>
          </label>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <AssetCard
          title="Logo principal"
          description="PNG, JPG o SVG. Máximo 5 MB."
          accept="image/png,image/jpeg,image/svg+xml"
          preview={logoPreview}
          filename={logoFile?.name ?? branding.logo_filename}
          canEdit={canEdit}
          onChange={(file) => previewFile("logo", file)}
          onDelete={() => markDelete("logo")}
        />
        <AssetCard
          title="Firma digital"
          description="PNG transparente preferiblemente. También JPG. Máximo 5 MB."
          accept="image/png,image/jpeg"
          preview={signaturePreview}
          filename={signatureFile?.name ?? branding.signature_filename}
          canEdit={canEdit}
          onChange={(file) => previewFile("signature", file)}
          onDelete={() => markDelete("signature")}
        />
      </div>

      <Card title="Información profesional">
        <div className="grid gap-4 md:grid-cols-2">
          {field("primary_dentist_name", "Nombre del odontólogo principal")}
          {field("professional_specialty", "Especialidad")}
          {field("professional_license", "Registro profesional")}
          {field("university", "Universidad")}
          {field("experience_years", "Años de experiencia", "number")}
        </div>
      </Card>

      <Card title="Información para documentos">
        <div className="grid gap-4 md:grid-cols-2">
          {textarea("header_text", "Texto de encabezado")}
          {textarea("footer_text", "Texto de pie de página")}
          {field("payment_receipt_title", "Nombre del comprobante de pago")}
          {textarea("legal_observations", "Observaciones legales", 4)}
          {textarea("cancellation_policy", "Política de cancelación", 4)}
          <div className="md:col-span-2">{textarea("thank_you_message", "Mensaje de agradecimiento")}</div>
        </div>
      </Card>

      <Card title="Colores institucionales">
        <div className="grid gap-4 md:grid-cols-4">
          <ColorField label="Color principal" value={data.primary_color} disabled={!canEdit} onChange={(value) => update("primary_color", value)} />
          <ColorField label="Color secundario" value={data.secondary_color} disabled={!canEdit} onChange={(value) => update("secondary_color", value)} />
          <ColorField label="Color de botones" value={data.button_color} disabled={!canEdit} onChange={(value) => update("button_color", value)} />
          <ColorField label="Color de encabezados" value={data.heading_color} disabled={!canEdit} onChange={(value) => update("heading_color", value)} />
        </div>
      </Card>

      {canEdit && (
        <div className="flex justify-end">
          <button
            disabled={saving}
            className="min-h-11 rounded-xl bg-dentia-primary px-6 text-sm font-bold text-white hover:bg-green-700 disabled:opacity-60"
          >
            {saving ? "Guardando…" : "Guardar personalización"}
          </button>
        </div>
      )}
    </form>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <h2 className="text-lg font-black text-slate-950">{title}</h2>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function AssetCard({
  title,
  description,
  accept,
  preview,
  filename,
  canEdit,
  onChange,
  onDelete,
}: {
  title: string;
  description: string;
  accept: string;
  preview: string | null;
  filename: string | null;
  canEdit: boolean;
  onChange: (file: File | null) => void;
  onDelete: () => void;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <h2 className="text-lg font-black text-slate-950">{title}</h2>
      <p className="mt-1 text-sm text-slate-500">{description}</p>
      <div className="mt-5 flex min-h-48 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4">
        {preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={preview} alt={title} className="max-h-40 max-w-full object-contain" />
        ) : (
          <p className="text-sm text-slate-500">Sin archivo cargado.</p>
        )}
      </div>
      {filename && <p className="mt-3 truncate text-xs font-bold text-slate-500">{filename}</p>}
      {canEdit && (
        <div className="mt-4 flex flex-wrap gap-3">
          <label className="cursor-pointer rounded-xl border border-green-200 px-4 py-2 text-sm font-bold text-green-700 hover:bg-green-50">
            Seleccionar archivo
            <input
              type="file"
              accept={accept}
              className="sr-only"
              onChange={(event) => onChange(event.target.files?.[0] ?? null)}
            />
          </label>
          <button type="button" onClick={onDelete} className="rounded-xl border border-red-200 px-4 py-2 text-sm font-bold text-red-700 hover:bg-red-50">
            Eliminar
          </button>
        </div>
      )}
    </section>
  );
}

function ColorField({
  label,
  value,
  disabled,
  onChange,
}: {
  label: string;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      <span className="mb-1 block text-sm font-bold text-slate-700">{label}</span>
      <div className="flex min-h-11 overflow-hidden rounded-xl border border-slate-300 bg-white">
        <input type="color" disabled={disabled} value={value} onChange={(event) => onChange(event.target.value)} className="h-11 w-14 border-0 bg-transparent p-1" />
        <input disabled={disabled} value={value} onChange={(event) => onChange(event.target.value)} className="min-w-0 flex-1 px-3 text-sm disabled:bg-slate-50" />
      </div>
    </label>
  );
}
