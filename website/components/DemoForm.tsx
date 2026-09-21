"use client";

import Link from "next/link";
import { FormEvent, useRef, useState } from "react";

type SubmissionState = "idle" | "submitting" | "success" | "error";

export function DemoForm() {
  const [state, setState] = useState<SubmissionState>("idle");
  const submittingRef = useRef(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submittingRef.current) return;

    const form = event.currentTarget;
    const data = new FormData(form);
    submittingRef.current = true;
    setState("submitting");
    try {
      const response = await fetch("/api/public/demo-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          first_name: data.get("firstName"),
          last_name: data.get("lastName"),
          email: data.get("email"),
          phone: data.get("phone"),
          country: data.get("country"),
          city: data.get("city"),
          practice_type: data.get("practiceType"),
          dentist_count: Number(data.get("dentistCount")),
          message: data.get("message") || null,
          privacy_consent: data.get("privacyConsent") === "on",
          company_website: data.get("companyWebsite") || null,
        }),
      });
      if (!response.ok) throw new Error("request_failed");
      form.reset();
      setState("success");
    } catch {
      setState("error");
    } finally {
      submittingRef.current = false;
    }
  }

  return (
    <form className="demo-form" aria-describedby="demo-form-status" onSubmit={submit}>
      <div className="form-grid">
        <div className="form-field">
          <label htmlFor="demo-name">Nombre</label>
          <input id="demo-name" name="firstName" autoComplete="given-name" type="text" required minLength={2} maxLength={100} />
        </div>
        <div className="form-field">
          <label htmlFor="demo-last-name">Apellido</label>
          <input id="demo-last-name" name="lastName" autoComplete="family-name" type="text" required minLength={2} maxLength={100} />
        </div>
        <div className="form-field">
          <label htmlFor="demo-email">Email</label>
          <input id="demo-email" name="email" autoComplete="email" type="email" required maxLength={320} />
        </div>
        <div className="form-field">
          <label htmlFor="demo-phone">WhatsApp / teléfono</label>
          <input id="demo-phone" name="phone" autoComplete="tel" inputMode="tel" type="tel" required minLength={7} maxLength={50} />
        </div>
        <div className="form-field">
          <label htmlFor="demo-country">País</label>
          <select id="demo-country" name="country" defaultValue="" required>
            <option value="" disabled>Selecciona un país</option>
            <option value="CO">Colombia</option>
            <option value="CL">Chile</option>
            <option value="OTHER">Otro</option>
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="demo-city">Ciudad</label>
          <input id="demo-city" name="city" autoComplete="address-level2" type="text" required minLength={2} maxLength={120} />
        </div>
        <div className="form-field">
          <label htmlFor="demo-practice">Tipo de práctica</label>
          <select id="demo-practice" name="practiceType" defaultValue="" required>
            <option value="" disabled>Selecciona una opción</option>
            <option value="INDEPENDENT_DENTIST">Odontólogo independiente</option>
            <option value="DENTAL_OFFICE">Consultorio odontológico</option>
            <option value="DENTAL_CLINIC">Clínica odontológica</option>
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="demo-dentists">Número de odontólogos</label>
          <input id="demo-dentists" name="dentistCount" inputMode="numeric" min="1" max="10000" type="number" required />
        </div>
        <div className="form-field form-field--full">
          <label htmlFor="demo-message">Comentario o mensaje (opcional)</label>
          <textarea id="demo-message" name="message" maxLength={2000} />
        </div>
        <div className="demo-honeypot" aria-hidden="true">
          <label htmlFor="demo-company-website">Sitio web de la empresa</label>
          <input id="demo-company-website" name="companyWebsite" type="text" tabIndex={-1} autoComplete="off" />
        </div>
      </div>
      <label className="demo-consent">
        <input name="privacyConsent" type="checkbox" required />
        <span>
          He leído la <Link href="/privacidad">política de privacidad</Link> y autorizo a Dentia a
          contactarme respecto a mi solicitud de demostración.
        </span>
      </label>
      <button className="button button--primary" type="submit" disabled={state === "submitting"}>
        {state === "submitting" ? "Enviando…" : "Solicitar demostración"}
      </button>
      <p
        className={`form-disclosure ${state === "error" ? "form-disclosure--error" : ""} ${state === "success" ? "form-disclosure--success" : ""}`}
        id="demo-form-status"
        role={state === "error" ? "alert" : "status"}
        aria-live="polite"
      >
        {state === "success"
          ? "Solicitud recibida. Gracias por tu interés en Dentia. Revisaremos tu solicitud y te contactaremos para coordinar una demostración."
          : state === "error"
            ? "No pudimos enviar tu solicitud. Intenta nuevamente."
            : "Usaremos estos datos únicamente para atender tu solicitud de demostración."}
      </p>
    </form>
  );
}
