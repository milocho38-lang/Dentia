# D002 - Reglas de Negocio

Versión: 1.0

## 1. Estructura Organizacional

### RN-001

El sistema deberá permitir:

* Un odontólogo en múltiples consultorios o sedes.
* Múltiples odontólogos en una misma sede.
* Múltiples sedes por empresa.

---

### RN-002

Toda cita deberá estar asociada a:

* Paciente.
* Odontólogo.
* Sede.
* Fecha.
* Hora.

---

## 2. Pacientes

### RN-003

El paciente se registrará una única vez por empresa.

Si cambia de sede o especialista:

* Mantendrá la misma historia clínica.
* Mantendrá los mismos tratamientos.
* Mantendrá el mismo historial financiero.

---

### RN-004

Campos mínimos obligatorios:

* Nombres.
* Apellidos.
* Documento.
* Celular.

---

### RN-005

No podrán existir dos pacientes con el mismo documento dentro de la misma empresa.

---

## 3. Agenda

### RN-006

Estados posibles de una cita:

* Programada.
* Confirmada.
* Atendida.
* Cancelada.
* No asistió.
* Reprogramada.

---

### RN-007

El sistema deberá verificar conflictos de agenda para cada odontólogo.

Cuando se intente crear una cita en un horario donde ya exista una cita programada para el mismo odontólogo, el sistema deberá mostrar una advertencia indicando:

* Paciente existente.
* Hora.
* Tipo de cita.
* Duración estimada.

El usuario podrá:

* Cancelar.
* Reprogramar.
* Crear la cita como sobrecupo.

---

### RN-007A

Las citas creadas bajo esta condición deberán marcarse como:

```text
Sobrecupo = Sí
```

---

### RN-007B

Las citas con sobrecupo deberán visualizarse con una marca visual diferenciada.

---

### RN-007C

El sistema deberá permitir consultar y reportar citas registradas como sobrecupo.

---

### RN-008

No podrán existir dos citas simultáneas para el mismo paciente.

---

### RN-009

Toda cancelación deberá registrar motivo.

Ejemplos:

* Solicitud del paciente.
* Solicitud del consultorio.
* Emergencia.
* Falta de pago.
* Otro.

---

### RN-010

Toda reprogramación deberá conservar historial.

El sistema deberá almacenar:

* Fecha original.
* Fecha nueva.
* Motivo.
* Usuario responsable.

---

## 4. Valoración Inicial

### RN-011

La valoración inicial genera una atención clínica independiente.

---

### RN-012

La valoración podrá generar:

* Alta sin tratamiento.
* Plan de tratamiento.
* Remisión.

---

### RN-013

La valoración podrá tener costo independiente.

---

## 5. Historia Clínica

### RN-014

Toda atención clínica deberá generar evolución.

---

### RN-015

Las evoluciones no podrán eliminarse.

Solo podrán:

* Corregirse.
* Anularse.

Con trazabilidad completa.

---

### RN-016

Toda modificación deberá registrar:

* Usuario.
* Fecha.
* Hora.
* Motivo.

---

## 6. Odontograma

### RN-017

Cada pieza dental deberá tener historial.

---

### RN-018

Todo procedimiento deberá quedar asociado a la pieza correspondiente cuando aplique.

---

### RN-019

El odontograma deberá permitir visualizar:

* Estado actual.
* Estado histórico.

---

## 7. Presupuestos

### RN-020

Un paciente podrá tener múltiples presupuestos.

---

### RN-021

Estados posibles:

* Borrador.
* Entregado.
* En seguimiento.
* Aceptado.
* Rechazado.
* Vencido.

---

### RN-022

Un presupuesto aceptado podrá convertirse en tratamiento.

---

## 8. Tratamientos

### RN-023

Todo tratamiento pertenece a un paciente.

---

### RN-024

Un tratamiento podrá tener una o varias citas.

---

### RN-025

Estados posibles:

* Planeado.
* Activo.
* Suspendido.
* Finalizado.
* Cancelado.

---

### RN-026

El sistema deberá mostrar:

* Citas realizadas.
* Citas pendientes.
* Porcentaje de avance.

---

### RN-027

Todo tratamiento deberá mostrar:

* Valor total.
* Valor abonado.
* Saldo pendiente.

---

## 9. Pagos

### RN-028

El sistema permitirá:

