# RESUMEN_PROYECTO

## 1. Objetivo del producto

Dentia es el nombre oficial y comercial de la plataforma integral de gestion odontologica para odontologos independientes, consultorios y clinicas odontologicas. Su objetivo es centralizar la operacion clinica, administrativa y financiera en una sola herramienta facil de usar para odontologos, secretarias y administradores.

El producto debe permitir operar inicialmente en entorno local y quedar preparado desde el inicio para evolucionar a un modelo SaaS multiempresa, multiusuario y con funciones futuras de inteligencia artificial. La operacion normal no debe depender de IA.

El MVP debe permitir que un consultorio real gestione usuarios, pacientes, agenda, historia clinica, odontograma, presupuestos, tratamientos, pagos y caja.

## 1A. Identidad visual

El documento D006 define la identidad visual oficial de Dentia. La marca debe transmitir confianza, salud, organizacion, profesionalismo, tecnologia y cercania.

El estilo visual definido es "Clinica Moderna":

- Diseno limpio, claro y profesional.
- Mucho espacio visual y baja carga decorativa.
- Navegacion sencilla para personal administrativo y clinico.
- Apariencia moderna sin sentirse agresiva ni excesivamente tecnologica.
- Enfoque en facilidad de uso, orden y productividad.

Se deben evitar:

- Interfaces oscuras como estilo principal.
- Exceso de colores simultaneos.
- Estetica gamer o tecnologica agresiva.
- Elementos visuales recargados.

Paleta de colores oficial:

- Color principal: Verde Clinico `#16A34A`, para botones principales, acciones positivas y elementos destacados.
- Color secundario: Verde Suave `#22C55E`, para indicadores, tarjetas y estados secundarios.
- Color terciario: Verde Claro `#BBF7D0`, para fondos suaves y areas informativas.
- Fondo principal: `#F8FAFC`.
- Texto principal: `#1F2937`.

Estados del sistema:

- Exito: `#22C55E`.
- Advertencia: `#F59E0B`.
- Error: `#EF4444`.
- Informacion: `#0EA5E9`.

Lineamientos de componentes:

- Botones con bordes redondeados, aspecto moderno y tamano comodo para operacion administrativa.
- Tarjetas con sombras suaves y bordes discretos.
- Tablas limpias, con filtros visibles y busqueda rapida.
- Formularios con campos amplios y validaciones visuales claras.
- Dashboard orientado a transmitir orden, control y estado del consultorio mediante tarjetas visuales.

El logo queda pendiente de diseno. Los lineamientos iniciales indican un estilo moderno, relacionado con salud dental, uso predominante de tonos verdes y funcionamiento sobre fondos claros y oscuros.

## 2. Usuarios del sistema

Los documentos definen cuatro perfiles principales:

- Administrador: configura empresa, usuarios, sedes, permisos, reportes y parametros generales.
- Secretaria: gestiona agenda, pacientes, presupuestos, pagos, seguimiento, alertas, comunicaciones y operacion diaria.
- Odontologo: gestiona historia clinica, evoluciones, odontograma, tratamientos, procedimientos, evidencias y documentos clinicos.
- Odontologo Administrador: combina funciones clinicas y administrativas para consultorios pequenos o profesionales independientes sin secretaria.

Tambien aparecen actores indirectos o contextuales:

- Paciente: participa en firmas, conformidades, aceptaciones y comunicaciones, aunque no se contempla portal de paciente en el alcance inicial.
- Laboratorio externo: entidad gestionada por el sistema para trabajos odontologicos, sin acceso directo definido.
- Usuario autorizado: perfil funcional para acciones criticas como reversar pagos.

Los usuarios pueden tener multiples roles simultaneamente, lo cual es importante para consultorios pequenos donde una misma persona cumple varias funciones.

## 3. Modulos principales

Los modulos funcionales definidos son:

- Dashboard operativo: citas del dia, pacientes, pagos, tratamientos, alertas y laboratorios pendientes.
- Seguridad y configuracion: login, JWT, roles, permisos, empresas, sedes, odontologos y especialidades.
- Pacientes: registro unico por empresa, responsables legales, expediente e historial.
- Agenda: citas diarias, semanales y mensuales, confirmaciones, cancelaciones, reprogramaciones y sobrecupos.
- Historia clinica: antecedentes, alergias, medicamentos, diagnosticos, evoluciones y correcciones auditadas.
- Odontograma: estado actual por pieza dental, eventos historicos y procedimientos asociados.
- Presupuestos: generacion, items, seguimiento comercial, aceptacion, rechazo y conversion a tratamiento.
- Tratamientos: planes, etapas, procedimientos, avance, costos, cierre y conformidad del paciente.
- Pagos y caja: valoraciones, anticipos, abonos, pagos totales, movimientos, cartera, cierres diarios y reversiones.
- Laboratorios: laboratorios externos, ordenes, seguimiento, costos, alertas y entrega al paciente.
- Inventario basico: insumos, movimientos, stock minimo y alertas.
- Archivos clinicos: fotografias, radiografias, PDFs, documentos y evidencias asociadas a paciente, cita o tratamiento.
- Documentos legales: consentimientos, proteccion de datos, documentos firmados, versiones y cierres.
- Alertas y seguimiento: controles, presupuestos sin respuesta, tratamientos sin proxima cita, laboratorios, saldos y stock bajo.
- Comunicaciones y WhatsApp: plantillas, mensajes manuales e historial de contacto.
- Reportes: financieros, clinicos, operativos, cartera, laboratorios e inventario.
- IA futura: redaccion de evoluciones, generacion de mensajes, resumen de pacientes y alertas inteligentes.

