# D007 - Seguridad y Autenticación

Versión: 1.0

## Objetivo

Definir el diseño funcional, técnico y de datos oficial para la autenticación,
autorización y gestión de sesiones de Dentia.

Este documento formaliza las decisiones aprobadas para C005. En caso de
conflicto con lineamientos anteriores sobre contraseñas, JWT, refresh tokens,
sesiones o almacenamiento de credenciales, prevalece D007.

---

# 1. Alcance

C005 deberá incluir:

- Empresas y sedes mínimas requeridas por seguridad.
- Usuarios.
- Login mediante correo y contraseña.
- Hash de contraseñas con Argon2id.
- Access Token JWT.
- Refresh Tokens rotatorios.
- Sesiones activas y múltiples sesiones simultáneas.
- Logout de una sesión y de todas las sesiones.
- Bloqueo por intentos fallidos.
- Cambio de contraseña.
- Recuperación administrativa de contraseña.
- Roles empresariales.
- Permisos.
- Alcance por sede mediante usuario_sedes.
- Protección de rutas frontend.
- Protección de endpoints backend.
- Auditoría de accesos.
- Creación segura del primer usuario administrador.
- Flujo de instalación inicial.

No incluye:

- Recuperación por correo o SMTP.
- MFA.
- Inicio de sesión social.
- SSO.
- OAuth con proveedores externos.
- Portal público de registro.

---

# 2. Principios de Seguridad

## DS-001 - Denegar por defecto

Todo acceso se considera prohibido mientras no exista autenticación, sesión,
empresa, sede y permiso válidos.

## DS-002 - Validación en Backend

El frontend podrá ocultar rutas y acciones, pero toda autorización oficial se
ejecutará en el backend.

## DS-003 - Menor privilegio

Cada usuario recibirá únicamente los roles, permisos y sedes necesarios para su
trabajo.

## DS-004 - Separación de responsabilidades

- Autenticación confirma identidad.
- Roles y permisos autorizan acciones.
- usuario_sedes limita el alcance operativo por sede.
- empresa_id define el límite principal de aislamiento.

## DS-005 - Secretos

Contraseñas, tokens completos y secretos JWT nunca se registrarán en logs,
auditoría ni respuestas de error.

---

# 3. Empresas y Sedes Mínimas

Durante C005 se crearán modelos mínimos de empresas y sedes porque todo usuario
y toda sesión deben operar dentro de un contexto empresarial.

La implementación completa de configuración de empresas y sedes continuará en
C008 y C009.

## Empresa mínima

Campos necesarios:

```text
id
nombre
slug
estado
created_at
updated_at
created_by
is_active
```

## Sede mínima

Campos necesarios:

```text
id
empresa_id
nombre
estado
created_at
updated_at
created_by
is_active
```

---

# 4. Usuarios

Cada usuario:

- Pertenece a una empresa.
- Puede tener múltiples roles.
- Puede acceder a múltiples sedes.
- Puede mantener múltiples sesiones simultáneas.
- Tiene una sede predeterminada cuando corresponde.

Estados operativos:

```text
Pendiente
Activo
Bloqueado
Suspendido
Inactivo
```

El campo is_active representa eliminación lógica. El estado representa la
condición operativa del usuario.

## Identificador de Login

Para el MVP:

```text
Correo
+
Contraseña
```

No se solicitará empresa al iniciar sesión.

El correo será único dentro de la instalación actual. La arquitectura mantendrá
empresa_id en usuarios y entidades de seguridad para permitir la evolución
futura a SaaS multiempresa.

El correo deberá normalizarse antes de comparar o aplicar restricciones de
unicidad.

---

# 5. Política de Contraseñas

## Algoritmo

Las contraseñas se almacenarán exclusivamente mediante:

```text
Argon2id
```

Nunca se almacenarán contraseñas en texto plano ni mediante cifrado reversible.

## Reglas

- Longitud mínima: 12 caracteres.
- Permitir espacios.
- Permitir Unicode.
- No exigir obligatoriamente mayúsculas, minúsculas, números o símbolos.
- No truncar silenciosamente.
- Permitir una longitud máxima mínima de 64 caracteres.
- No forzar cambios periódicos.
- Exigir cambio cuando exista recuperación administrativa o compromiso.

## Cambio de Contraseña

El cambio voluntario requiere:

- Sesión activa.
- Contraseña actual.
- Nueva contraseña.
- Confirmación de la nueva contraseña.

Después del cambio:

- Actualizar password_changed_at.
- Incrementar auth_version.
- Revocar las demás sesiones.
- Renovar la sesión actual.
- Generar auditoría.

---

# 6. Roles y Permisos

Los roles serán empresariales.

Roles iniciales:

```text
Administrador
Secretaria
Odontólogo
Odontólogo Administrador
```

Un usuario podrá tener múltiples roles simultáneamente.

Los permisos efectivos serán la unión de los permisos de sus roles activos.

Convención recomendada:

```text
recurso.accion
```

Ejemplos:

