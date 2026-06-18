# D004B - Arquitectura Técnica
# Frontend

Versión: 1.0

## Objetivo

Definir la arquitectura del Frontend de la Plataforma de Gestión Odontológica.

El Frontend será responsable de:

- Experiencia de usuario.
- Navegación.
- Formularios.
- Visualización de información.
- Consumo de APIs.
- Gestión de estado de interfaz.

No contendrá lógica de negocio crítica.

---

# 1. Tecnologías

## Framework Principal

```text
Next.js
```

---

## Librería UI

```text
React
```

---

## Lenguaje

```text
TypeScript
```

---

## Estilos

```text
Tailwind CSS
```

---

## Manejo de Formularios

```text
React Hook Form
```

---

## Validaciones

```text
Zod
```

Las validaciones del frontend son únicamente de experiencia de usuario.

La validación oficial siempre será realizada en Backend.

---

## Consumo de API

```text
Axios
```

---

## Calendario

Se utilizará una librería React compatible con:

- Vista diaria.
- Vista semanal.
- Vista mensual.
- Drag & Drop.
- Eventos personalizados.

Opciones sugeridas:

```text
FullCalendar
```

o

```text
React Big Calendar
```

---

# 2. Principios de Diseño

## FT-001

La aplicación deberá ser:

- Intuitiva.
- Moderna.
- Profesional.

---

## FT-002

Debe ser usable por:

- Secretarias.
- Odontólogos.
- Administradores.

Sin entrenamiento técnico.

---

## FT-003

Las acciones frecuentes deberán requerir la menor cantidad posible de clics.

---

## FT-004

La aplicación deberá funcionar correctamente en:

- Portátiles.
- Monitores externos.
- Tablets.

---

## FT-005

La experiencia principal estará optimizada para escritorio.

---

# 3. Estructura del Frontend

```text
frontend/

├── app/
├── components/
├── services/
├── hooks/
├── types/
├── utils/
├── styles/
└── public/
```

---

# 4. Carpeta app

Contiene las páginas del sistema.

```text
app/

├── login/
├── dashboard/
├── agenda/
├── pacientes/
├── historia-clinica/
├── odontograma/
├── presupuestos/
├── tratamientos/
├── pagos/
├── laboratorios/
├── inventario/
├── documentos/
├── alertas/
├── reportes/
└── configuracion/
```

---

# 5. Carpeta components

Componentes reutilizables.

```text
components/

├── layout/
├── agenda/
├── pacientes/
├── tratamientos/
├── pagos/
├── laboratorios/
├── inventario/
├── reportes/
└── shared/
```

---

## Ejemplos

```text
PatientForm.tsx
PatientTable.tsx
AppointmentCard.tsx
DashboardWidget.tsx
```

---

# 6. Carpeta services

Responsable de consumir APIs.

Ejemplo:

```text
services/

patientService.ts
appointmentService.ts
treatmentService.ts
paymentService.ts
```

---

## Regla

Ningún componente deberá consumir APIs directamente.

Toda llamada deberá pasar por services.

---

# 7. Carpeta hooks

Hooks personalizados.

Ejemplos:

```text
useAuth.ts
usePermissions.ts
usePatients.ts
useAppointments.ts
```

---

# 8. Carpeta types

Tipos TypeScript.

Ejemplos:

```text
Patient.ts
Appointment.ts
Treatment.ts
Payment.ts
```

---

# 9. Carpeta utils

Funciones auxiliares.

Ejemplos:

```text
dateUtils.ts
currencyUtils.ts
validationUtils.ts
```

---

# 10. Layout General

El sistema utilizará:

```text
Sidebar Izquierdo
+
Header Superior
+
Área Principal
```

---

## Sidebar

Módulos principales:

```text
Dashboard
Agenda
Pacientes
Historia Clínica
Presupuestos
Tratamientos
Pagos
Laboratorios
Inventario
Documentos
Alertas
Reportes
Configuración
```

---

## Header

