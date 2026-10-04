# PERIO-7 — Liberación clínica general

## Decisión

Periodontograma deja el piloto controlado y pasa a estar disponible para todo
usuario clínico elegible. La liberación no concede permisos nuevos: el acceso
continúa limitado a `DENTIST` y `DENTIST_ADMIN` mediante los permisos
`periodontogram.*` ya existentes.

## Resolución de acceso

Cada endpoint mantiene su permiso específico y el backend vuelve a comprobar:

- usuario y empresa activos;
- perfil `Dentist` activo, vinculado al usuario y perteneciente al mismo tenant;
- sede seleccionada autorizada para el usuario;
- asignación `DentistSite` activa en esa sede.

`ADMINISTRATOR`, `SECRETARY` y `PLATFORM_ADMIN` no obtienen acceso clínico por
esta transición. En particular, los permisos administrativos históricos del
piloto no conceden `periodontogram.view` ni evitan las fronteras de tenant/sede.

La UI consulta `/api/periodontograms/access` como resolver general para decidir
la visibilidad de navegación y deep links. Esa consulta es solo UX; todos los
endpoints clínicos vuelven a aplicar las validaciones en backend.

## Configuración histórica

Se conservan sin reescritura:

- `periodontogram_pilot_company_gates`;
- `periodontogram_pilot_dentist_authorizations`;
- modelos ORM, migración `20260926_0045` y eventos de auditoría existentes;
- actores, fechas, revocaciones y motivos registrados durante el piloto.

Esos datos ya no habilitan ni deniegan el acceso normal. Las rutas y controles
activos de administración del piloto se retiran. Los permisos
`periodontogram.pilot.*` permanecen inertes para evitar una migración destructiva
o una limpieza global sin beneficio clínico.

## Sin migración

La transición no cambia el esquema ni requiere backfill. No se modifican
exámenes, versiones, snapshots, hashes, filas de captura, gráficos ni vínculos a
evoluciones. Las reglas de borrador, finalización, corrección, inmutabilidad,
concurrencia, auditoría, tenant y sede permanecen intactas.

## Regresión obligatoria

- acceso general de `DENTIST` y `DENTIST_ADMIN` sin filas piloto;
- gates deshabilitados y autorizaciones revocadas históricas no bloquean;
- roles no clínicos, plataforma, cross-tenant e IDOR siguen denegados;
- identidad odontológica y `DentistSite` continúan siendo obligatorios;
- navegación y deep links reflejan el resolver general;
- CRUD, historial, correcciones, concurrencia y evoluciones conservan contratos;
- identidades, snapshots y hashes históricos permanecen byte-semánticamente
  iguales después de lecturas y de la transición de acceso.

Este documento no autoriza push ni deploy.
