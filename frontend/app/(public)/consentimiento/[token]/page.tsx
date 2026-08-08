"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import {
  createTokenValidationGate,
  validatePublicConsentLink,
  type PublicConsentLink,
} from "@/lib/publicConsentClient.mjs";
import { ConsentSignatureCanvas } from "@/components/consents/ConsentSignatureCanvas";
import { ConsentRestrictedMarkdown } from "@/components/consents/ConsentRestrictedMarkdown";
import { ConsentSubmissionAct } from "@/lib/consentSubmissionAct.mjs";
import { SecureRandomUuidUnavailableError } from "@/lib/secureRandomUuid.mjs";
import { acceptanceErrorMessage, publicConsentRequestError } from "@/lib/publicConsentAcceptanceError.mjs";
import { publishConsentSigned } from "@/lib/consentStatusEvents.mjs";

type DocumentState = {
  title: string;
  clinic_name: string;
  patient_name: string;
  signer_actor_type: "PATIENT_SELF" | "RESPONSIBLE_ADULT";
  signer_name: string | null;
  signer_relationship: string | null;
  professional_name: string;
  clinical_date: string;
  procedures: string[];
  content: string;
  template_version: number;
  status_label: string;
  test_document: boolean;
  is_test_document: boolean;
  test_notice: string | null;
  legal_review_status: string | null;
  declaration_set_code: string | null;
  declaration_set_version: string | null;
  acceptance_compatible: boolean;
  acceptance_block_message: string | null;
};
type LoadState = "loading" | "ready" | "unavailable" | "rate_limited" | "network" | "timeout";
type Requirements = { enabled:boolean; declaration_set_code:string; declarations_country_code:string; declarations_locale:string; declarations_version:string; declarations_legal_status:string; declarations_set_sha256:string; declarations:{code:string;text:string;order:number}[]; patient_name:string; signer_actor_type:"PATIENT_SELF"|"RESPONSIBLE_ADULT"; signer_name:string|null; signer_relationship:string|null; signature_required:boolean; legal_review_pending:boolean; test_document:boolean; test_notice:string|null };
type SignedResult = { acceptance_id:string; accepted_at:string; final_document_sha256:string; verification_id:string; download_url:string; copy_delivery_status:string; test_document:boolean; test_notice:string|null };

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...options,
    credentials: "include",
    cache: "no-store",
    headers: { Accept: "application/json", ...(options.headers || {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    if (options.method === "POST" && path.endsWith("/acceptance")) throw publicConsentRequestError(response.status, body);
    throw new Error(typeof body.detail === "string" ? body.detail : "No fue posible completar la solicitud.");
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
  const [step, setStep] = useState<"link" | "otp" | "document" | "declarations" | "identity" | "signature" | "confirm" | "signed" | "clarification">("link");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [requirements,setRequirements]=useState<Requirements|null>(null);
  const [accepted,setAccepted]=useState<Record<string,boolean>>({});
  const [ownBehalf,setOwnBehalf]=useState(false);
  const [typedName,setTypedName]=useState("");
  const [signature,setSignature]=useState<string|null>(null);
  const [signed,setSigned]=useState<SignedResult|null>(null);
  const submissionActRef=useRef<ConsentSubmissionAct|null>(null);
  if (!submissionActRef.current) submissionActRef.current = new ConsentSubmissionAct();

  function invalidateSubmissionAct(){submissionActRef.current?.invalidate();}

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
  async function continueToAcceptance(){if(!path)return;setBusy(true);setError(null);try{const value=await request<Requirements>(`${path}/acceptance-requirements`);setRequirements(value);setAccepted({});setOwnBehalf(value.signer_actor_type === "PATIENT_SELF");setTypedName("");setSignature(null);submissionActRef.current?.invalidate();setStep("declarations");}catch(caught){setError(caught instanceof Error?caught.message:"No fue posible iniciar la aceptación.");}finally{setBusy(false);}}
  async function submitAcceptance(){
    if(!path||!requirements||!signature||signed)return;
    let idempotencyKey:string|null;
    try{idempotencyKey=submissionActRef.current?.begin()??null;}
    catch(caught){setError(caught instanceof SecureRandomUuidUnavailableError?"No fue posible preparar el envío de forma segura. Sus datos permanecen en esta pantalla. Intente nuevamente.":"No fue posible completar el envío. Sus datos permanecen en esta pantalla. Intente nuevamente.");return;}
    if(!idempotencyKey)return;
    setBusy(true);setError(null);
    try{
      const result=await request<SignedResult>(`${path}/acceptance`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({idempotency_key:idempotencyKey,acting_on_own_behalf:ownBehalf,declaration_set_code:requirements.declaration_set_code,declarations_version:requirements.declarations_version,declarations_set_sha256:requirements.declarations_set_sha256,declarations:requirements.declarations.map(item=>({code:item.code,accepted:Boolean(accepted[item.code])})),typed_full_name:typedName,signature_data_url:signature})});
      submissionActRef.current?.settle({completed:true});publishConsentSigned(result.acceptance_id);setSigned(result);setStep("signed");
    }catch(caught){
      submissionActRef.current?.settle();
      setError(caught instanceof SecureRandomUuidUnavailableError?"No fue posible preparar el envío de forma segura. Sus datos permanecen en esta pantalla. Intente nuevamente.":acceptanceErrorMessage(caught));
    }finally{setBusy(false);}
  }

  const retryable = loadState === "network" || loadState === "timeout" || loadState === "rate_limited";
  const testNotice = signed?.test_notice ?? requirements?.test_notice ?? document?.test_notice ?? null;
  const showTestNotice = Boolean(signed?.test_document ?? requirements?.test_document ?? document?.is_test_document);
  const showAcceptanceStage = ["document", "declarations", "identity", "signature", "confirm", "signed"].includes(step);
  return <main className="min-h-[100dvh] bg-slate-50 text-slate-900" style={{paddingTop:"calc(2rem + env(safe-area-inset-top))",paddingRight:"calc(1rem + env(safe-area-inset-right))",paddingBottom:"calc(2rem + env(safe-area-inset-bottom))",paddingLeft:"calc(1rem + env(safe-area-inset-left))"}}><div className="mx-auto max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-9"><header className="mb-7"><p className="text-lg font-black text-emerald-700">Dentia</p><h1 className="mt-2 text-2xl font-black">Revisión segura de consentimiento</h1><p className="mt-2 text-sm text-slate-600">Dentia nunca solicitará contraseñas ni información bancaria.</p></header>{showAcceptanceStage&&showTestNotice&&testNotice&&<p role="alert" data-testid="test-document-notice" className="mb-4 rounded-xl border-2 border-red-700 bg-red-50 p-3 text-center text-sm font-black text-red-800">{testNotice}</p>}{error&&<p role="alert" className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-800">{error}</p>}
  {step === "link" && <section aria-live="polite">
    {loadState === "loading" && <p>Validando enlace seguro…</p>}
    {loadState === "unavailable" && <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">Este enlace es inválido, venció, fue revocado o el consentimiento ya no está disponible.</p>}
    {retryable && <div><p role="alert" className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900">{technicalErrors[loadState]}</p><button type="button" onClick={() => token && void validateLink(token, true)} className="mt-4 rounded-xl border px-4 py-3 font-bold">Reintentar</button></div>}
    {loadState === "ready" && link && <><p>{link.message}</p><p className="mt-3 text-sm">El código se enviará a <b>{link.recipient_masked}</b>.</p><p className="mt-1 text-xs text-slate-500">Acceso disponible aproximadamente hasta {new Date(link.expires_at).toLocaleString()}.</p><button disabled={busy} onClick={() => void sendOtp()} className="mt-6 min-h-12 w-full rounded-xl bg-emerald-700 font-black text-white disabled:opacity-50">Enviar código</button></>}
  </section>}
  {step === "otp" && <section><label className="block text-sm font-bold">Código de seis dígitos<input inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={code} onChange={event=>setCode(event.target.value.replace(/\D/g,""))} className="mt-2 min-h-14 w-full rounded-xl border px-4 text-center text-2xl tracking-[0.5em]" /></label><button disabled={busy||code.length!==6} onClick={()=>void verify()} className="mt-5 min-h-12 w-full rounded-xl bg-emerald-700 font-black text-white disabled:opacity-50">Verificar y revisar documento</button><button disabled={busy} onClick={()=>void sendOtp()} className="mt-3 w-full text-sm font-bold text-emerald-700">Reenviar código</button></section>}
  {step === "document" && document && <section><span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-black text-amber-800">{document.status_label}</span><h2 className="mt-4 text-2xl font-black">{document.title}</h2><dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2"><div><dt className="text-slate-500">Paciente</dt><dd className="font-bold">{document.patient_name}</dd></div>{document.signer_actor_type === "RESPONSIBLE_ADULT" && <div><dt className="text-slate-500">Adulto responsable que firma</dt><dd className="font-bold">{document.signer_name}{document.signer_relationship ? ` · ${document.signer_relationship}` : ""}</dd></div>}<div><dt className="text-slate-500">Clínica</dt><dd className="font-bold">{document.clinic_name}</dd></div><div><dt className="text-slate-500">Profesional que confirmó el contenido clínico</dt><dd>{document.professional_name}</dd></div><div><dt className="text-slate-500">Fecha clínica</dt><dd>{document.clinical_date}</dd></div></dl>{document.procedures.length>0&&<p className="mt-4 text-sm"><b>Procedimientos:</b> {document.procedures.join(", ")}</p>}<article className="my-6 rounded-xl border p-5"><ConsentRestrictedMarkdown content={document.content}/></article>{!document.acceptance_compatible&&<p role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm font-bold text-amber-950">{document.acceptance_block_message}</p>}<p className="mt-4 rounded-xl bg-sky-50 p-3 text-sm text-sky-900">Revise cuidadosamente el documento antes de continuar.</p><div className="mt-5 flex flex-wrap gap-3">{document.acceptance_compatible&&<button disabled={busy} onClick={()=>void continueToAcceptance()} className="rounded-xl bg-emerald-700 px-5 py-3 font-black text-white">Continuar a aceptación</button>}<button onClick={()=>setStep("clarification")} className="rounded-xl border px-4 py-3 font-bold">Necesito una aclaración</button></div></section>}
  {step === "declarations"&&requirements&&<section><h2 className="text-xl font-black">Declaraciones</h2><p className="mt-2 text-sm text-amber-800">{requirements.declarations_country_code} · {requirements.declarations_locale} · {requirements.declarations_legal_status}</p><div className="mt-5 space-y-3">{requirements.declarations.map(item=><label key={item.code} className="flex items-start gap-3 rounded-xl border p-3 text-sm"><input type="checkbox" checked={Boolean(accepted[item.code])} onChange={event=>{invalidateSubmissionAct();setAccepted(current=>({...current,[item.code]:event.target.checked}));}}/><span>{item.text}</span></label>)}</div><button disabled={!requirements.declarations.every(item=>accepted[item.code])} onClick={()=>setStep("identity")} className="mt-5 w-full rounded-xl bg-emerald-700 px-5 py-3 font-black text-white disabled:opacity-50">Continuar</button></section>}
  {step === "identity"&&requirements&&<section><h2 className="text-xl font-black">Confirmación de identidad</h2><p className="mt-2 text-sm">Paciente identificado: <b>{requirements.patient_name}</b></p>{requirements.signer_actor_type === "RESPONSIBLE_ADULT" ? <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm"><p>Firmará como adulto responsable:</p><p className="mt-1 font-black">{requirements.signer_name}{requirements.signer_relationship ? ` · ${requirements.signer_relationship}` : ""}</p><p className="mt-2 text-xs text-slate-600">La clínica preparó este consentimiento con este firmante. Si los datos no son correctos, no continúe y contacte a la clínica.</p></div> : <label className="mt-5 flex items-start gap-3 rounded-xl border p-4 text-sm"><input type="checkbox" checked={ownBehalf} onChange={event=>{invalidateSubmissionAct();setOwnBehalf(event.target.checked);}}/><span>Declaro que estoy actuando en nombre propio y que soy la persona identificada en este consentimiento.</span></label>}<label className="mt-5 block text-sm font-bold">Digite el nombre completo del firmante<input value={typedName} autoComplete="name" onChange={event=>{invalidateSubmissionAct();setTypedName(event.target.value);}} className="mt-2 min-h-12 w-full rounded-xl border px-4 font-normal"/></label><button disabled={(requirements.signer_actor_type === "PATIENT_SELF" && !ownBehalf)||typedName.trim().length<2} onClick={()=>setStep("signature")} className="mt-5 w-full rounded-xl bg-emerald-700 px-5 py-3 font-black text-white disabled:opacity-50">Continuar a firma</button></section>}
  {step === "signature"&&<section><h2 className="text-xl font-black">Firma manuscrita electrónica</h2><p className="my-3 text-sm text-slate-600">Dibuje su firma dentro del recuadro. No cargue archivos externos.</p><ConsentSignatureCanvas onChange={value=>{invalidateSubmissionAct();setSignature(value);}}/><button disabled={!signature} onClick={()=>setStep("confirm")} className="mt-5 w-full rounded-xl bg-emerald-700 px-5 py-3 font-black text-white disabled:opacity-50">Revisar y confirmar</button></section>}
  {step === "confirm"&&requirements&&<section><h2 className="text-xl font-black">Confirmación final</h2><dl className="mt-4 space-y-2 rounded-xl bg-slate-50 p-4 text-sm"><div><dt className="text-slate-500">Paciente</dt><dd className="font-bold">{requirements.patient_name}</dd></div>{requirements.signer_actor_type === "RESPONSIBLE_ADULT" && <div><dt className="text-slate-500">Adulto responsable</dt><dd>{requirements.signer_name}{requirements.signer_relationship ? ` · ${requirements.signer_relationship}` : ""}</dd></div>}<div><dt className="text-slate-500">Nombre digitado</dt><dd>{typedName}</dd></div><div><dt className="text-slate-500">Declaraciones</dt><dd>{requirements.declarations.length} aceptadas individualmente</dd></div></dl><p className="mt-4 text-sm text-red-700">Al confirmar se generará un registro inmutable y el documento final. Revise antes de continuar.</p><button disabled={busy} onClick={()=>void submitAcceptance()} className="mt-5 w-full rounded-xl bg-emerald-700 px-5 py-3 font-black text-white disabled:opacity-50">Confirmar aceptación y firma</button></section>}
  {step === "signed"&&signed&&<section><h2 className="text-2xl font-black text-emerald-800">Aceptación registrada</h2><p className="mt-3 text-sm">Fecha: {new Date(signed.accepted_at).toLocaleString()}</p><p className="mt-2 break-all text-xs text-slate-500">Verificación: {signed.verification_id}<br/>SHA-256: {signed.final_document_sha256}</p><a href={signed.download_url} className="mt-6 block rounded-xl bg-emerald-700 px-5 py-3 text-center font-black text-white">Descargar copia PDF</a><p className="mt-3 text-xs text-slate-500">Entrega por correo: {signed.copy_delivery_status}. Si la entrega falla, la clínica puede reenviar la copia sin alterar el documento.</p></section>}
  {step === "clarification" && <section><h2 className="text-xl font-black">Solicitar aclaración</h2>{document&&<><label className="mt-4 block text-sm font-bold">Mensaje opcional<textarea maxLength={500} value={message} onChange={event=>setMessage(event.target.value)} className="mt-2 min-h-28 w-full rounded-xl border p-3 font-normal" /></label><button disabled={busy} onClick={()=>void clarify()} className="mt-4 rounded-xl bg-emerald-700 px-5 py-3 font-black text-white">Registrar solicitud</button></>}{!document&&<p className="mt-3 rounded-xl bg-emerald-50 p-4 text-emerald-900">La solicitud fue registrada. La clínica podrá atenderla antes de continuar.</p>}</section>}
  </div></main>;
}