* Pago de valoración.
* Anticipos.
* Abonos.
* Pago total.

---

### RN-029

Cada pago deberá registrar:

* Fecha.
* Valor.
* Medio de pago.
* Usuario.

---

### RN-030

Medios de pago iniciales:

* Efectivo.
* Tarjeta débito.
* Tarjeta crédito.
* Transferencia.
* Nequi.
* Daviplata.
* Otro.

---

### RN-031

Los pagos no podrán eliminarse.

Solo podrán reversarse mediante ajuste auditado.

---

## 10. Caja

### RN-032

Todo ingreso deberá impactar caja.

---

### RN-033

Toda modificación financiera deberá generar auditoría.

---

### RN-034

El sistema deberá permitir cierre diario de caja.

---

## 11. WhatsApp

### RN-035

El sistema permitirá envío manual de mensajes.

---

### RN-036

Plantillas iniciales:

* Confirmación de cita.
* Recordatorio de cita.
* Presupuesto pendiente.
* Pago pendiente.
* Control pendiente.
* Laboratorio listo.

---

## 12. Reportes

### RN-037

Reportes mínimos:

* Ingresos diarios.
* Ingresos mensuales.
* Pacientes nuevos.
* Tratamientos activos.
* Cartera pendiente.

---

## 13. Auditoría

### RN-038

Toda acción crítica deberá registrar:

* Usuario.
* Fecha.
* Hora.
* Acción ejecutada.

---

## 14. Seguridad

### RN-039

Los usuarios solo podrán acceder a información autorizada según sus permisos.

---

### RN-040

Toda sesión requerirá autenticación.

---

## 15. Confirmación de Citas

### RN-041

Las citas podrán registrarse como:

* Confirmada por WhatsApp.
* Confirmada por llamada.
* Confirmada presencialmente.
* Sin confirmar.

---

## 16. Pacientes Ausentes

### RN-042

El sistema deberá registrar inasistencias.

Se deberá conservar historial para análisis posterior.

---

## 17. Cierre y Conformidad de Tratamientos

### RN-043

Todo tratamiento finalizado deberá tener cierre formal.

---

### RN-044

El sistema deberá permitir registrar conformidad del paciente mediante:

* Firma digital.
* Documento firmado.
* Confirmación registrada.

---

### RN-045

Estados posibles:

* Conforme.
* Conforme con observaciones.
* No conforme.

---

### RN-046

El cierre no podrá eliminarse.

Solo podrán agregarse notas aclaratorias.

---

### RN-047

El sistema deberá permitir generar documento de cierre de tratamiento.

---

## 18. Alertas de Control

### RN-048

El sistema deberá generar alertas automáticas para controles periódicos.

---

### RN-049

Cada procedimiento podrá definir una periodicidad sugerida.

Ejemplos:

* Profilaxis: 6 meses.
* Ortodoncia: 30 días.
* Retenedor: 3 a 6 meses.
* Postoperatorio: según configuración.

---

### RN-050

Estados posibles de seguimiento:

* Próximo a control.
* Control vencido.
* Contactado.
* Cita programada.
* Cerrado sin cita.
* No desea continuar.

---

### RN-051

Desde una alerta deberá ser posible:

* Programar cita.
* Enviar WhatsApp.
* Registrar contacto.
* Registrar observaciones.

---

### RN-052

El dashboard deberá mostrar alertas de control.

---

### RN-053

El sistema deberá generar reportes de seguimiento.

---

### RN-054

Toda gestión deberá quedar registrada en el historial del paciente.

---

### RN-055

El sistema deberá permitir plantillas para seguimiento de controles.

---

## 19. Documentos Legales

### RN-056

El sistema deberá gestionar documentos legales asociados al paciente.

---

### RN-057

Tipos iniciales:

* Consentimiento informado.
* Presupuesto aceptado.
* Plan de tratamiento aceptado.
* Autorización de menores.
* Protección de datos.
* Cierre de tratamiento.
* Otros.

---

### RN-058

Todo documento deberá registrar:

* Tipo.
* Fecha generación.
* Fecha firma.
* Paciente.
* Odontólogo.
* Usuario generador.

---

### RN-059

Los documentos deberán generarse mediante plantillas configurables.

---

### RN-060

Se permitirá:

* Firma digital.
* Firma en tablet.
* PDF firmado.
* Documento escaneado.

