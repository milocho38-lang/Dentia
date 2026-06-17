# D002A - Casos de Uso Operativos

Versión: 1.0

## Objetivo

Definir los principales procesos operativos que realizarán los usuarios dentro del sistema para servir como base del diseño funcional y posterior desarrollo.

---

# CU001 - Registrar Paciente

## Actores

* Secretaria
* Odontólogo
* Odontólogo Administrador

## Flujo Principal

1. Ingresar al módulo Pacientes.
2. Seleccionar "Nuevo Paciente".
3. Registrar datos básicos.
4. Registrar datos de contacto.
5. Registrar responsable legal si aplica.
6. Guardar paciente.

## Resultado

Paciente creado y disponible para programación de citas.

---

# CU002 - Programar Cita

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Buscar paciente.
2. Seleccionar odontólogo.
3. Seleccionar sede.
4. Seleccionar fecha.
5. Seleccionar hora.
6. Seleccionar tipo de cita.
7. Confirmar programación.

## Validaciones

* Disponibilidad del odontólogo.
* Conflictos de agenda.
* Sobrecupos.
* Horario permitido.
* Permiso del usuario para crear sobrecupos.

## Regla de Sobrecupo

Si existe conflicto de agenda para el odontólogo, el sistema podrá permitir sobrecupo únicamente para:

* Secretaria.
* Administrador.
* Odontólogo Administrador.

Un odontólogo sin privilegios administrativos no podrá crear sobrecupos.

## Resultado

Cita registrada.

---

# CU002A - Reprogramar Cita

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Abrir agenda.
2. Seleccionar cita existente.
3. Elegir nueva fecha y hora.
4. Registrar motivo de reprogramación.
5. Confirmar reprogramación.

## Reglas

* La cita original cambia a estado Reprogramada.
* Se crea una nueva cita con la nueva fecha y hora.
* Ambas citas quedan relacionadas mediante cita_historial.
* Se conserva trazabilidad completa de usuario, motivo, fecha original y fecha nueva.

## Resultado

Cita nueva registrada y cita original marcada como reprogramada.

---

# CU003 - Confirmar Cita

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Abrir agenda.
2. Seleccionar cita.
3. Contactar paciente.
4. Registrar resultado.

## Estados

Estado de cita:

* Confirmada.

Medio de confirmación:

* WhatsApp.
* Llamada.
* Presencial.

El estado de la cita y el medio de confirmación son independientes.

## Resultado

Estado de confirmación actualizado.

---

# CU004 - Realizar Valoración Inicial

## Actor

* Odontólogo

## Flujo Principal

1. Abrir ficha del paciente.
2. Registrar antecedentes.
3. Registrar diagnóstico.
4. Registrar observaciones.
5. Actualizar odontograma.
6. Guardar valoración.

## Resultado

Valoración completada.

---

# CU005 - Crear Presupuesto

## Actor

* Odontólogo

## Flujo Principal

1. Seleccionar paciente.
2. Seleccionar procedimientos.
3. Asociar piezas dentales si aplica.
4. Calcular valor.
5. Generar presupuesto.

## Resultado

Presupuesto generado.

---

# CU006 - Seguimiento de Presupuesto

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Abrir panel de alertas.
2. Consultar presupuestos pendientes.
3. Contactar paciente.
4. Registrar respuesta.

## Resultado

Estado actualizado.

---

# CU007 - Convertir Presupuesto en Tratamiento

## Actores

* Secretaria
* Odontólogo
* Odontólogo Administrador

## Flujo Principal

1. Abrir presupuesto.
2. Registrar aceptación.
3. Registrar anticipo si aplica.
4. Crear tratamiento.

## Resultado

Tratamiento activo.

---

# CU008 - Registrar Pago

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Buscar paciente.
2. Abrir tratamiento.
3. Registrar valor.
4. Seleccionar medio de pago.
5. Confirmar.

## Resultado

Pago registrado.

---

# CU009 - Registrar Evolución Clínica

## Actor

* Odontólogo

## Flujo Principal

1. Abrir cita.
2. Registrar procedimiento realizado.
3. Registrar evolución.
4. Registrar recomendaciones.
5. Adjuntar evidencias si aplica.
6. Guardar.

## Resultado

Historia clínica actualizada.

---

# CU010 - Actualizar Odontograma

## Actor

* Odontólogo

## Flujo Principal

1. Abrir odontograma.
2. Seleccionar pieza dental.
3. Registrar procedimiento o estado.
4. Guardar cambios.

## Resultado

Odontograma actualizado.

---

# CU011 - Enviar Trabajo a Laboratorio

## Actores

* Odontólogo
* Secretaria

## Flujo Principal

1. Abrir tratamiento.
2. Crear orden de laboratorio.
3. Seleccionar laboratorio.
4. Registrar fecha estimada.
5. Registrar costo.
6. Guardar.

## Resultado

Orden creada.

---

# CU012 - Consultar Estado de Laboratorio

## Actores

* Secretaria
* Odontólogo

## Flujo Principal

1. Abrir módulo Laboratorios.
2. Consultar órdenes activas.
3. Revisar estado.

## Resultado

Seguimiento actualizado.

---

# CU013 - Registrar Recepción de Laboratorio

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Abrir orden.
2. Marcar como recibida.
3. Confirmar recepción.

## Resultado

Se genera alerta para contactar paciente.

---

# CU014 - Programar Instalación de Trabajo

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Abrir alerta.
2. Contactar paciente.
3. Programar cita.
4. Confirmar agenda.

## Resultado

Paciente agendado.

---

