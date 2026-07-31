# C019A.0 — Flujos de revisión, decisión y firma de consentimientos

Estado: diseño UX provisional; textos no aprobados jurídicamente.

Documento maestro: [Contrato clínico-funcional C019A.0](../clinical/C019A0-Informed-Consents-Electronic-Acceptance-Contract.md).

Todos los textos entre comillas en este documento son **copy provisional no aprobado jurídicamente**. Deben validarse por país y categoría antes de producción.

## 1. Principios

- El profesional informa; la interfaz registra el proceso, no lo reemplaza.
- Aceptar y rechazar deben ser acciones explícitas, equivalentes en claridad.
- No se marca una casilla por defecto.
- La versión y contenido se congelan antes de presentar.
- El firmante conoce quién solicita, para qué paciente y qué acto se propone.
- No se reutiliza una firma gráfica.
- Cerrar, abandonar o expirar nunca equivale a aceptar.
- Urgencias no se bloquean por una automatización de UX.

## 2. Profesional crea una instancia

1. Paciente → Documentos → Consentimientos.
2. Acción “Nuevo consentimiento”.
3. Elegir familia, plantilla publicada y país aplicable.
4. Relacionar sede, profesional, cita, tratamiento o procedimiento.
5. Validar paciente, edad, participante y representación.
6. Revisar variables resueltas y anexos.
7. Guardar `DRAFT`.
8. Mostrar resumen de faltantes.

Copy provisional:

- “Borrador. Este documento todavía no puede ser firmado.”
- “Los textos y participantes deben revisarse antes de presentarlo.”

## 3. Revisión profesional

1. El profesional abre vista previa.
2. Verifica diagnóstico/contexto, procedimiento, riesgos, alternativas y participantes.
3. Confirma que explicó y ofreció preguntas.
4. Acción “Confirmar para revisión”.
5. La instancia pasa a `READY_FOR_REVIEW`; el contenido queda congelado.

Copy provisional:

- “Confirmo que revisé el contenido y que será explicado al paciente o representante.”
- “Después de continuar no podrá cambiar el texto de esta instancia.”

La declaración exacta requiere revisión clínica y jurídica.

## 4. Firma en tableta de la clínica

1. Personal elige “Firmar en este dispositivo”.
2. Confirma identidad presencial según política.
3. Entrega o gira el dispositivo al firmante.
4. Pantalla de privacidad muestra documento completo y navegación.
5. Firmante marca declaraciones individualmente cuando aplique.
6. Elige aceptar o rechazar.
7. Si acepta, firma con dedo o stylus; mouse solo contingencia.
8. Revisa resumen final.
9. Confirma.
10. Sistema sella evidencia/PDF y ofrece copia.

Copy provisional:

- “Lea todo el documento antes de decidir.”
- “Su firma se usará únicamente en este documento.”
- “Firmar no reemplaza su derecho a preguntar.”

## 5. Firma desde celular del paciente

1. Profesional genera sesión remota.
2. Paciente abre enlace opaco.
3. Ve clínica, profesional, paciente parcialmente identificado y propósito.
4. Verifica canal mediante OTP si la política lo requiere.
5. Lee contenido en diseño móvil.
6. Puede ampliar secciones, regresar y solicitar aclaración.
7. Acepta o rechaza.
8. Si acepta, firma con dedo.
9. Confirma y recibe copia.

No se debe cargar una firma guardada del dispositivo como sustituto silencioso.

## 6. Enlace por correo

1. Usuario verifica correo del participante.
2. Sistema muestra destino parcialmente enmascarado.
3. Se emite enlace con vigencia provisional configurable.
4. Correo no incluye contenido clínico.
5. Apertura lleva al portal Dentia.
6. Reenvío rota o invalida sesiones según política.

Copy provisional:

- “Enviaremos un enlace seguro a c***@dominio.com.”
- “El correo no contiene su información clínica.”

El envío de PDF adjunto no forma parte del MVP sin evaluación de privacidad.

## 7. QR

1. Profesional muestra QR generado para una sesión.
2. QR contiene únicamente URL opaca.
3. Paciente escanea con su dispositivo.
4. La sesión continúa como firma móvil.
5. QR expira y no puede reutilizarse fuera de política.

Copy provisional:

- “Escanee para revisar el documento en su dispositivo.”
- “No comparta este código.”

## 8. OTP

1. Sistema informa el canal enmascarado.
2. Firmante solicita código.
3. Se envía OTP por correo en MVP provisional.
4. Firmante ingresa el código.
5. Error no revela si existe otra persona/cuenta.
6. Intentos y reenvíos se limitan.
7. Al verificar, la sesión continúa.

Copy provisional:

- “Ingrese el código enviado a su correo.”
- “Este código verifica acceso al canal; no reemplaza la revisión del documento.”

Vigencia, longitud e intentos son decisiones provisionales pendientes.

## 9. Solicitud de aclaración

1. Firmante elige “Necesito una aclaración”.
2. La interfaz no interpreta esto como rechazo.
3. Registra evento de pausa/solicitud sin texto clínico sensible en auditoría general.
4. Profesional retoma explicación.
5. Si cambia contenido material, se crea nueva instancia/versionado según corresponda.
6. Si no cambia, se reanuda revisión.

Copy provisional:

- “La firma queda pausada. Un profesional responderá sus preguntas.”

## 10. Rechazo

