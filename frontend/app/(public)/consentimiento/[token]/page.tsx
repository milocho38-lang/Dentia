"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import {
  createTokenValidationGate,
  validatePublicConsentLink,
  type PublicConsentLink,
} from "@/lib/publicConsentClient.mjs";

type DocumentState = {
  title: string;
  clinic_name: string;
  patient_name: string;
  professional_name: string;
  clinical_date: string;
  procedures: string[];
  content: string;
  template_version: number;
  status_label: string;
};
type LoadState = "loading" | "ready" | "unavailable" | "rate_limited" | "network" | "timeout";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...options,
    credentials: "include",
    cache: "no-store",
    headers: { Accept: "application/json", ...(options.headers || {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "No fue posible completar la solicitud.");
  }
  return response.json();
}

const technicalErrors: Record<Exclude<LoadState, "loading" | "ready" | "unavailable">, string> = {
  rate_limited: "Se realizaron demasiados intentos. Espere un momento y vuelva a intentarlo.",
  network: "No fue posible conectar con Dentia. Revise su conexión e intente nuevamente.",
  timeout: "La validación tardó demasiado. Revise su conexión e intente nuevamente.",
};

export default function PublicConsentPage() {
  const params = useParams<{ token?: string | string[] }>();
  const routeToken = params?.token;
  const token = Array.isArray(routeToken) ? routeToken[0] : routeToken;
  const gateRef = useRef(createTokenValidationGate());
  const validationSequence = useRef(0);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [link, setLink] = useState<PublicConsentLink | null>(null);
  const [document, setDocument] = useState<DocumentState | null>(null);
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [step, setStep] = useState<"link" | "otp" | "document" | "clarification">("link");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const validateLink = useCallback(async (currentToken: string, force = false) => {
    if (!gateRef.current.shouldValidate(currentToken, { force })) return;
    const sequence = ++validationSequence.current;
    setLoadState("loading");
    setLink(null);
    const result = await validatePublicConsentLink(currentToken);
    if (sequence !== validationSequence.current) return;
    if (result.kind === "ready") {
      setLink(result.data);
      setLoadState("ready");
      return;
    }
    setLoadState(result.kind);
  }, []);

  useEffect(() => {
    if (!token) {
      setLoadState("unavailable");
      return;
    }
    void validateLink(token);
  }, [token, validateLink]);

  const path = token ? `/api/public/consents/${encodeURIComponent(token)}` : "";
  async function sendOtp() {
    if (!path) return;
    setBusy(true); setError(null);
    try { await request(`${path}/otp`, { method: "POST" }); setStep("otp"); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible enviar el código."); }
    finally { setBusy(false); }
  }
  async function verify() {
    if (!path) return;
    setBusy(true); setError(null);
    try {
      await request(`${path}/otp/verify`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code }) });
      setDocument(await request<DocumentState>(`${path}/document`)); setStep("document");
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Código no válido."); }
    finally { setBusy(false); }
  }
  async function clarify() {
    if (!path) return;
    setBusy(true); setError(null);
    try {
      await request(`${path}/clarification`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message }) });
      setDocument(null); setStep("clarification");
    } catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible registrar la solicitud."); }
    finally { setBusy(false); }
  }

  const retryable = loadState === "network" || loadState === "timeout" || loadState === "rate_limited";
  return <main className="min-h-screen bg-slate-50 px-4 py-8 text-slate-900"><div className="mx-auto max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-9"><header className="mb-7"><p className="text-lg font-black text-emerald-700">Dentia</p><h1 className="mt-2 text-2xl font-black">Revisión segura de consentimiento</h1><p className="mt-2 text-sm text-slate-600">Dentia nunca solicitará contraseñas ni información bancaria.</p></header>{error&&<p role="alert" className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-800">{error}</p>}
  {step === "link" && <section aria-live="polite">
    {loadState === "loading" && <p>Validando enlace seguro…</p>}
    {loadState === "unavailable" && <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">Este enlace es inválido, venció, fue revocado o el consentimiento ya no está disponible.</p>}
    {retryable && <div><p role="alert" className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900">{technicalErrors[loadState]}</p><button type="button" onClick={() => token && void validateLink(token, true)} className="mt-4 rounded-xl border px-4 py-3 font-bold">Reintentar</button></div>}
    {loadState === "ready" && link && <><p>{link.message}</p><p className="mt-3 text-sm">El código se enviará a <b>{link.recipient_masked}</b>.</p><p className="mt-1 text-xs text-slate-500">Acceso disponible aproximadamente hasta {new Date(link.expires_at).toLocaleString()}.</p><button disabled={busy} onClick={() => void sendOtp()} className="mt-6 min-h-12 w-full rounded-xl bg-emerald-700 font-black text-white disabled:opacity-50">Enviar código</button></>}
  </section>}
  {step === "otp" && <section><label className="block text-sm font-bold">Código de seis dígitos<input inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={code} onChange={event=>setCode(event.target.value.replace(/\D/g,""))} className="mt-2 min-h-14 w-full rounded-xl border px-4 text-center text-2xl tracking-[0.5em]" /></label><button disabled={busy||code.length!==6} onClick={()=>void verify()} className="mt-5 min-h-12 w-full rounded-xl bg-emerald-700 font-black text-white disabled:opacity-50">Verificar y revisar documento</button><button disabled={busy} onClick={()=>void sendOtp()} className="mt-3 w-full text-sm font-bold text-emerald-700">Reenviar código</button></section>}
  {step === "document" && document && <section><span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-black text-amber-800">{document.status_label}</span><h2 className="mt-4 text-2xl font-black">{document.title}</h2><dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2"><div><dt className="text-slate-500">Paciente</dt><dd className="font-bold">{document.patient_name}</dd></div><div><dt className="text-slate-500">Clínica</dt><dd className="font-bold">{document.clinic_name}</dd></div><div><dt className="text-slate-500">Profesional</dt><dd>{document.professional_name}</dd></div><div><dt className="text-slate-500">Fecha clínica</dt><dd>{document.clinical_date}</dd></div></dl>{document.procedures.length>0&&<p className="mt-4 text-sm"><b>Procedimientos:</b> {document.procedures.join(", ")}</p>}<article className="my-6 whitespace-pre-wrap rounded-xl border p-5 text-sm leading-7">{document.content}</article><p className="rounded-xl bg-sky-50 p-3 text-sm text-sky-900">Revise cuidadosamente este documento. La aceptación y firma se completarán en la siguiente etapa.</p><button onClick={()=>setStep("clarification")} className="mt-5 rounded-xl border px-4 py-3 font-bold">Necesito una aclaración</button></section>}
  {step === "clarification" && <section><h2 className="text-xl font-black">Solicitar aclaración</h2>{document&&<><label className="mt-4 block text-sm font-bold">Mensaje opcional<textarea maxLength={500} value={message} onChange={event=>setMessage(event.target.value)} className="mt-2 min-h-28 w-full rounded-xl border p-3 font-normal" /></label><button disabled={busy} onClick={()=>void clarify()} className="mt-4 rounded-xl bg-emerald-700 px-5 py-3 font-black text-white">Registrar solicitud</button></>}{!document&&<p className="mt-3 rounded-xl bg-emerald-50 p-4 text-emerald-900">La solicitud fue registrada. La clínica podrá atenderla antes de continuar.</p>}</section>}
  </div></main>;
}