## 4. Arquitectura propuesta

La arquitectura oficial esta compuesta por frontend, backend, base de datos y almacenamiento de archivos.

Frontend:

- Next.js, React, TypeScript y Tailwind CSS.
- React Hook Form y Zod para formularios y validaciones de experiencia de usuario.
- Axios para consumo de APIs.
- Layout con sidebar izquierdo, header superior y area principal.
- Optimizacion principal para escritorio, portatiles, monitores externos y tablets.
- No debe contener logica de negocio critica ni acceder directamente a la base de datos.
- Debe aplicar la identidad visual Dentia: estilo de clinica moderna, fondo claro, verdes clinicos como acento principal, estados visuales consistentes y componentes limpios.

Backend:

- Python 3.12+, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT y bcrypt.
- Arquitectura por capas: Router, Service, Repository, Database.
- La capa Service concentra reglas de negocio, validaciones clinicas, financieras, permisos, auditoria y generacion de alertas.
- API REST como unico canal entre frontend y backend.
- Jobs para procesos automaticos como alertas, seguimientos y controles.
- Servicios independientes previstos para storage, PDF, WhatsApp futuro e IA.

Base de datos:

- PostgreSQL con UUID como llave primaria.
- Migraciones mediante Alembic.
- Todas las entidades operativas deben filtrar por empresa_id.
- Uso de DECIMAL(14,2) para dinero.
- Estados inicialmente como texto controlado, con posible evolucion futura a catalogos o enumeraciones.
- Indices recomendados sobre empresa_id, paciente_id, odontologo_id, fechas, estados y campos de busqueda.

Storage:

- Inicialmente sistema de archivos local.
- La base de datos solo almacena rutas, metadatos y relaciones.
- Los archivos se acceden mediante backend, nunca por rutas publicas directas.
- Debe existir abstraccion de storage para migrar a S3, MinIO, Google Cloud Storage o Azure Blob Storage.

Seguridad y SaaS:

- Toda operacion requiere autenticacion.
- Autorizacion basada en roles y permisos.
- JWT con user_id, empresa_id y roles.
- Aislamiento multiempresa por empresa_id.
- Auditoria obligatoria para acciones criticas.
- Preparacion para Docker, nube, backups, monitoreo y alta disponibilidad futura.

## 5. Modelo de datos resumido

El modelo se divide en cinco bloques principales y supera las 45 tablas principales.

Estructura organizacional y seguridad:

- empresas, sedes, usuarios, roles, usuario_roles, permisos, rol_permisos.
- odontologos, especialidades, odontologo_especialidades, odontologo_sedes.
- Soporta multiempresa, multiples sedes, multiples roles por usuario y odontologos en varias sedes.

Pacientes, agenda e historia clinica:

- pacientes, responsables_paciente, tipos_cita, citas, cita_historial.
- historias_clinicas, evoluciones_clinicas, evolucion_correcciones.
- odontograma_piezas, odontograma_eventos, procedimientos.
- El paciente es unico por empresa y mantiene historia, tratamientos y finanzas aunque cambie de sede o especialista.

Presupuestos, tratamientos y pagos:

- presupuestos, presupuesto_items, presupuesto_seguimientos.
- tratamientos, tratamiento_etapas, tratamiento_procedimientos, cierres_tratamiento.
- pagos, pago_reversiones, caja_movimientos, caja_cierres.
- La cartera se plantea inicialmente como vista logica desde saldos de tratamientos.

Laboratorios, inventario, documentos y archivos:

- laboratorios, ordenes_laboratorio, laboratorio_seguimientos.
- inventario_items, inventario_movimientos.
- documentos, documento_versiones, plantillas_documentos.
- archivos, archivo_etiquetas.
- Los documentos firmados no se modifican y los archivos clinicos se almacenan fuera de la base de datos.

Alertas, comunicaciones, IA, auditoria y configuracion:

