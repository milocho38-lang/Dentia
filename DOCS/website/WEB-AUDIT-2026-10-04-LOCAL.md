# Auditoría local de la website — 2026-10-04

## Alcance

Cambios preparados sobre el release `168ba2f74ec1db2b4ce5b1af2c1d226e82b5655d`. La publicación y el procedimiento manual de privacidad fueron aprobados; este documento no registra ni autoriza la ejecución de supresiones de datos.

## Cambios implementados para revisión

- Propuesta de valor más concreta para odontólogos independientes y prácticas pequeñas.
- Mensaje coherente de lanzamiento y validación; Colombia y Chile se presentan como lugares de validación con prácticas reales, sin atribuir clientes pagos ni prueba social no confirmada.
- Periodontograma general incorporado a la descripción de producto con capacidades verificadas en el release.
- Montos, monedas, promesa de tarifa de lanzamiento y navegación pública de “Precios” retirados. La ruta histórica `/precios` se conserva, pero presenta opciones de servicio y CTA a demostración.
- CTA comercial convertido en enlaces reales a `/demo`.
- Tests contractuales actualizados para impedir la reaparición de montos públicos conocidos o monedas.

Las tarifas existentes permanecen únicamente en la historia y documentación interna previa. Este cambio no modifica precios ni condiciones comerciales.

## Textos legales y operación aprobada

`/privacidad` y `/terminos` contienen los textos aprobados para publicación. La fecha de entrada en vigor se fijó en **3 de octubre de 2026**, según `America/Bogota`; el identificador técnico separado permanece como `DENTIA_PRIVACY_POLICY_V2_2026_10_04`.

La operación aprobada establece:

1. Camilo Andres Medina Romero como responsable y `dentiapro.notificaciones@gmail.com` como canal público.
2. Retención de leads no convertidos durante 12 meses desde el último contacto bilateral documentado o, si no lo hubo, desde `created_at`.
3. Revisión manual por Camilo Andres Medina Romero y Kimberly Astudillo Sánchez antes de cualquier supresión.
4. Revisión coordinada de PostgreSQL y de la copia operativa en Gmail; ninguna supresión se declara completa sin comprobar ambos sistemas.
5. Los backups no se modifican individualmente: expiran mediante la rotación de los 30 paquetes verificados más recientes y toda supresión debe reaplicarse antes de devolver a uso ordinario un backup restaurado.
6. Este procedimiento no ejecuta supresiones por sí solo. Cada caso requiere identidad verificada, alcance exacto, ausencia de excepciones y un comando limitado al UUID revisado y probado con datos sintéticos.

El estado de error del formulario ofrece únicamente el canal público confirmado, sin exponer el destinatario operativo privado.

El destinatario operativo existente de las notificaciones de demo fue confirmado por Camilo únicamente para esa función. No constituye un contacto público ni identifica por sí solo al responsable legal; no debe exponerse en contenido, metadata, bundles, enlaces o mensajes de error.

## Fricción del formulario

El backend exige actualmente nombre, apellido, email, teléfono, país, ciudad, tipo de práctica, número de odontólogos y autorización. Sin modificar el contrato ni fabricar valores, esos ocho datos son el mínimo aceptado. Una reducción real requiere decidir qué campos pueden volverse opcionales y cambiar schema, persistencia y pruebas en un alcance backend separado.

## Medición propuesta, sin proveedor

No se instaló analytics, cookies ni transmisión de datos. Si se aprueba un proveedor y el consentimiento correspondiente, el esquema mínimo puede medir solo:

- `page_view`: ruta y referente limitado al origen, sin query string.
- `cta_select`: identificador estable del CTA y ruta de origen.
- `demo_form_start`: primera interacción, una vez por sesión.
- `demo_form_validation_error`: nombre técnico del campo, nunca su valor.
- `demo_form_submit_result`: `success` o código de error no sensible.

No enviar nombres, correo, teléfono, ciudad, mensaje, identificadores clínicos ni contenido de formularios. Definir primero proveedor, base legal, consentimiento, retención, acceso y mecanismo de exclusión.

## Hallazgos técnicos secundarios

