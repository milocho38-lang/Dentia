# C019A.5 — Arquitectura del consentimiento en papel

Estado: implementado localmente, pendiente de validación manual y aprobación.

## Decisión

`ConsentInstance` continúa siendo la única raíz clínica. El canal de finalización se identifica con `completion_channel` (`ELECTRONIC` o `PAPER`). El canal papel añade un `ConsentPaperPacket` inmutable por instancia y una colección ordenada de `ConsentPaperPage`.

```text
ConsentInstance revisado
  ├─ ELECTRONIC → OTP/declaraciones/firma → ConsentAcceptance
  └─ PAPER      → packet impreso → firma física → páginas → PDF sellado
```

No se crean eventos clínicos nuevos ni una segunda copia del snapshot. El packet usa el contenido, paciente, firmante, contexto y profesional ya congelados en la instancia.

## Máquina de estados

- `READY_FOR_REVIEW`, sin canal: disponible para elegir método.
- `PENDING_SIGNATURE` + `PAPER` + `PRINTED`: packet generado.
- `PENDING_SIGNATURE` + `PAPER` + `SIGNED_PENDING_DIGITIZATION`: original físico reportado como firmado.
- `PENDING_SIGNATURE` + `PAPER` + `DIGITIZING`: páginas en preparación.
- `SIGNED` + `PAPER` + `FINALIZED`: copia digital verificada y sellada.

El canal electrónico activo puede cambiar a papel antes de la aceptación: todas sus sesiones, OTP y sesiones públicas son revocadas. Una vez creado el packet no se permite volver silenciosamente a electrónico ni regenerar el mismo packet. Una instancia finalizada por cualquier canal no admite el otro.

## Storage e integridad

Los objetos usan claves aleatorias bajo `consents/paper/{empresa}/{instancia}/{packet}`. No incluyen PII ni nombres aportados por el usuario. El packet de impresión, cada página normalizada y el PDF final tienen SHA-256. El PDF final no se reemplaza: una corrección posterior exige anulación/nueva instancia según el flujo administrativo aplicable.

PDF multipágina se divide en páginas PDF independientes. JPEG/PNG se valida con Pillow y se convierte a una página PDF. PyMuPDF valida, divide, previsualiza y consolida. No hay OCR ni reescritura clínica.

## Límites

- 15 MB por archivo.
- 50 MB por expediente.
- 50 páginas.
- 40 millones de píxeles por imagen.
- PDF cifrado, SVG, HTML y contenido desconocido: rechazados.

## Acceso

Los permisos `consent.paper.*` pertenecen a roles empresariales autorizados. `PLATFORM_ADMIN` no los recibe. Toda consulta vuelve a validar empresa, sede autorizada, instancia y packet; las rutas nunca exponen rutas físicas.
