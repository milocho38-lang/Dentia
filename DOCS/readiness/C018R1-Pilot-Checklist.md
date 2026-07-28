# C018R.1 — Checklist operativo para piloto K Astudillo

Este checklist debe completarse antes de iniciar varias semanas de uso real sin acompañamiento técnico permanente.

## Antes de iniciar

### Empresa

- [ ] Nombre comercial confirmado.
- [ ] Identificación/NIT/RUT registrada.
- [ ] País correcto.
- [ ] Zona horaria correcta.
- [ ] Correo institucional.
- [ ] Teléfono.
- [ ] Dirección.
- [ ] Branding cargado.
- [ ] Logo visible en PDFs.
- [ ] Encabezado institucional validado.
- [ ] Pie institucional validado.
- [ ] Firma gráfica configurada.

### Sedes

- [ ] Sede real creada.
- [ ] Dirección completa.
- [ ] Ciudad.
- [ ] Zona horaria efectiva.
- [ ] Estado activo.
- [ ] Horario operativo revisado.

### Usuario odontólogo

- [ ] Kimberly Astudillo activa.
- [ ] Pertenece a empresa K Astudillo.
- [ ] No tiene rol `PLATFORM_ADMIN`.
- [ ] Tiene rol `DENTIST_ADMIN` si gestionará clínica y administración.
- [ ] Tiene rol `DENTIST` si el catálogo real exige acumulación explícita.
- [ ] Tiene sede asignada.
- [ ] Cerró sesión y volvió a iniciar después del cambio de roles.

### Perfil odontológico

- [ ] Perfil vinculado al mismo `user_id`.
- [ ] Empresa correcta.
- [ ] Sedes correctas.
- [ ] Registro profesional.
- [ ] Especialidad.
- [ ] Estado activo.
- [ ] Firma coherente con documentos del piloto.

### Catálogo inicial

- [ ] Valoración inicial.
- [ ] Profilaxis.
- [ ] Sellante.
- [ ] Resina una superficie.
- [ ] Resina dos superficies.
- [ ] Resina MOD.
- [ ] Endodoncia unirradicular.
- [ ] Endodoncia multirradicular.
- [ ] Corona provisional.
- [ ] Corona definitiva.
- [ ] Exodoncia simple.
- [ ] Exodoncia quirúrgica.
- [ ] Implante.
- [ ] Control postoperatorio.
- [ ] Blanqueamiento.
- [ ] Procedimientos generales marcados como `NO_CHANGE` cuando no alteran odontograma.

### Seguridad operacional

- [ ] Backup PostgreSQL + storage configurado.
- [ ] Prueba de restauración documentada.
- [ ] Git limpio antes de desplegar.
- [ ] Producción en commit esperado.
- [ ] Alembic en head.
- [ ] Health check OK.

## Primer día

- [ ] Crear paciente de prueba.
- [ ] Crear cita.
- [ ] Abrir historia clínica.
- [ ] Crear evolución en borrador.
- [ ] Firmar evolución.
- [ ] Abrir odontograma.
- [ ] Registrar diagnóstico.
- [ ] Crear tratamiento desde odontograma.
- [ ] Crear procedimiento desde tratamiento.
- [ ] Generar presupuesto.
- [ ] Aprobar presupuesto.
- [ ] Registrar pago.
- [ ] Descargar comprobante.
- [ ] Crear receta.
- [ ] Previsualizar receta.
- [ ] Finalizar receta.
- [ ] Crear remisión/carta.
- [ ] Descargar PDF histórico.

## Uso semanal

- [ ] Revisar citas creadas.
- [ ] Revisar evoluciones firmadas.
- [ ] Revisar tratamientos activos.
- [ ] Revisar presupuestos aprobados/rechazados.
- [ ] Revisar pagos y cartera.
- [ ] Revisar recetas emitidas.
- [ ] Revisar documentos clínicos emitidos.
- [ ] Revisar reportes básicos.
- [ ] Registrar errores y fricciones.

## Soporte

Al reportar un error:

- [ ] Enviar módulo y acción exacta.
- [ ] Enviar hora aproximada.
- [ ] Enviar captura sin datos sensibles cuando sea posible.
- [ ] No enviar historias clínicas completas por chat.
- [ ] No enviar medicamentos/alergias específicas si no son necesarios.
- [ ] Indicar paciente con iniciales o identificador interno.
- [ ] Adjuntar PDF solo si el error es del PDF.

Cuándo detener uso de una función:

- [ ] Si el pago queda duplicado.
- [ ] Si una empresa ve datos de otra.
- [ ] Si una evolución firmada cambia sin adenda.
- [ ] Si un PDF histórico no descarga.
- [ ] Si se pierde una receta/documento finalizado.

## Métricas de éxito

- [ ] Pacientes creados.
- [ ] Citas gestionadas.
- [ ] Evoluciones firmadas.
- [ ] Tratamientos creados.
- [ ] Presupuestos generados.
- [ ] Pagos registrados.
- [ ] Recetas generadas.
- [ ] Documentos clínicos generados.
- [ ] Errores bloqueantes.
- [ ] Errores no bloqueantes.
- [ ] Tiempo promedio del flujo completo.
- [ ] Funciones abandonadas por fricción.