- No hay JSON-LD. No se añadió porque faltan la identidad legal y los datos canónicos necesarios para una entidad pública fiable.
- La CSP permite `unsafe-inline` para scripts y estilos. No se relajó ni se modificó: endurecerla exige diseñar nonces/hashes compatibles con Next.js y verificar todo el runtime.
- La política de caché observada para HTML debe validarse en la capa productiva/CDN antes de cambiarla. No se modificó infraestructura ni headers de caché en este alcance.

## Validación ejecutada

Desde `website/`, sobre Node.js y dependencias bloqueadas por el `package-lock.json` del release:

```text
npm run lint
PASS — ESLint sin errores.

npm run typecheck
PASS — TypeScript (`tsc --noEmit`) sin errores.

npm test
PASS — site-contract-tests, set oficial de 11 capturas y carousel-autoplay-tests.

node scripts/demo-request-form-tests.mjs
PASS — contrato, consentimiento, estados y responsive del formulario.

npm run build
PASS — compilación optimizada y generación estática de 12 rutas.

pytest backend/tests/administration/test_demo_requests.py -q
PASS — 9 pruebas DB-backed sobre PostgreSQL aislado, incluidas V1 sin versión, V2 explícita,
rechazo de versión desconocida, conservación de la versión histórica y deduplicación separada por versión.
```

La revisión manual local cubrió home, Producto, Planes, Seguridad, Demo, Privacidad y Términos en escritorio y viewport móvil `390 × 844`. Se verificaron navegación, menú móvil, CTAs, ausencia de desborde horizontal y ausencia de importes visibles sin enviar el formulario. La búsqueda del artefacto `.next/server` y `.next/static` no encontró los importes ni monedas retirados.

## Fuentes oficiales de los textos legales

Consultadas el 4 de octubre de 2026:

- Colombia — Ley 1581 de 2012: <https://cancilleria.gov.co/normograma/compilacion/docs/ley_1581_2012.htm>
- Colombia — Decreto 1074 de 2015, parte 25: <https://www.cancilleria.gov.co/sites/default/files/Normograma/docs/decreto_1074_2015_pr025.htm>
- Colombia — Decreto 1074 de 2015, parte 26: <https://www.cancilleria.gov.co/sites/default/files/Normograma/docs/decreto_1074_2015_pr026.htm>
- Chile — Ley 19.628, versión vigente consultada: <https://www.bcn.cl/leychile/navegar?idNorma=141599&idVersion=2023-05-09>
- Chile — Ley 21.719 y disposiciones transitorias: <https://www.bcn.cl/leychile/navegar?idNorma=1209272>

La fuente colombiana confirma autorización previa e informada, deber de informar, consultas en diez días hábiles ampliables por cinco, reclamos en quince días hábiles ampliables por ocho y agotamiento del trámite antes de acudir a la Superintendencia de Industria y Comercio. La Ley 19.628 consultada confirma que el artículo 16 regula la vía ante juez civil cuando no hay pronunciamiento en dos días hábiles o existe denegación en los supuestos legales. La Ley 21.719 establece una entrada en vigor futura mediante su regla transitoria; el texto publicado no la presenta como vigente.

## Gate de versión del consentimiento

El protocolo queda cerrado sobre dos versiones conocidas:

- ausencia de `consent_version`: `DENTIA_PRIVACY_POLICY_V1`, para pestañas y formularios antiguos;
- website nueva: `DENTIA_PRIVACY_POLICY_V2_2026_10_04`.

El backend rechaza cualquier versión distinta. La ausencia nunca significa “versión actual” y no depende de una variable mutable de entorno.

La versión efectiva se incluye en la huella de deduplicación. Los mismos datos enviados primero bajo V1 y
luego bajo V2 producen dos evidencias separadas; repetir V2 dentro de la ventana de deduplicación conserva
una sola evidencia V2.

El orden de publicación de la nueva política es:

1. desplegar primero el backend compatible con V1 y V2;
2. desplegar después la website que envía explícitamente V2;
3. comprobar el contrato técnico sin enviar leads ni correos productivos innecesarios; cualquier prueba sintética productiva requiere aprobación y un método que no notifique a terceros.

No requiere migración, cambio de schema ni configuración productiva nueva. No se deben reetiquetar solicitudes históricas ni modificar su consentimiento conservado. Revertir la website hace que las pestañas sin versión vuelvan a V1; el backend nuevo continúa aceptando ambas durante el rollback.