Mostrará:

- Nombre empresa.
- Usuario actual.
- Notificaciones.
- Alertas pendientes.
- Cerrar sesión.

---

# 11. Dashboard

Será la pantalla principal.

---

## Widgets Iniciales

```text
Citas Hoy
Pacientes Hoy
Pagos del Día
Tratamientos Activos
Alertas Pendientes
Laboratorios Pendientes
```

---

# 12. Módulo Pacientes

Pantallas:

```text
Listado
Detalle
Crear
Editar
Historial
```

---

## Funciones

- Búsqueda rápida.
- Filtros.
- Acceso a historia clínica.
- Acceso a tratamientos.
- Acceso a archivos.

---

# 13. Módulo Agenda

Pantallas:

```text
Diaria
Semanal
Mensual
```

---

## Funciones

- Crear cita.
- Editar cita.
- Cancelar cita.
- Reprogramar.
- Confirmar.
- Sobrecupo.

---

## Colores Sugeridos

```text
Programada  = Azul
Confirmada  = Verde
Cancelada   = Rojo
No Asistió  = Gris
Sobrecupo   = Naranja
```

---

# 14. Historia Clínica

Pantallas:

```text
Antecedentes
Evoluciones
Odontograma
Archivos
```

---

## Funciones

- Crear evolución.
- Corregir evolución.
- Consultar historial.

---

# 15. Odontograma

Debe ser interactivo.

---

## Requisitos

Permitir:

- Selección de pieza.
- Visualización de estado.
- Registro de procedimiento.
- Historial.

---

# 16. Tratamientos

Pantallas:

```text
Listado
Detalle
Etapas
Pagos
Archivos
Cierre
```

---

## Indicadores

Mostrar:

```text
Valor Total
Abonado
Saldo Pendiente
Avance %
```

---

# 17. Pagos

Pantallas:

```text
Registrar Pago
Historial
Caja
Cierre Diario
```

---

# 18. Laboratorios

Pantallas:

```text
Laboratorios
Órdenes
Seguimientos
```

---

## Indicadores

Mostrar:

```text
Pendientes
Próximos a vencer
Vencidos
Recibidos
```

---

# 19. Inventario

Pantallas:

```text
Insumos
Movimientos
Alertas
```

---

# 20. Alertas

Pantalla centralizada.

Agrupar por:

```text
Controles
Presupuestos
Laboratorios
Pagos
Inventario
```

---

# 21. Documentos

Permitir:

- Visualizar.
- Descargar.
- Generar.
- Firmar.

---

# 22. Reportes

Reportes iniciales:

```text
Ingresos
Pacientes
Tratamientos
Cartera
Laboratorios
Inventario
```

---

# 23. Manejo de Estado

Inicialmente:

```text
React Context
```

Será suficiente.

---

## Futuro

Si el crecimiento lo requiere:

```text
Zustand
```

---

# 24. Autenticación

El frontend mantendrá el Access Token JWT únicamente en memoria.

El Refresh Token se almacenará en cookie HttpOnly.

No se utilizará localStorage ni sessionStorage para tokens.

---

## Funciones

- Login.
- Logout.
- Renovación de sesión.
- Protección de rutas.
- Selección de sede autorizada.

---

# 25. Manejo de Errores

Todos los errores deberán mostrarse de forma amigable.

Ejemplo:

```text
No fue posible guardar el paciente.
Intente nuevamente.
```

No se mostrarán errores técnicos al usuario.

---

# 26. Preparación para IA

El Frontend deberá reservar espacio para futuras funciones:

- Generar evolución.
- Resumen paciente.
- Generar WhatsApp.
- Sugerencias inteligentes.

Estas funciones podrán ocultarse si IA está deshabilitada.

---

# 27. Resultado Esperado

Un frontend:

- Moderno.
- Profesional.
- Fácil de usar.
- Escalable.
- Preparado para SaaS.
- Preparado para IA.
- Adecuado para odontólogos y secretarias.
