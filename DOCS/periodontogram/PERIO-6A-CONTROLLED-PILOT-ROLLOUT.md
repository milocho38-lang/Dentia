# PERIO-6A — Integración y rollout controlado del piloto

## Objetivo

Publicar el MVP de Periodontograma sin habilitarlo automáticamente a todos los
odontólogos. El acceso operativo exige simultáneamente permisos clínicos,
alcance tenant/sede y dos gates explícitos administrados por plataforma:

1. empresa habilitada para el piloto;
2. odontólogo autorizado para el piloto.

Este mecanismo no representa pricing, billing ni cupos comerciales.

## Modelo

- `periodontogram_pilot_company_gates`: habilitación lógica por empresa. La
  ausencia de fila equivale a módulo deshabilitado.
- `periodontogram_pilot_dentist_authorizations`: autorizaciones históricas por
  odontólogo. Una revocación marca la autorización como inactiva y conserva
  actor y fecha.
- `periodontal_exams`, sus versiones, snapshots, hashes, gráficos y vínculos a
  evolución no se modifican al deshabilitar o revocar el piloto.

No se crean registros de habilitación para empresas existentes durante la
migración.

## Resolución de acceso clínico

Todo endpoint PERIO vuelve a comprobar en backend:

- usuario activo;
- perfil odontológico activo y vinculado al usuario;
- pertenencia al mismo tenant;
- sede activa y autorizada para usuario y odontólogo;
- permiso clínico PERIO requerido por el endpoint;
- gate de empresa activo;
- autorización piloto activa para el odontólogo.

La pestaña de paciente consulta el mismo resolver y se oculta cuando el acceso
no está disponible. Esta ocultación es únicamente UX: el backend continúa
siendo la frontera de seguridad.

## Administración de plataforma

La ficha de empresa incluye **Módulos / Pilotos → Periodontograma** para:

- habilitar o deshabilitar la empresa;
- consultar odontólogos de la empresa;
- autorizar o revocar individualmente odontólogos activos.

Los permisos `periodontogram.pilot.view` y
`periodontogram.pilot.manage` pertenecen exclusivamente a `PLATFORM_ADMIN`.
No conceden `periodontogram.view` ni otro permiso clínico, por lo cual un
administrador de plataforma no puede consultar exámenes periodontales.

La auditoría administrativa registra únicamente identificadores operativos,
actor, tenant, fecha y acción. No incluye mediciones ni contenido clínico.

## Migraciones

Cadena integrada sobre el head productivo verificado:

```text
20260921_0041
→ 20260922_0042
→ 20260923_0043
→ 20260923_0044
→ 20260926_0045
```

`0045` crea exclusivamente los gates del piloto y sus permisos RBAC. El estado
inicial es deshabilitado para todas las empresas y sin odontólogos autorizados.

## Rollout

Antes del deploy se obtiene en modo read-only la lista de candidatos del tenant
chileno. La empresa y el odontólogo se habilitan únicamente después de una
confirmación humana explícita. No se infiere ni se activa un candidato durante
la integración.

Para retirar el piloto:

1. revocar la autorización del odontólogo o deshabilitar la empresa;
2. comprobar que el acceso operativo queda denegado;
3. conservar intacto todo el histórico clínico.

## Validación mínima

- módulo deshabilitado: acceso denegado;
- empresa habilitada sin autorización individual: acceso denegado;
- odontólogo autorizado, activo y con scope válido: acceso permitido;
- otro odontólogo del mismo tenant: acceso denegado;
- odontólogo de otro tenant: acceso denegado;
- Platform Admin administra gates sin acceso clínico;
- revocación/deshabilitación no elimina histórico;
- frontend oculta la pestaña cuando el resolver deniega;
- migraciones reversibles y un único head Alembic.
