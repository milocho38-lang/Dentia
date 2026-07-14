from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDefinition:
    code: str
    name: str
    module: str
    description: str


@dataclass(frozen=True)
class RoleDefinition:
    code: str
    name: str
    description: str
    permission_codes: frozenset[str]


PERMISSIONS = (
    PermissionDefinition("dashboard.view", "Ver dashboard", "dashboard", "Consultar el dashboard operativo."),
    PermissionDefinition("users.view", "Ver usuarios", "security", "Consultar usuarios de la empresa."),
    PermissionDefinition("users.create", "Crear usuarios", "security", "Crear usuarios en la empresa."),
    PermissionDefinition("users.update", "Actualizar usuarios", "security", "Modificar datos y estado de usuarios."),
    PermissionDefinition("users.deactivate", "Desactivar usuarios", "security", "Desactivar usuarios mediante eliminación lógica."),
    PermissionDefinition("users.unlock", "Desbloquear usuarios", "security", "Retirar bloqueos temporales de autenticación."),
    PermissionDefinition("users.reset_password", "Restablecer contraseñas", "security", "Ejecutar recuperación administrativa de contraseña."),
    PermissionDefinition("users.assign_roles", "Asignar roles", "security", "Asignar o retirar roles empresariales."),
    PermissionDefinition("users.assign_sites", "Asignar sedes", "security", "Asignar o retirar sedes disponibles."),
    PermissionDefinition("roles.view", "Ver roles", "security", "Consultar roles empresariales."),
    PermissionDefinition("roles.manage", "Administrar roles", "security", "Crear y modificar roles empresariales."),
    PermissionDefinition("permissions.view", "Ver permisos", "security", "Consultar el catálogo de permisos."),
    PermissionDefinition("company.view", "Ver empresa", "organization", "Consultar la empresa actual."),
    PermissionDefinition("company.update", "Actualizar empresa", "organization", "Modificar la configuración de la empresa."),
    PermissionDefinition("branding.view", "Ver personalización", "organization", "Consultar identidad visual y datos documentales de la empresa."),
    PermissionDefinition("branding.update", "Actualizar personalización", "organization", "Modificar identidad visual, textos documentales, colores, logo y firma."),
    PermissionDefinition("sites.view", "Ver sedes", "organization", "Consultar sedes de la empresa."),
    PermissionDefinition("sites.manage", "Administrar sedes", "organization", "Crear, modificar, activar e inactivar sedes."),
    PermissionDefinition("sessions.view_own", "Ver sesiones propias", "security", "Consultar sesiones propias."),
    PermissionDefinition("sessions.revoke_own", "Revocar sesiones propias", "security", "Cerrar sesiones propias."),
    PermissionDefinition("sessions.view_all", "Ver todas las sesiones", "security", "Consultar sesiones de usuarios de la empresa."),
    PermissionDefinition("sessions.revoke_all", "Revocar cualquier sesión", "security", "Revocar sesiones de usuarios de la empresa."),
    PermissionDefinition("audit.view", "Ver auditoría", "security", "Consultar eventos de auditoría autorizados."),
    PermissionDefinition("patients.view", "Ver pacientes", "patients", "Consultar pacientes y su expediente."),
    PermissionDefinition("patients.create", "Crear pacientes", "patients", "Registrar pacientes."),
    PermissionDefinition("patients.update", "Actualizar pacientes", "patients", "Modificar información de pacientes."),
    PermissionDefinition("patients.deactivate", "Desactivar pacientes", "patients", "Desactivar y reactivar pacientes con validación de agenda."),
    PermissionDefinition("appointments.view", "Ver agenda", "appointments", "Consultar citas y agenda."),
    PermissionDefinition("appointments.create", "Crear citas", "appointments", "Programar citas."),
    PermissionDefinition("appointments.update", "Actualizar citas", "appointments", "Editar, confirmar y reprogramar citas."),
    PermissionDefinition("appointments.cancel", "Cancelar citas", "appointments", "Cancelar citas con trazabilidad."),
    PermissionDefinition("appointments.overbook", "Crear sobrecupos", "appointments", "Crear citas marcadas como sobrecupo."),
    PermissionDefinition("appointments.complete", "Finalizar atención", "appointments", "Registrar cierre básico de atención y marcar citas atendidas."),
    PermissionDefinition("followups.view", "Ver seguimientos", "followups", "Consultar controles y seguimientos operativos."),
    PermissionDefinition("followups.manage", "Gestionar seguimientos", "followups", "Cerrar, reabrir y vincular citas de seguimiento."),
    PermissionDefinition("followups.contact", "Contactar pacientes", "followups", "Registrar contactos y generar mensajes manuales."),
    PermissionDefinition("followups.view_clinical_summary", "Ver resumen de atención", "followups", "Consultar descripción de atención y medicamentos informativos."),
    PermissionDefinition("clinical.view", "Ver historia clínica", "clinical", "Consultar información clínica autorizada."),
    PermissionDefinition("clinical.update", "Actualizar historia clínica", "clinical", "Registrar historia y evoluciones clínicas."),
    PermissionDefinition("clinical_records.view", "Ver resumen clínico", "clinical", "Consultar existencia de historia y alertas clínicas operativas."),
    PermissionDefinition("clinical_records.create", "Abrir historia clínica", "clinical", "Crear la historia clínica longitudinal de un paciente."),
    PermissionDefinition("clinical_records.update_draft", "Actualizar borrador clínico", "clinical", "Modificar información clínica base antes de evoluciones firmadas."),
    PermissionDefinition("clinical_records.view_sensitive", "Ver detalle clínico sensible", "clinical", "Consultar antecedentes, alergias, medicamentos y contenido clínico sensible."),
    PermissionDefinition("clinical_records.audit", "Auditar historia clínica", "clinical", "Consultar trazabilidad clínica autorizada."),
    PermissionDefinition("clinical_evolutions.view", "Ver evoluciones clínicas", "clinical", "Consultar evoluciones clínicas autorizadas."),
    PermissionDefinition("clinical_evolutions.create", "Crear evoluciones clínicas", "clinical", "Crear borradores de evolución clínica."),
    PermissionDefinition("clinical_evolutions.update_draft", "Actualizar borrador de evolución", "clinical", "Editar borradores de evolución clínica."),
    PermissionDefinition("clinical_evolutions.sign", "Firmar evoluciones clínicas", "clinical", "Firmar y cerrar evoluciones clínicas."),
    PermissionDefinition("clinical_evolutions.add_addendum", "Agregar adendas clínicas", "clinical", "Agregar adendas a evoluciones clínicas firmadas."),
    PermissionDefinition("clinical_timeline.view", "Ver línea de tiempo clínica", "clinical", "Consultar la línea de tiempo clínica del paciente."),
    PermissionDefinition("odontogram.view", "Ver odontograma", "odontogram", "Consultar odontograma e historial."),
    PermissionDefinition("odontogram.update", "Actualizar odontograma", "odontogram", "Registrar estados y eventos odontológicos."),
    PermissionDefinition("budgets.view", "Ver presupuestos", "budgets", "Consultar presupuestos."),
    PermissionDefinition("budgets.create", "Crear presupuestos", "budgets", "Generar presupuestos."),
    PermissionDefinition("budgets.update", "Actualizar presupuestos", "budgets", "Modificar y gestionar presupuestos."),
    PermissionDefinition("treatments.view", "Ver tratamientos", "treatments", "Consultar tratamientos."),
    PermissionDefinition("treatments.create", "Crear tratamientos", "treatments", "Crear tratamientos."),
    PermissionDefinition("treatments.update", "Actualizar tratamientos", "treatments", "Gestionar etapas y procedimientos."),
    PermissionDefinition("treatments.close", "Cerrar tratamientos", "treatments", "Finalizar tratamientos y registrar cierre."),
    PermissionDefinition("treatments.cancel", "Cancelar tratamientos", "treatments", "Cancelar tratamientos con trazabilidad."),
    PermissionDefinition("procedure_catalog.view", "Ver catálogo de procedimientos", "treatments", "Consultar el catálogo de procedimientos de la empresa."),
    PermissionDefinition("procedure_catalog.manage", "Administrar catálogo de procedimientos", "treatments", "Crear, editar, activar e inactivar procedimientos del catálogo."),
    PermissionDefinition("payments.view", "Ver pagos", "finance", "Consultar pagos y cartera."),
    PermissionDefinition("payments.create", "Registrar pagos", "finance", "Registrar pagos de pacientes."),
    PermissionDefinition("payments.reverse", "Reversar pagos", "finance", "Reversar pagos con auditoría."),
    PermissionDefinition("finance.dashboard.view", "Ver dashboard financiero", "finance", "Consultar indicadores económicos básicos."),
    PermissionDefinition("cash.view", "Ver caja", "finance", "Consultar movimientos de caja."),
    PermissionDefinition("cash.close", "Cerrar caja", "finance", "Realizar cierre diario de caja."),
    PermissionDefinition("documents.view", "Ver documentos", "documents", "Consultar documentos autorizados."),
    PermissionDefinition("documents.manage", "Administrar documentos", "documents", "Generar y gestionar documentos."),
    PermissionDefinition("reports.view", "Ver reportes", "reports", "Consultar reportes autorizados."),
    PermissionDefinition("platform.companies.view", "Ver empresas de plataforma", "platform", "Consultar empresas administradas por la plataforma."),
    PermissionDefinition("platform.companies.manage", "Administrar empresas de plataforma", "platform", "Crear, activar e inactivar empresas desde plataforma."),
)

