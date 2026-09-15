# ORT-1 — Entitlement y cupos de Ortodoncia por odontólogo

## Alcance

ORT-1 introduce únicamente la habilitación comercial del módulo, el límite de cupos, la asignación lógica a odontólogos y un resolver central de acceso. No crea fichas, casos, evoluciones ni contenido clínico de Ortodoncia.

## Modelo

- `orthodontics_entitlements`: un registro opcional por empresa. La ausencia equivale a módulo desactivado y cero cupos.
- `orthodontics_dentist_assignments`: asignación histórica tenant-scoped. Retirar un cupo marca la asignación como inactiva; nunca elimina historia clínica.
- Un cupo se consume solo cuando asignación, odontólogo y usuario vinculado están activos.
- El límite se protege con bloqueo de fila del entitlement y un índice único parcial evita dos asignaciones activas al mismo odontólogo.

Las empresas existentes quedan desactivadas y sin asignaciones. No hay habilitación automática ni lógica de precios.

## RBAC

| Rol | Entitlement | Asignaciones | Acceso clínico derivado |
|---|---|---|---|
| PLATFORM_ADMIN | ver/administrar | no | no |
| ADMINISTRATOR | ver | ver/administrar | no |
| DENTIST_ADMIN | ver | ver/administrar | solo si está asignado y cumple scope clínico |
| DENTIST | no | no | solo si está asignado y cumple scope clínico |
| SECRETARY | no | no | no |

No existe `orthodontics.module.access`: el resolver exige entitlement vigente, asignación activa, usuario y perfil odontológico activos, tenant coincidente, `clinical.view` y sede clínica activa.

## Seguridad y auditoría

- Plataforma gestiona el add-on sin entrar al contexto clínico del tenant.
- Las APIs tenant derivan siempre `company_id` de la sesión.
- Un odontólogo extranjero, inactivo o sin usuario activo no puede asignarse.
- Reducir el límite por debajo de cupos activos se rechaza.
- Se auditan habilitación, deshabilitación, cambio de límite, asignación y retiro.
- Desactivar al usuario o retirar su capacidad odontológica revoca lógicamente su asignación.

## Fuera de alcance

Pricing, cobro, casos, ficha ortodóncica, diagnósticos, evoluciones, aparatología y documentos clínicos pertenecen a fases posteriores.
