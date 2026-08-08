# C019A.4-LIB1-NORM5 — Normalización electrónica segura

NORM5 crea un paquete inmutable v4 desde v3. Limpia artefactos administrativos seguros, conserva `source_text` y bloquea las variantes ambiguas para diseño/revisión posterior.

- Esquema: `LIB1_NORM_V2_ELECTRONIC_READINESS`
- Documentos: 35
- Variantes: 70
- Nuevas versiones: 18
- Resultados: `{'SAFE_NORMALIZED': 18, 'NO_CHANGE': 48, 'NEEDS_STRUCTURED_FIELD': 2, 'NEEDS_HUMAN_REVIEW': 2}`
- Aptitud electrónica: `{'READY': 62, 'BLOCKED': 8}`

## Cambios de signer policy

| Código | País | Versión | Antes | Después |
|---|---|---:|---|---|
| `CONS_OXIDO_NITROSO` | CO | 3 → 4 | `RESPONSIBLE_ADULT_REQUIRED` | `PATIENT_OR_RESPONSIBLE_ADULT` |
| `CONS_OXIDO_NITROSO` | CL | 3 → 4 | `RESPONSIBLE_ADULT_REQUIRED` | `PATIENT_OR_RESPONSIBLE_ADULT` |

## Nuevas versiones

| Código | País | Versión | Resultado | Aptitud | Cambios |
|---|---|---:|---|---|---|
| `CERT_ASISTENCIA` | CO | 2 → 3 | `SAFE_NORMALIZED` | `READY` | attendance_manual_identity_and_date_replaced_with_structured_variables |
| `CERT_ASISTENCIA` | CL | 2 → 3 | `SAFE_NORMALIZED` | `READY` | attendance_manual_identity_and_date_replaced_with_structured_variables |
| `CONS_CIRUGIA` | CO | 3 → 4 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_CIRUGIA` | CL | 3 → 4 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_IMPLANTOLOGIA` | CO | 3 → 4 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_IMPLANTOLOGIA` | CL | 3 → 4 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_ENDODONCIA` | CO | 2 → 3 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_ENDODONCIA` | CL | 2 → 3 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_PROTESIS_FIJA` | CO | 3 → 4 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_PROTESIS_FIJA` | CL | 3 → 4 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_PROTESIS_REMOVIBLE` | CO | 3 → 4 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_PROTESIS_REMOVIBLE` | CL | 3 → 4 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_REHAB_IMPLANTES` | CO | 3 → 4 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_REHAB_IMPLANTES` | CL | 3 → 4 | `SAFE_NORMALIZED` | `READY` | procedure_blank_replaced_with_procedures.list |
| `CONS_URGENCIA` | CO | 3 → 4 | `SAFE_NORMALIZED` | `READY` | diagnosis_blank_replaced_with_treatment.diagnosis, treatment_blank_replaced_with_treatment.description |
| `CONS_URGENCIA` | CL | 3 → 4 | `SAFE_NORMALIZED` | `READY` | diagnosis_blank_replaced_with_treatment.diagnosis, treatment_blank_replaced_with_treatment.description |
| `CONS_OXIDO_NITROSO` | CO | 3 → 4 | `SAFE_NORMALIZED` | `READY` | removed_manual_identity_preamble, removed_manual_signature_and_date_block, normalized_tutor_legal_term |
| `CONS_OXIDO_NITROSO` | CL | 3 → 4 | `SAFE_NORMALIZED` | `READY` | removed_manual_identity_preamble, removed_manual_signature_and_date_block, normalized_tutor_legal_term |

## Bloqueadas

| Código | País | Motivos |
|---|---|---|
| `CONS_NO_GARANTIA` | CO | ERROR:special_workflow |
| `CONS_NO_GARANTIA` | CL | ERROR:special_workflow |
| `RECHAZO_TRATAMIENTO` | CO | ERROR:manual_blank_present, ERROR:rut_in_colombia_variant, ERROR:special_workflow |
| `RECHAZO_TRATAMIENTO` | CL | ERROR:manual_blank_present, ERROR:special_workflow |
| `CONS_APROBACION_ESTETICA` | CO | ERROR:special_workflow |
| `CONS_APROBACION_ESTETICA` | CL | ERROR:special_workflow |
| `CONS_RETIRO_ORTODONCIA` | CO | ERROR:special_workflow |
| `CONS_RETIRO_ORTODONCIA` | CL | ERROR:special_workflow |