---

### RN-061

Un documento firmado no podrá modificarse.

---

### RN-062

El sistema deberá conservar historial de versiones.

---

### RN-063

Todo procedimiento invasivo deberá tener consentimiento informado asociado.

---

### RN-064

El sistema deberá advertir cuando falte consentimiento requerido.

---

### RN-065

Para menores de edad será obligatorio registrar responsable legal.

---

### RN-066

Todo presupuesto aceptado deberá conservar evidencia de aceptación.

---

### RN-067

El sistema deberá generar documento de cierre de tratamiento.

---

### RN-068

Los documentos deberán estar disponibles desde la ficha del paciente.

---

### RN-069

Los documentos no podrán eliminarse físicamente.

---

## 20. Decisiones Operativas Aprobadas

### RN-070

Estados de cita:

* Programada.
* Confirmada.
* Atendida.
* Cancelada.
* No Asistió.
* Reprogramada.

El estado de la cita representa el avance operativo de la atención.

---

### RN-071

Medios de confirmación de cita:

* WhatsApp.
* Llamada.
* Presencial.

El medio de confirmación es independiente del estado de la cita.

Ejemplo:

```text
Estado = Confirmada
Medio de confirmación = WhatsApp
```

---

### RN-072

Toda reprogramación deberá conservar trazabilidad completa.

Reglas:

* La cita original cambia a estado Reprogramada.
* Se crea una nueva cita.
* Ambas citas quedan relacionadas mediante cita_historial.
* Se conserva historial de fecha original, fecha nueva, motivo y usuario responsable.

---

### RN-073

Pueden crear sobrecupos:

* Secretaria.
* Administrador.
* Odontólogo Administrador.

Un odontólogo sin privilegios administrativos no puede crear sobrecupos.

---

### RN-074

Las citas con sobrecupo deberán visualizarse en color naranja dentro de la agenda.

---

### RN-075

Consentimientos MVP:

* El consentimiento informado está incluido en el MVP.
* La protección de datos está incluida en el MVP.
* No se requiere firma electrónica certificada para el MVP.

El MVP podrá registrar aceptación mediante firma simple, documento firmado, archivo adjunto o confirmación registrada, según el flujo disponible.

---

### RN-076

WhatsApp MVP:

* El sistema deberá generar el mensaje.
* El sistema deberá abrir WhatsApp Web.
* No se incluye WhatsApp Business API en el MVP.
* No se incluyen envíos automáticos en el MVP.

---

## 21. Seguimiento Comercial

### RN-077

El sistema deberá alertar pacientes valorados que no han aceptado ni rechazado el presupuesto.

---

### RN-078

Desde la alerta deberá ser posible:

* Contactar paciente.
* Enviar WhatsApp.
* Registrar respuesta.
* Aceptar presupuesto.
* Rechazar presupuesto.

---

### RN-079

El sistema deberá gestionar estados comerciales del presupuesto.

---

### RN-080

Los tiempos de seguimiento deberán ser configurables.

---

## 22. Laboratorios

### RN-081

El sistema deberá gestionar procedimientos dependientes de laboratorio.

Ejemplos:

* Corona.
* Prótesis.
* Carilla.
* Retenedor.
* Alineador.
* Placa.

---

### RN-082

Toda orden de laboratorio deberá registrar:

* Laboratorio.
* Fecha envío.
* Fecha estimada.
* Estado.

---

### RN-083

Estados posibles:

* Pendiente envío.
* Enviada.
* En proceso.
* Recibida.
* Entregada al paciente.
* Cancelada.
* Repetida.

---

### RN-084

El sistema deberá alertar trabajos próximos a vencerse.

---

### RN-085

El sistema deberá alertar trabajos vencidos.

---

### RN-086

Cuando un trabajo sea recibido deberá generarse alerta para contactar al paciente.

---

### RN-087

Desde la alerta deberá ser posible:

* Programar cita.
* Contactar paciente.
* Consultar orden.

---

### RN-088

Los tiempos estimados por tipo de trabajo deberán ser configurables.

---

## 23. Roles Flexibles

### RN-089

Un usuario podrá tener múltiples roles simultáneamente.

Ejemplo:

* Odontólogo.
* Secretaria.
* Administrador.

Esto permitirá operación en consultorios donde el odontólogo realiza funciones administrativas.
