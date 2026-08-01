# C019A.2 — Reporte de pruebas de instancias de consentimiento

## Cobertura implementada

Las pruebas PostgreSQL cubren:

- plantillas aplicables y selección múltiple;
- batch atómico y consecutivo por empresa;
- snapshots de procedimiento y versión;
- preview sin semántica de envío o firma;
- revisión profesional y control optimista;
- inmutabilidad posterior;
- bloqueo contractual de `PENDING_SIGNATURE`;
- detección de alteración del contenido sellado;
- datos faltantes y bloqueo de confirmación;
- anulación sin borrado;
- `SECRETARY`, `ADMINISTRATOR`, `DENTIST_ADMIN` y `PLATFORM_ADMIN`;
- aislamiento empresa A/B y alcance de sede;
- auditoría.

La caracterización frontend verifica integración en el paciente, asistente, selección múltiple, preview, textos humanos, permisos, doble-submit, revisión, anulación y ausencia de acciones de firma, OTP, QR, envío o portal.

## Resultados de la ejecución local

- Compilación Python: OK.
- Frontend lint: OK.
- Frontend build: OK.
- DB-backed PostgreSQL 17: 53 aprobadas.
- Caracterización C018R.4: 217 rutas, 0 pendientes, 70/70 mutaciones críticas DB-backed.
- Hardening: `pilot-hardening-tests OK`; fechas y zonas horarias 14 aprobadas.

- Suite oficial `--full`: OK (caracterización + DB-backed + hardening).
- Scripts frontend de consentimientos, integración clínica-comercial, Dental Inspector y orientación clásica: OK.
- Alembic: `0024 (head)`, `check` sin operaciones nuevas y ciclo `0024 → 0023 → 0024` correcto.
- Dependencias Python (`pip check`): sin requisitos rotos.

## Riesgos y límites

- La especialidad y el registro profesional provienen de la configuración institucional disponible; el modelo actual no los almacena por odontólogo.
- El tratamiento actual no expone diagnóstico clínico ni número de plan confiable. Esas variables se marcan faltantes.
- La validación jurídica de textos, menores, representación y firma no forma parte de C019A.2.
- Las advertencias de deprecación de FastAPI/Starlette bajo Python 3.14 son preexistentes y no afectan el resultado.