```text
users.view
users.create
users.update
users.deactivate
users.unlock
users.reset_password
users.assign_roles
users.assign_sites
roles.view
roles.manage
permissions.view
sessions.view_own
sessions.revoke_own
sessions.view_all
sessions.revoke_all
audit.view
```

---

# 7. Alcance por Sede

El acceso a sedes se manejará mediante:

```text
usuario_sedes
```

Reglas:

- La empresa es el límite principal de seguridad.
- La sede es un alcance operativo adicional.
- Los roles no cambian por sede en el MVP.
- Una sesión mantiene una sede activa.
- Un usuario solo puede seleccionar sedes asignadas.
- Cambiar de sede genera un nuevo access token.
- Cambiar de sede no requiere nueva autenticación.

## Administrador

El rol Administrador tendrá acceso automático a todas las sedes presentes y
futuras de su empresa.

Este acceso se deriva del rol y no requiere crear manualmente una fila
usuario_sedes por cada sede.

---

# 8. Sesiones y Tokens

## Access Token

Tipo:

```text
JWT
```

Duración:

```text
15 minutos
```

Claims mínimos:

```json
{
  "sub": "usuario_id",
  "sid": "sesion_id",
  "empresa_id": "empresa_id",
  "sede_id": "sede_activa_id",
  "roles": [],
  "type": "access",
  "jti": "token_id",
  "iss": "dentia-api",
  "aud": "dentia-web",
  "iat": 0,
  "nbf": 0,
  "exp": 0
}
```

El backend validará explícitamente algoritmo, firma, issuer, audience,
expiración, tipo de token, usuario, empresa y sesión.

## Refresh Token

Se implementará desde C005.

Reglas:

- Será opaco y generado criptográficamente.
- Solo se almacenará su hash.
- Rotará en cada renovación.
- Será de un solo uso.
- La reutilización de un token anterior revocará la sesión.
- Duración máxima absoluta: 8 horas.
- Expiración por inactividad: 60 minutos.

## Sesiones Simultáneas

Un usuario podrá mantener múltiples sesiones activas simultáneamente.

Cada sesión tendrá:

- Identificador independiente.
- Refresh token independiente.
- Sede activa.
- Fecha de creación.
- Última actividad.
- Fecha de expiración.
- Información básica del dispositivo.
- Estado de revocación.

---

# 9. Almacenamiento en Frontend

## Access Token

Se mantendrá únicamente en memoria.

No se almacenará en:

- localStorage.
- sessionStorage.
- Cookies accesibles mediante JavaScript.

## Refresh Token

Se almacenará en cookie:

```text
HttpOnly
SameSite=Lax
Path restringido al flujo de autenticación
Secure en producción
```

Las operaciones basadas en cookie deberán incluir protección CSRF apropiada.

---

# 10. Login

Flujo:

1. Usuario ingresa correo y contraseña.
2. Backend normaliza el correo.
3. Backend aplica controles de frecuencia.
4. Backend valida credenciales mediante Argon2id.
5. Backend verifica usuario, empresa y sedes disponibles.
6. Backend verifica bloqueo o suspensión.
7. Backend crea una sesión.
8. Backend emite access token.
9. Backend entrega refresh token mediante cookie HttpOnly.
10. Backend registra auditoría.

Mensaje genérico de fallo:

```text
Credenciales inválidas o acceso no disponible.
```

No se revelará si el correo no existe, la contraseña es incorrecta o la cuenta
está bloqueada.

---

# 11. Bloqueo por Intentos Fallidos

El sistema deberá implementar bloqueo temporal y limitación de frecuencia.

Reglas aprobadas:

- Cinco intentos fallidos consecutivos bloquearán la cuenta.
- El bloqueo tendrá una duración de 15 minutos.
- Un login exitoso reiniciará el contador.
- Un administrador autorizado podrá desbloquear la cuenta.
- No habrá bloqueo permanente automático.
- Existirá limitación adicional por IP.

---

# 12. Renovación y Logout

## Renovación

El endpoint de renovación:

1. Recibe la cookie HttpOnly.
2. Verifica su hash y sesión.
3. Verifica inactividad y expiración absoluta.
4. Rota el refresh token.
5. Emite un access token nuevo.
6. Actualiza last_seen_at.

## Logout Actual

- Revoca la sesión actual.
- Invalida el refresh token.
- Elimina la cookie.
- Registra auditoría.

## Logout Global

- Revoca todas las sesiones del usuario.
- Incrementa auth_version.
- Elimina la cookie actual.
- Registra auditoría.

---

# 13. Recuperación Administrativa

Para el MVP no se implementará recuperación por correo ni SMTP.

Un administrador con permiso users.reset_password podrá:

1. Seleccionar un usuario de su empresa.
2. Generar una contraseña temporal o credencial de recuperación de un solo uso.
3. Marcar must_change_password = true.
4. Revocar todas las sesiones existentes.
5. Entregar la credencial por un canal administrativo controlado.
6. Registrar auditoría.

La credencial temporal no podrá consultarse nuevamente después de generarse.

SMTP y recuperación autoservicio quedan para fases posteriores.

---

# 14. Protección del Frontend

Rutas públicas:

```text
/login
```

Rutas protegidas:

```text
/dashboard
/*
```

