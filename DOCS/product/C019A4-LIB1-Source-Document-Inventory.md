# C019A4-LIB1 — Inventario fuente de documentos odontológicos

Fuente local no versionada: `local_inputs/consent_library/CONSENTIMIENTOS_PROPUESTOS.pdf`.

SHA-256 de fuente: `5389c42049ef4a6bcd90d765e7f4f2bbec8f8aad3114be955ba8ce6349259b7c`.

| # | Código | Documento | Clasificación | Especialidad | Páginas | Alcance de firma |
|---|--------|-----------|---------------|--------------|---------|------------------|
| 1 | `CERT_ASISTENCIA` | Certificado de asistencia | CERTIFICATE | GENERAL | 1-1 | ADMINISTRATIVE_RECORD |
| 2 | `CONS_BLANQUEAMIENTO` | Consentimiento informado de blanqueamiento dental | INFORMED_CONSENT | ESTETICA | 2-2 | ADULT_OR_REPRESENTATIVE |
| 3 | `CONS_ORTODONCIA` | Consentimiento informado de ortodoncia | INFORMED_CONSENT | ORTODONCIA | 3-5 | ADULT_OR_REPRESENTATIVE |
| 4 | `CONS_NO_GARANTIA` | Exención de garantía odontológica | NO_WARRANTY_ACKNOWLEDGEMENT | GENERAL | 6-6 | ADULT_SELF |
| 5 | `CONS_CIRUGIA` | Consentimiento informado de cirugía odontológica | INFORMED_CONSENT | CIRUGIA | 7-7 | ADULT_SELF |
| 6 | `CONS_DESTARTRAJE_OPERATORIA` | Consentimiento de destartraje y operatoria dental | INFORMED_CONSENT | OPERATORIA | 8-9 | ADULT_SELF |
| 7 | `CONS_IMPLANTOLOGIA` | Consentimiento informado de implantología | INFORMED_CONSENT | IMPLANTOLOGIA | 10-11 | ADULT_OR_REPRESENTATIVE |
| 8 | `CONS_ODONTOPEDIATRIA` | Consentimiento informado de odontopediatría | INFORMED_CONSENT | ODONTOPEDIATRIA | 12-13 | REPRESENTATIVE_REQUIRED |
| 9 | `RECHAZO_TRATAMIENTO` | Rechazo de tratamiento odontológico, quirúrgico o diagnóstico | TREATMENT_REFUSAL | GENERAL | 14-14 | ADULT_OR_REPRESENTATIVE |
| 10 | `CONS_DESTARTRAJE` | Consentimiento informado de destartraje | INFORMED_CONSENT | PERIODONCIA | 15-15 | ADULT_SELF |
| 11 | `CONS_ENDODONCIA` | Consentimiento informado de endodoncia | INFORMED_CONSENT | ENDODONCIA | 16-17 | ADULT_SELF |
| 12 | `CONS_OBTURACION_DIRECTA` | Consentimiento informado de obturación directa | INFORMED_CONSENT | OPERATORIA | 18-18 | ADULT_SELF |
| 13 | `CONS_OBTURACION_BASE` | Consentimiento informado de obturación directa con base cavitaria | INFORMED_CONSENT | OPERATORIA | 19-19 | ADULT_SELF |
| 14 | `CONS_PERIODONCIA` | Consentimiento informado de periodoncia | INFORMED_CONSENT | PERIODONCIA | 20-20 | ADULT_SELF |
| 15 | `CONS_PROTESIS_FIJA` | Consentimiento informado de rehabilitación oral prótesis fija | INFORMED_CONSENT | REHABILITACION_ORAL | 21-21 | ADULT_SELF |
| 16 | `CONS_PROTESIS_REMOVIBLE` | Consentimiento informado de rehabilitación oral prótesis removible | INFORMED_CONSENT | REHABILITACION_ORAL | 22-23 | ADULT_SELF |
| 17 | `CONS_REHAB_IMPLANTES` | Consentimiento informado de rehabilitación oral sobre implantes | INFORMED_CONSENT | REHABILITACION_ORAL | 24-25 | ADULT_SELF |
| 18 | `CONS_APROBACION_ESTETICA` | Aprobación estética de rehabilitación oral | AESTHETIC_APPROVAL | REHABILITACION_ORAL | 26-26 | ADULT_SELF |
| 19 | `CONS_URGENCIA` | Consentimiento informado de urgencia odontológica | INFORMED_CONSENT | URGENCIA | 27-27 | ADULT_SELF |
| 20 | `CONS_OXIDO_NITROSO` | Consentimiento informado de óxido nitroso | INFORMED_CONSENT | SEDACION | 28-29 | ADULT_OR_REPRESENTATIVE |
| 21 | `CONS_PLANO_RELAJACION` | Consentimiento informado de plano de relajación y estabilización | INFORMED_CONSENT | REHABILITACION_ORAL | 30-30 | ADULT_SELF |
| 22 | `CONS_RETIRO_ORTODONCIA` | Retiro anticipado de ortodoncia y paciente externo | TREATMENT_TERMINATION_ACKNOWLEDGEMENT | ORTODONCIA | 31-31 | ADULT_SELF |
| 23 | `IND_CIRUGIA` | Indicaciones de cirugía | POST_CARE_INSTRUCTIONS | CIRUGIA | 32-32 | NO_SIGNATURE_REQUIRED |
| 24 | `IND_CIRUGIA_IMPLANTES` | Indicaciones de cirugía de implantes | POST_CARE_INSTRUCTIONS | IMPLANTOLOGIA | 33-33 | NO_SIGNATURE_REQUIRED |
| 25 | `IND_ENDODONCIA` | Indicaciones de endodoncia | POST_CARE_INSTRUCTIONS | ENDODONCIA | 34-34 | NO_SIGNATURE_REQUIRED |
| 26 | `IND_BLANQUEAMIENTO` | Indicaciones de blanqueamiento | POST_CARE_INSTRUCTIONS | ESTETICA | 34-34 | NO_SIGNATURE_REQUIRED |
| 27 | `IND_FLUOR_BARNIZ` | Aplicación de flúor barniz | POST_CARE_INSTRUCTIONS | ODONTOPEDIATRIA | 34-34 | NO_SIGNATURE_REQUIRED |
| 28 | `IND_OBTURACIONES_RESINA` | Indicaciones de obturaciones en resina | POST_CARE_INSTRUCTIONS | OPERATORIA | 35-36 | NO_SIGNATURE_REQUIRED |
| 29 | `IND_DESTARTRAJE` | Indicaciones para destartraje | POST_CARE_INSTRUCTIONS | PERIODONCIA | 35-35 | NO_SIGNATURE_REQUIRED |
| 30 | `IND_ODONTOPEDIATRIA_GENERAL` | Indicaciones generales de odontopediatría | POST_CARE_INSTRUCTIONS | ODONTOPEDIATRIA | 35-35 | NO_SIGNATURE_REQUIRED |
| 31 | `IND_ORTODONCIA` | Indicaciones de ortodoncia | POST_CARE_INSTRUCTIONS | ORTODONCIA | 36-36 | NO_SIGNATURE_REQUIRED |
| 32 | `IND_PERIODONCIA` | Indicaciones de periodoncia | POST_CARE_INSTRUCTIONS | PERIODONCIA | 36-37 | NO_SIGNATURE_REQUIRED |
| 33 | `IND_PREOP_CIRUGIA_MAXILOFACIAL` | Indicaciones preoperatorias de cirugía menor maxilofacial | PRE_CARE_INSTRUCTIONS | CIRUGIA_MAXILOFACIAL | 37-38 | NO_SIGNATURE_REQUIRED |
| 34 | `IND_REHABILITACION_ORAL` | Indicaciones de rehabilitación oral | POST_CARE_INSTRUCTIONS | REHABILITACION_ORAL | 38-39 | NO_SIGNATURE_REQUIRED |
| 35 | `IND_TRAUMA_DENTOALVEOLAR` | Indicaciones de odontopediatría trauma dentoalveolar | POST_CARE_INSTRUCTIONS | ODONTOPEDIATRIA | 39-39 | NO_SIGNATURE_REQUIRED |

## Patrones relevantes detectados

- El documento fuente contiene referencias institucionales a Clínica/Dental Seis que fueron reemplazadas por variables seguras de Dentia.
- Se detectaron documentos que no son consentimientos comunes: certificado de asistencia, rechazo de tratamiento, exención/no garantía, aprobación estética, retiro anticipado e indicaciones pre/postoperatorias.
- Se detectaron documentos con representante/apoderado o menores. Esos documentos quedan clasificados, pero no se habilitan como flujo electrónico estándar de adulto en C019A.4.
- Se preservan términos locales de instrucciones clínicas como “cabritas”, “bombilla”, “calugas” y “tapadura” cuando pertenecen al texto fuente.