1. Firmante elige “No acepto”.
2. Sistema explica que la decisión será registrada.
3. Motivo es opcional salvo política legal aprobada.
4. Se confirma rechazo sin exigir firma gráfica salvo decisión jurídica.
5. Se genera constancia `REJECTED`.
6. Se entrega copia.

Copy provisional:

- “He recibido información y decido no aceptar este procedimiento.”
- “Su decisión será registrada en el expediente.”

No usar mensajes intimidatorios ni botones visualmente desbalanceados.

## 11. Representante de menor

1. Sistema detecta que la plantilla/paciente requiere evaluación de representación.
2. Profesional selecciona responsable existente o registra datos permitidos.
3. Confirma relación y fundamento según política.
4. Se captura snapshot del representante.
5. El menor participa mediante flujo de información/asentimiento cuando corresponda.
6. Representante revisa y decide en su propio rol.
7. PDF distingue consentimiento del representante y asentimiento del menor.

Copy provisional:

- “Usted firma en calidad de representante del paciente.”
- “Confirme su relación y facultad para actuar.”

No asumir que todo acudiente es representante legal.

## 12. Testigo e intérprete

1. Plantilla indica si requiere o permite participante adicional.
2. Se identifica rol: testigo o intérprete.
3. Se captura snapshot y declaración propia.
4. Cada participante tiene sesión/evidencia separada.
5. El orden de firma lo define la política.
6. El PDF identifica la función de cada persona.

Copy provisional:

- Testigo: “Declaro haber presenciado el acto indicado.”
- Intérprete: “Declaro haber facilitado la comunicación de manera fiel.”

Estos textos requieren aprobación jurídica.

## 13. Contingencia física

1. Profesional elige “Usar formato físico”.
2. Instancia pasa a `WET_INK_PENDING`.
3. Se imprime la versión exacta con identificador.
4. Se firma en papel.
5. Usuario autorizado escanea el documento completo.
6. Sistema valida archivo, registra fecha declarada, custodio y hash.
7. Se revisa legibilidad.
8. Se cierra como `WET_INK_SCANNED`.
9. La UI lo rotula “Soporte físico incorporado”, nunca “firma electrónica”.

Copy provisional:

- “La evidencia original corresponde a un documento firmado en papel.”

## 14. Revocación

1. Usuario abre un consentimiento `SIGNED` o `WET_INK_SCANNED`.
2. Elige “Registrar revocación”.
3. Verifica al solicitante y su facultad.
4. Muestra original y alcance.
5. Registra decisión posterior y fecha.
6. Genera constancia separada.
7. Conserva original.
8. Estado proyectado pasa a `REVOKED`.

Copy provisional:

- “La revocación no elimina el documento original ni cambia hechos anteriores.”

El efecto jurídico exacto debe revisarse.

## 15. Entrega de copia

Después de firma, rechazo, revocación o contingencia:

1. ofrecer descarga inmediata;
2. registrar resultado;
3. ofrecer enlace seguro si está habilitado;
4. registrar nueva descarga sin duplicar el PDF;
5. permitir entrega física registrada;
6. mantener correo adjunto fuera del MVP hasta evaluación.

Copy provisional:

- “Su copia está disponible para descarga.”
- “El enlace de descarga tendrá vigencia limitada.”

## 16. Errores

| Error | Comportamiento |
| --- | --- |
| sesión inválida/vencida | mensaje uniforme, sin revelar paciente; opción de contactar clínica |
| OTP incorrecto | intento registrado, contador no expuesto con precisión abusiva |
| PDF no generado | no confirmar `SIGNED`; reintento seguro |
| hash inconsistente | bloquear descarga y alertar internamente |
| red perdida antes de confirmar | no asumir firma; consultar idempotencia al reconectar |
| archivo físico ilegible | mantener `WET_INK_PENDING` y solicitar reemplazo |
| participante incorrecto | cancelar sesión y emitir otra; no editar evidencia |

Copy provisional:

- “No fue posible completar la operación. Su decisión no se registró.”
- “Solicite un nuevo enlace a la clínica.”

## 17. Expiración

1. El enlace vence sin decisión.
2. Estado pasa a `EXPIRED`.
3. No se muestra como rechazo.
4. Un reenvío genera sesión nueva y deja trazabilidad.
5. Si cambió contenido, se crea nueva instancia.

Copy provisional:

- “Este enlace venció. La clínica puede enviar uno nuevo.”

## 18. Reenvío

1. Usuario autorizado confirma destino.
2. Sistema registra motivo/canal.
3. Invalida o conserva sesión previa según política aprobada.
4. Emite token/OTP nuevos.
5. No altera contenido ni fecha clínica silenciosamente.
6. Limita frecuencia.

## 19. Abandono

1. Cerrar pestaña, perder foco o no terminar no constituye decisión.
2. Puede registrarse evento técnico mínimo sin contenido.
3. La sesión sigue vigente o expira según política.
4. Al volver se presenta nuevamente contenido exacto.
5. Una firma incompleta no se conserva como firma final.

## 20. Navegación y accesibilidad

- lectura con teclado y lector de pantalla;
- foco visible y orden lógico;
- botones aceptar/rechazar con etiquetas explícitas;
- no depender de color;
- contenido móvil legible;
- firma con alternativa física accesible;
- idioma/país visibles;
- error asociado al campo;
- resumen antes de confirmación;
- retorno seguro al expediente para usuario interno.