ALL_PERMISSION_CODES = frozenset(permission.code for permission in PERMISSIONS)
PLATFORM_PERMISSION_CODES = frozenset(
    {
        "platform.companies.view",
        "platform.companies.manage",
    }
)
CLINICAL_SENSITIVE_PERMISSION_CODES = frozenset(
    {
        "clinical_records.create",
        "clinical_records.update_draft",
        "clinical_records.view_sensitive",
        "clinical_records.audit",
        "clinical_evolutions.view",
        "clinical_evolutions.create",
        "clinical_evolutions.update_draft",
        "clinical_evolutions.sign",
        "clinical_evolutions.add_addendum",
        "clinical_timeline.view",
    }
)
CLINIC_ADMIN_PERMISSION_CODES = (
    ALL_PERMISSION_CODES - PLATFORM_PERMISSION_CODES - CLINICAL_SENSITIVE_PERMISSION_CODES
)

SECRETARY_PERMISSIONS = frozenset(
    {
        "dashboard.view",
        "patients.view",
        "patients.create",
        "patients.update",
        "appointments.view",
        "appointments.create",
        "appointments.update",
        "appointments.cancel",
        "appointments.overbook",
        "followups.view",
        "followups.manage",
        "followups.contact",
        "budgets.view",
        "budgets.update",
        "treatments.view",
        "procedure_catalog.view",
        "finance.dashboard.view",
        "payments.view",
        "payments.create",
        "cash.view",
        "cash.close",
        "documents.view",
        "clinical_records.view",
        "sessions.view_own",
        "sessions.revoke_own",
    }
)