- alertas, alerta_gestiones.
- plantillas_mensaje, comunicaciones.
- ia_solicitudes.
- auditoria_eventos.
- configuraciones_empresa, parametros_laboratorio, parametros_control.
- El dashboard se define como vista logica desde citas, alertas, tratamientos, pagos y laboratorios.

Reglas transversales:

- Toda tabla principal debe incluir id, created_at, updated_at, created_by e is_active.
- Las eliminaciones fisicas estan prohibidas en tablas criticas.
- Toda accion critica debe auditarse.
- Los pagos no se eliminan, solo se reversan.
- Las evoluciones clinicas no se eliminan, solo se corrigen o anulan con trazabilidad.
- Los documentos firmados no se modifican y deben conservar versiones.

## 6. Roadmap resumido

El roadmap oficial define desarrollo incremental por fases. No debe iniciarse una fase nueva hasta que la actual este implementada, probada y aprobada.

MVP oficial: Fase 0 a Fase 8, tareas C001 a C038.

- Fase 0: preparacion del proyecto, estructura, backend, frontend y PostgreSQL.
- Fase 1: seguridad y configuracion, login, roles, permisos, empresas, sedes y odontologos.
- Fase 2: pacientes, responsables y expediente.
- Fase 3: agenda, tipos de cita, programacion, sobrecupos y confirmaciones.
- Fase 4: historia clinica, evoluciones y auditoria clinica.
- Fase 5: odontograma, interfaz visual e historial por pieza.
- Fase 6: procedimientos, presupuestos, seguimiento comercial y conversion a tratamiento.
- Fase 7: tratamientos, etapas, procedimientos, cierre y conformidad.
- Fase 8: pagos, cartera, caja, cierre diario y reversiones.

Fases posteriores al MVP:

- Fase 9: laboratorios.
- Fase 10: archivos y documentos.
- Fase 11: inventario.
- Fase 12: alertas operativas.
- Fase 13: comunicaciones y WhatsApp manual.
- Fase 14: reportes.
- Fase 15: inteligencia artificial.
- Fase 16: SaaS, Docker, cloud storage, PostgreSQL cloud y despliegue productivo.

## 7. Riesgos tecnicos detectados

- Alcance amplio para MVP: aunque el MVP excluye laboratorios, inventario, IA, SaaS y WhatsApp Business, sigue incluyendo agenda, historia clinica, odontograma, presupuestos, tratamientos, pagos y caja, todos con reglas criticas.
- Complejidad multiempresa temprana: filtrar todo por empresa_id desde el inicio es correcto, pero cualquier omision puede producir fuga de datos entre empresas.
- Auditoria transversal: muchas reglas dependen de auditoria, pero se debe definir con precision que acciones son criticas, que datos se registran y como se evita manipulacion.
- Sincronizacion financiera: valor_total, valor_abonado y saldo_pendiente en tratamientos pueden desincronizarse si no se define una estrategia clara entre calculo derivado, persistencia y transacciones.
- Pagos y caja: todo pago debe impactar caja y toda reversion debe auditarse; esto exige transacciones atomicas y pruebas fuertes.
- Odontograma interactivo: tiene riesgo de complejidad de UI y modelo, especialmente por piezas, superficies, historial y asociacion con procedimientos.
- Storage local inicial: es simple para MVP, pero requiere disciplina en rutas, permisos, backups, migracion futura y limpieza de temporales.
- Documentos legales y firmas: hay varias modalidades de firma, versionamiento y bloqueo de documentos firmados; puede volverse complejo si no se acota el MVP.
- Alertas automaticas: dependen de reglas temporales, estados y datos de varios modulos; hay riesgo de duplicados, vencimientos incorrectos o alertas no cerradas.
- Manejo de fechas y zonas horarias: se recomienda UTC, pero falta definir zona local por empresa o sede y reglas para agenda.
- Estados como texto controlado: agiliza el inicio, pero puede generar inconsistencias si no se centralizan constantes y validaciones.
- Consistencia visual: D006 define paleta y estilo, pero aun falta convertirlo en sistema de diseno concreto con tokens, componentes base, reglas de espaciado, tipografia y estados interactivos.
- Seguridad de JWT y almacenamiento en frontend: se menciona almacenamiento seguro, pero falta decision especifica sobre cookies httpOnly vs almacenamiento del navegador.
- Pruebas: los documentos exigen pruebas por modulo, services, endpoints y validaciones, pero aun no detallan estrategia minima, fixtures o datos semilla.
- Instalacion local: se desea facilidad de instalacion, pero Python, Node.js, PostgreSQL y storage pueden ser una barrera si no se define automatizacion.

## 8. Inconsistencias o vacios encontrados

