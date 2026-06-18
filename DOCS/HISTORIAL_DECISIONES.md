# HISTORIAL_DECISIONES

Registro de decisiones aprobadas para el proyecto Dentia.

---

## DEC-001 Nombre oficial Dentia

Dentia queda confirmado como nombre oficial y definitivo del producto.

Documento relacionado:

* D006 - Identidad Visual

---

## DEC-002 Estilo visual Clínica Moderna

El estilo visual oficial del producto será Clínica Moderna.

Lineamientos principales:

* Diseño limpio.
* Mucho espacio visual.
* Interfaz clara.
* Navegación sencilla.
* Apariencia profesional.
* Orientación a personal administrativo y clínico.

Documento relacionado:

* D006 - Identidad Visual

---

## DEC-003 Paleta verde corporativa

La paleta de verdes definida en D006 queda confirmada como estándar corporativo oficial.

Colores principales:

* Verde Clínico: `#16A34A`
* Verde Suave: `#22C55E`
* Verde Claro: `#BBF7D0`
* Fondo Principal: `#F8FAFC`
* Texto Principal: `#1F2937`

Documento relacionado:

* D006 - Identidad Visual

---

## DEC-004 Reprogramación de citas

La reprogramación de citas se manejará así:

* La cita original cambia a estado Reprogramada.
* Se crea una nueva cita.
* Ambas quedan relacionadas mediante cita_historial.
* Debe conservarse trazabilidad completa.

Documentos relacionados:

* D002 - Reglas de Negocio
* D002A - Casos de Uso Operativos

---

## DEC-005 Sobrecupos

Los sobrecupos podrán ser creados por:

* Secretaria.
* Administrador.
* Odontólogo Administrador.

Un odontólogo sin privilegios administrativos no podrá crear sobrecupos.

Los sobrecupos se visualizarán en color naranja en la agenda.

Documentos relacionados:

* D002 - Reglas de Negocio
* D002A - Casos de Uso Operativos

---

## DEC-006 Consentimientos MVP

El MVP incluirá:

* Consentimiento informado.
* Protección de datos.

No se requiere firma electrónica certificada para el MVP.

Los documentos legales avanzados se mantienen en fases posteriores.

Documentos relacionados:

* D002 - Reglas de Negocio
* D002A - Casos de Uso Operativos
* D005 - Roadmap Desarrollo

---

## DEC-007 WhatsApp MVP

El alcance de WhatsApp en el MVP será:

* Generar mensaje.
* Abrir WhatsApp Web.

No se incluye:

* WhatsApp Business API.
* Envíos automáticos.

Documentos relacionados:

* D002 - Reglas de Negocio
* D002A - Casos de Uso Operativos

---

## DEC-008 Argon2id

Las contraseñas de Dentia se almacenarán mediante Argon2id.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-009 Política de contraseñas

La política oficial será:

* Mínimo 12 caracteres.
* Permitir espacios y Unicode.
* No exigir combinaciones artificiales.
* No forzar cambios periódicos.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-010 Sesiones y tokens

La sesión utilizará:

* Access Token JWT de 15 minutos.
* Refresh Token de máximo 8 horas.
* Expiración por inactividad de 60 minutos.
* Refresh Tokens implementados desde C005.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-011 Almacenamiento de tokens

El Access Token se mantendrá en memoria.

El Refresh Token se almacenará en cookie HttpOnly.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-012 Login del MVP

El MVP solicitará únicamente:

* Correo.
* Contraseña.

No solicitará empresa. El correo será único dentro de la instalación actual y
la arquitectura conservará preparación multiempresa.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-013 Roles y sedes

Los roles serán empresariales.

El alcance por sede se controlará separadamente mediante usuario_sedes.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-014 Empresas y sedes mínimas en C005

C005 incluirá modelos mínimos de empresa y sede requeridos por el contexto de
seguridad. La gestión funcional completa continúa en C008 y C009.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-015 Recuperación administrativa MVP

La recuperación de contraseña será administrativa durante el MVP.

SMTP y recuperación por correo quedan para fases posteriores.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-016 Sesiones simultáneas

Dentia permitirá múltiples sesiones activas simultáneas por usuario.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-017 MFA futuro

La arquitectura quedará preparada para MFA, pero MFA no se implementará en el
MVP.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-018 Cambio de sede

Cambiar de sede activa generará un nuevo Access Token y no requerirá nueva
autenticación.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-019 Acceso del Administrador a sedes

El rol Administrador tendrá acceso automático a todas las sedes presentes y
futuras de su empresa.

Documento relacionado:

* D007 - Seguridad y Autenticación

---

## DEC-020 Bloqueo por intentos fallidos

La política de bloqueo de autenticación será:

* Cinco fallos consecutivos bloquean la cuenta durante 15 minutos.
* Un login exitoso reinicia el contador.
* No existe bloqueo permanente automático.
* Un administrador autorizado puede desbloquear la cuenta.
* Se aplica limitación adicional por IP.

Documento relacionado:

* D007 - Seguridad y Autenticación