DENTIST_PERMISSIONS = frozenset(
    {
        "dashboard.view",
        "patients.view",
        "patients.create",
        "patients.update",
        "appointments.view",
        "appointments.complete",
        "followups.view",
        "followups.manage",
        "followups.contact",
        "followups.view_clinical_summary",
        "clinical.view",
        "clinical.update",
        "clinical_records.view",
        "clinical_records.create",
        "clinical_records.update_draft",
        "clinical_records.view_sensitive",
        "clinical_evolutions.view",
        "clinical_evolutions.create",
        "clinical_evolutions.update_draft",
        "clinical_evolutions.sign",
        "clinical_evolutions.add_addendum",
        "clinical_timeline.view",
        "odontogram.view",
        "odontogram.update",
        "budgets.view",
        "budgets.create",
        "budgets.update",
        "treatments.view",
        "treatments.create",
        "treatments.update",
        "treatments.close",
        "procedure_catalog.view",
        "documents.view",
        "documents.manage",
        "sessions.view_own",
        "sessions.revoke_own",
    }
)

DENTIST_ADMIN_PERMISSIONS = SECRETARY_PERMISSIONS | DENTIST_PERMISSIONS | frozenset(
    {
        "company.view",
        "company.update",
        "sites.view",
        "sites.manage",
        "users.view",
        "users.create",
        "users.update",
        "users.unlock",
        "users.reset_password",
        "users.assign_sites",
        "patients.deactivate",
        "clinical_records.audit",
        "clinical_records.view",
        "clinical_records.create",
        "clinical_records.update_draft",
        "clinical_records.view_sensitive",
        "clinical_evolutions.view",
        "clinical_evolutions.create",
        "clinical_evolutions.update_draft",
        "clinical_evolutions.sign",
        "clinical_evolutions.add_addendum",
        "clinical_timeline.view",
        "treatments.cancel",
        "procedure_catalog.view",
        "procedure_catalog.manage",
        "payments.reverse",
        "reports.view",
    }
)

ROLES = (
    RoleDefinition(
        "ADMINISTRATOR",
        "Administrador",
        "Administración completa de la empresa y sus sedes.",
        CLINIC_ADMIN_PERMISSION_CODES,
    ),
    RoleDefinition(
        "PLATFORM_ADMIN",
        "Administrador de plataforma",
        "Administración de empresas y clínicas de la plataforma.",
        PLATFORM_PERMISSION_CODES,
    ),
    RoleDefinition(
        "SECRETARY",
        "Secretaria",
        "Operación administrativa diaria del consultorio.",
        SECRETARY_PERMISSIONS,
    ),
    RoleDefinition(
        "DENTIST",
        "Odontólogo",
        "Operación clínica y seguimiento de tratamientos.",
        DENTIST_PERMISSIONS,
    ),
    RoleDefinition(
        "DENTIST_ADMIN",
        "Odontólogo Administrador",
        "Operación clínica con configuración administrativa básica.",
        DENTIST_ADMIN_PERMISSIONS,
    ),
)


def validate_security_catalog() -> None:
    permission_codes = [permission.code for permission in PERMISSIONS]
    role_codes = [role.code for role in ROLES]

    if len(permission_codes) != len(set(permission_codes)):
        raise ValueError("The permission catalog contains duplicate codes.")

    if len(role_codes) != len(set(role_codes)):
        raise ValueError("The role catalog contains duplicate codes.")

    unknown_permissions = {
        permission_code
        for role in ROLES
        for permission_code in role.permission_codes
        if permission_code not in ALL_PERMISSION_CODES
    }
    if unknown_permissions:
        raise ValueError(
            "Roles reference unknown permissions: "
            + ", ".join(sorted(unknown_permissions))
        )