- Rutas y nombres de documentos: esta inconsistencia fue corregida en C003B. La carpeta oficial es DOCS y AGENTS.md referencia los nombres reales de los archivos.
- Nombre del archivo D006: el usuario lo menciona como DOCS/D006_IDENTIDAD_VISUAL.md, pero el archivo real encontrado es DOCS/D006 - IDENTIDAD VISUAL.md.
- Codificacion de documentos: al leerlos aparecen caracteres corruptos en tildes y simbolos, lo que sugiere un problema de encoding que conviene normalizar antes de seguir documentando o automatizar lecturas.
- Nombre del producto: D000 hablaba de "Nombre provisional: Dentia", mientras D006 ya establece "Dentia" como nombre comercial. Debe tratarse como nombre oficial desde este punto.
- Alcance inicial inconsistente: D001 incluye laboratorios, inventario, archivos, documentos legales, alertas, WhatsApp y reportes dentro del alcance inicial; D005 indica que el MVP no requiere inicialmente inventario, laboratorios, IA, SaaS, WhatsApp Business ni nube, y deja varios de esos modulos para fases posteriores.
- MVP funcional vs casos criticos: D002A marca como criticos CU001, CU002, CU004, CU005, CU007, CU008, CU009, CU010, CU020 y CU028; D005 incluye ademas seguridad, roles, pacientes, agenda, historia, odontograma, presupuestos, tratamientos, pagos, caja, cartera y reversiones hasta C038.
- Documentos legales: las reglas RN-056 a RN-069 exigen gestion robusta de documentos legales y consentimientos, pero el roadmap los ubica principalmente en Fase 10, despues del MVP. Esto puede chocar con reglas como consentimiento obligatorio para procedimientos invasivos.
- Archivos clinicos ilimitados: se define repositorio ilimitado por paciente, pero tambien almacenamiento local inicial y limite sugerido por archivo de 25 MB. Falta politica de cuota, backups, monitoreo de disco y retencion.
- Auditoria estandar incompleta en algunas tablas: varias tablas principales listadas no incluyen todos los campos estandar id, created_at, updated_at, created_by, is_active. Puede ser intencional en tablas de historial, pero no esta explicado caso por caso.
- empresa_id no aparece en algunas tablas relacionadas: por ejemplo responsables_paciente, historias_clinicas, evolucion_correcciones, odontograma_piezas, odontograma_eventos y otras dependen indirectamente del paciente o entidad padre. Falta definir si el aislamiento sera directo por empresa_id en todas las operativas o indirecto por relacion.
- sede_id en pagos y caja: pagos no incluye sede_id, pero caja_movimientos y caja_cierres si. Falta definir como se determina la sede de un pago cuando no hay cita asociada.
- Tratamiento desde presupuesto aceptado: las reglas indican que un tratamiento debe originarse desde un presupuesto aceptado, pero tambien hay valoracion inicial, remisiones, alta sin tratamiento y multiples tratamientos. Falta definir excepciones o flujo para tratamientos iniciados sin presupuesto formal.
- Valoracion inicial: se describe como atencion clinica independiente y puede tener costo, pero el modelo no separa claramente una entidad de valoracion; parece resolverse mediante cita, evolucion y pago tipo Valoracion.
- Confirmacion de cita: existe estado de cita Confirmada y campo medio_confirmacion. Falta definir si la confirmacion cambia el estado principal o solo el medio, y como se representa "Sin confirmar".
- Reprogramaciones: citas tiene estado Reprogramada y cita_historial guarda fechas. Falta definir si se actualiza la misma cita, se crea una nueva, o ambas cosas.
- Sobrecupos: se permite crear cita como sobrecupo con advertencia, pero falta una regla clara sobre limites, permisos requeridos y visualizacion en calendario.
- WhatsApp MVP: D002 habla de envio manual y D004C/D004E aclaran que MVP genera mensajes, no integra WhatsApp Business. Falta precisar si "abrir WhatsApp" sera enlace externo, WhatsApp Web o solo copia de texto.
- IA futura: se define ia_solicitudes y proveedores posibles, pero falta politica de privacidad, minimizacion de datos clinicos, consentimiento y configuracion por empresa.
- Reportes: estan definidos funcionalmente, pero no se detallan metricas exactas, filtros obligatorios ni permisos por rol.
- Identidad visual incompleta: D006 define paleta, estilo y lineamientos generales, pero el logo esta pendiente y no se especifica tipografia, iconografia, densidad exacta de tablas, variantes de botones, estados hover/focus/disabled ni criterios de accesibilidad de contraste.
- Backups: se recomienda backup diario, pero falta definir retencion, ubicacion, cifrado, restauracion probada y responsable operativo en instalacion local.
- Refresh token: queda para fases posteriores; para MVP con JWT de 8 horas falta definir comportamiento de expiracion, renovacion manual y cierre de sesion.
- Eliminacion logica universal: se prohiben eliminaciones fisicas en tablas criticas, pero algunos historiales y tablas puente no incluyen is_active. Falta clasificacion formal de tablas criticas, historicas, puente y catalogos.