# CU015 - Gestionar Alertas de Control

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Abrir panel de alertas.
2. Revisar controles próximos o vencidos.
3. Contactar paciente.
4. Programar cita.

## Resultado

Control gestionado.

---

# CU016 - Cargar Radiografías e Imágenes

## Actores

* Secretaria
* Odontólogo

## Flujo Principal

1. Abrir expediente.
2. Seleccionar archivos.
3. Clasificar archivo.
4. Guardar.

## Resultado

Archivo disponible en expediente.

---

# CU017 - Consultar Archivos Clínicos

## Actores

* Secretaria
* Odontólogo

## Flujo Principal

1. Abrir expediente.
2. Filtrar archivos.
3. Visualizar o descargar.

## Resultado

Información disponible.

---

# CU018 - Generar Consentimiento Informado

## Actores

* Secretaria
* Odontólogo

## Flujo Principal

1. Seleccionar tratamiento.
2. Seleccionar plantilla.
3. Generar documento.
4. Solicitar firma.

## Resultado

Documento almacenado.

## Alcance MVP

El consentimiento informado está incluido dentro del MVP.

No se requiere firma electrónica certificada para el MVP.

---

# CU018A - Generar Documento de Protección de Datos

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Abrir ficha del paciente.
2. Seleccionar plantilla de protección de datos.
3. Generar documento.
4. Solicitar aceptación o firma simple.
5. Guardar evidencia.

## Resultado

Documento de protección de datos almacenado.

## Alcance MVP

La protección de datos está incluida dentro del MVP.

No se requiere firma electrónica certificada para el MVP.

---

# CU019 - Registrar Firma o Aceptación

## Actores

* Paciente
* Secretaria

## Flujo Principal

1. Abrir documento.
2. Registrar aceptación.
3. Capturar firma o adjuntar documento firmado.
4. Guardar.

## Resultado

Documento firmado.

---

# CU020 - Finalizar Tratamiento

## Actor

* Odontólogo

## Flujo Principal

1. Abrir tratamiento.
2. Registrar estado final.
3. Adjuntar evidencias.
4. Generar documento de cierre.

## Resultado

Tratamiento finalizado.

---

# CU021 - Registrar Conformidad del Paciente

## Actores

* Paciente
* Secretaria
* Odontólogo

## Flujo Principal

1. Revisar resultado final.
2. Seleccionar conformidad.
3. Registrar observaciones si aplica.
4. Firmar.

## Estados

* Conforme.
* Conforme con observaciones.
* No conforme.

## Resultado

Cierre legal completado.

---

# CU022 - Registrar Inventario

## Actores

* Secretaria
* Administrador

## Flujo Principal

1. Crear insumo.
2. Registrar stock inicial.
3. Guardar.

## Resultado

Insumo disponible.

---

# CU023 - Registrar Movimiento de Inventario

## Actores

* Secretaria
* Administrador

## Flujo Principal

1. Seleccionar insumo.
2. Registrar entrada o salida.
3. Confirmar.

## Resultado

Stock actualizado.

---

# CU024 - Consultar Alertas de Stock

## Actores

* Secretaria
* Administrador

## Flujo Principal

1. Abrir alertas.
2. Revisar insumos próximos a agotarse.
3. Gestionar reposición.

## Resultado

Inventario controlado.

---

# CU025 - Enviar WhatsApp

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Seleccionar paciente.
2. Seleccionar plantilla.
3. Generar mensaje.
4. Abrir WhatsApp Web.
5. Enviar.

## Resultado

Comunicación registrada.

## Alcance MVP

El MVP permite generar el mensaje y abrir WhatsApp Web.

No incluye WhatsApp Business API ni envíos automáticos.

---

# CU026 - Registrar Gestión Comercial

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Abrir presupuesto pendiente.
2. Registrar contacto.
3. Registrar respuesta.
4. Guardar seguimiento.

## Resultado

Seguimiento actualizado.

---

# CU027 - Consultar Indicadores

## Actor

* Administrador

## Flujo Principal

1. Abrir dashboard.
2. Aplicar filtros.
3. Consultar indicadores.

## Resultado

Información consolidada.

---

# CU028 - Cierre Diario de Caja

## Actores

* Secretaria
* Administrador
* Odontólogo Administrador

## Flujo Principal

1. Consultar movimientos.
2. Verificar valores.
3. Registrar observaciones.
4. Cerrar caja.

## Resultado

Caja cerrada.

---

# CU029 - Reversar Pago

## Actores

* Administrador
* Usuario autorizado

## Flujo Principal

1. Seleccionar pago.
2. Registrar motivo.
3. Confirmar reverso.

## Resultado

Pago reversado con auditoría.

---

# CU030 - Gestión Integral del Día

## Actores

* Secretaria
* Odontólogo Administrador

## Flujo Principal

1. Revisar agenda del día.
2. Revisar alertas pendientes.
3. Confirmar pacientes.
4. Gestionar pagos.
5. Gestionar laboratorios.
6. Gestionar controles.
7. Revisar caja.

## Resultado

Operación diaria controlada desde una única plataforma.

---

# Casos de Uso Críticos para MVP

Los siguientes casos de uso se consideran indispensables para la primera versión:

* CU001 Registrar Paciente
* CU002 Programar Cita
* CU004 Realizar Valoración Inicial
* CU005 Crear Presupuesto
* CU007 Convertir Presupuesto en Tratamiento
* CU008 Registrar Pago
* CU009 Registrar Evolución Clínica
* CU010 Actualizar Odontograma
* CU020 Finalizar Tratamiento
* CU028 Cierre Diario de Caja

Estos casos conforman el núcleo operativo mínimo del sistema.