El frontend deberá:

- Restaurar la sesión mediante refresh.
- Mantener el access token en memoria.
- Redirigir al login cuando no exista sesión válida.
- Renovar el token de forma centralizada.
- Ocultar opciones sin permiso.
- Permitir seleccionar sede cuando exista más de una.
- Mostrar cambio obligatorio de contraseña cuando aplique.

La protección frontend es exclusivamente de navegación y experiencia de
usuario.

---

# 15. Protección del Backend

Todo endpoint protegido deberá validar:

1. Access token válido.
2. Sesión activa.
3. Usuario activo.
4. Empresa activa.
5. Sede activa y autorizada.
6. Permiso requerido.
7. Pertenencia del recurso a la empresa autenticada.

empresa_id y sede_id no se tomarán como autoridad desde datos enviados por el
frontend. El contexto se derivará de la sesión verificada.

---

# 16. Auditoría de Accesos

Eventos mínimos:

```text
LOGIN_SUCCESS
LOGIN_FAILED
ACCOUNT_LOCKED
ACCOUNT_UNLOCKED
LOGOUT
LOGOUT_ALL
TOKEN_REFRESHED
REFRESH_REUSE_DETECTED
PASSWORD_CHANGED
ADMIN_PASSWORD_RESET
SESSION_REVOKED
SITE_CHANGED
ACCESS_DENIED
USER_DISABLED
INITIAL_INSTALLATION
```

Datos:

```text
empresa_id
usuario_id
session_id
acción
resultado
fecha
ip_origen
user_agent
detalle controlado
```

No almacenar:

- Contraseñas.
- Access tokens completos.
- Refresh tokens.
- Tokens temporales.
- Hashes de contraseña.

---

# 17. MFA Futuro

La arquitectura deberá permitir incorporar MFA posteriormente.

El MVP no implementará:

- TOTP.
- Passkeys.
- SMS OTP.
- Códigos de recuperación MFA.

Los flujos y tablas iniciales no deberán impedir su incorporación futura.

---

# 18. Primer Usuario Administrador

La instalación inicial se realizará mediante un comando local seguro e
idempotente.

Flujo:

1. Verificar que no existan empresas ni usuarios.
2. Crear empresa inicial.
3. Crear sede principal.
4. Crear permisos base.
5. Crear roles iniciales.
6. Asignar permisos.
7. Crear primer administrador.
8. Registrar sede predeterminada.
9. Marcar instalación completada.
10. Registrar auditoría.

No existirá:

- Contraseña administrativa predeterminada.
- Endpoint público de bootstrap.
- Registro público de administradores.

---

# 19. Tablas de Seguridad

C005 requiere:

```text
empresas
sedes
usuarios
roles
permisos
usuario_roles
rol_permisos
usuario_sedes
auth_sessions
auth_attempts
auditoria_eventos
```

Las definiciones de datos oficiales se complementan en D003A y D003E.

---

# 20. Variables de Entorno

Variables previstas:

```text
JWT_SECRET
JWT_ALGORITHM
JWT_ISSUER
JWT_AUDIENCE
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_HOURS
SESSION_IDLE_TIMEOUT_MINUTES
AUTH_MAX_FAILED_ATTEMPTS
AUTH_LOCKOUT_MINUTES
COOKIE_SECURE
COOKIE_SAMESITE
```

Valores oficiales del MVP:

```text
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_HOURS = 8
SESSION_IDLE_TIMEOUT_MINUTES = 60
AUTH_MAX_FAILED_ATTEMPTS = 5
AUTH_LOCKOUT_MINUTES = 15
```

---

# 21. Casos de Uso

```text
CS001 Iniciar sesión
CS002 Renovar sesión
CS003 Cerrar sesión actual
CS004 Cerrar todas las sesiones
CS005 Cambiar contraseña
CS006 Recuperar contraseña administrativamente
CS007 Bloquear usuario temporalmente
CS008 Desbloquear usuario
CS009 Consultar sesiones activas
CS010 Revocar sesión
CS011 Cambiar sede activa
CS012 Crear primer administrador
CS013 Validar permiso
CS014 Denegar acceso entre empresas
CS015 Denegar acceso a sede no autorizada
```

---

# 22. Criterios de Aceptación

C005 se considerará completo cuando:

- El login funcione con correo y contraseña.
- Las contraseñas se almacenen con Argon2id.
- El access token expire en 15 minutos.
- El refresh token rote y expire máximo en 8 horas.
- La sesión expire tras 60 minutos de inactividad.
- El logout revoque la sesión.
- Se permitan sesiones simultáneas.
- Cinco intentos fallidos consecutivos generen un bloqueo temporal de 15
  minutos.
- Un login exitoso reinicie el contador de fallos.
- Un administrador autorizado pueda desbloquear la cuenta.
- Exista limitación adicional por IP.
- La recuperación administrativa obligue cambio de contraseña.
- Los endpoints validen empresa, sede y permiso.
- El Administrador acceda automáticamente a todas las sedes de su empresa.
- Los eventos de seguridad queden auditados.
- No exista recuperación SMTP ni MFA en el MVP.
