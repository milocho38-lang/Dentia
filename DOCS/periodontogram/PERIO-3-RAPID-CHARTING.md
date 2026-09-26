# PERIO-3 — Captura rápida y ergonomía clínica

## Alcance

PERIO-3 convierte el editor clínico básico de PERIO-2 en un recorrido continuo de captura periodontal. No cambia el modelo, la semántica clínica, RBAC, snapshots ni persistencia: continúa usando el `PATCH` batch con `row_version` definido en PERIO-2 y no requiere migración.

No se incorporan gráfico periodontal avanzado, curvas, comparación longitudinal, PDF, voz, diagnóstico automático, índices adicionales ni secuencia configurable; esas decisiones permanecen fuera de este alcance y la visualización avanzada corresponde a PERIO-4.

## Recorrido clínico

Las arcadas se presentan en scrollers horizontales locales, sin generar overflow global:

- Maxilar: `18 → 17 → … → 27 → 28`.
- Mandíbula: `48 → 47 → … → 37 → 38`.

En cada pieza se recorren primero los tres sitios vestibulares y luego los tres palatinos —en maxilar— o linguales —en mandíbula—:

- Cuadrantes derechos 1 y 4: distal → medio → mesial.
- Cuadrantes izquierdos 2 y 3: mesial → medio → distal.

La secuencia excluye piezas `ABSENT`. Las piezas `PRESENT` e `IMPLANT` conservan seis sitios activos. Los rótulos usan “Distal”, “Medio” y “Mesial” completos para evitar confundir medio con mesial.

## Modos y navegación

El profesional puede seleccionar:

- `PD`: recorre únicamente profundidad de sondaje.
- `GM`: recorre únicamente margen gingival.
- `PD + GM`: intercala ambas mediciones sitio por sitio.

El contexto sticky identifica pieza, cara, sitio y medición activos. El foco puede ubicarse directamente con click o tap y el recorrido continúa desde ese punto.

- `Enter` valida el campo no vacío y avanza al siguiente objetivo del modo activo.
- `Shift+Tab` conserva el retroceso nativo del navegador.
- `Backspace` en un input ya vacío vuelve al objetivo anterior.
- No se registran listeners globales ni se interceptan teclas fuera de los inputs numéricos.

PD usa teclado numérico y GM admite signo negativo. Los inputs son nativos, tienen foco visible y etiquetas accesibles que expresan pieza, cara, sitio y medición.

## Captura clínica rápida

BOP, placa y supuración usan controles tri-state compactos:

`No evaluado → No → Sí → No evaluado`.

Así, `null` permanece distinto de `false`. Supuración solo aparece en implantes. Movilidad usa un control segmentado `No evaluado / 0 / 1 / 2 / 3` y solo aparece en dientes naturales presentes. Furcación M/D aparece únicamente en molares elegibles y conserva semántica tri-state.

Los estados `PRESENT`, `ABSENT` e `IMPLANT` son controles separados de los roles y del odontograma. Un cambio con información clínica requiere confirmación antes de limpiar el borrador. Una pieza ausente queda atenuada y sin sitios editables; el implante tiene identificación visual propia y no ofrece movilidad ni furcación.

La nota clínica por pieza se mantiene porque está expresamente respaldada por PERIO-0.2, sección 17, y por el contrato de PERIO-2. Se presenta como detalle secundario colapsable, no como eje principal de la captura.

## Derivaciones en vivo

CAL se calcula en frontend con la misma regla clínica del backend:

`CAL = PD - GM`.

Ejemplos:

- `PD 4`, `GM -2` → `CAL 6`.
- `PD 4`, `GM +2` → `CAL 2`.

CAL no es editable. Un `PD >= 4 mm` recibe un marcador visual con el texto accesible “PD mayor o igual a 4 milímetros”; no se interpreta como diagnóstico.

La cabecera muestra cobertura, BOP, placa y estado del examen. Los denominadores de BOP y placa incluyen solo sitios evaluados; cuando no existe denominador se muestra `—`, nunca un 0 % ficticio. Las piezas ausentes no participan en cobertura ni índices.

## Guardado y concurrencia

La decisión de PERIO-3 es conservar guardado explícito. El editor mantiene todos los cambios locales de varias piezas y envía un solo batch al seleccionar “Guardar cambios”; no existe request por tecla ni autosave temporizado.

La UI muestra:

- `Cambios sin guardar`;
- `Guardando…`;
- `Guardado`.

Cerrar con cambios pendientes solicita confirmación y finalizar queda bloqueado hasta guardar. El request mantiene `row_version`, límites de 32 dientes y 192 sitios, confirmación de limpieza y manejo de conflictos `409` existentes. El autosave con debounce queda diferido porque puede introducir conflictos de versión y pérdida de contexto sin una mejora clínica validada.

## Responsive y rendimiento

Desktop es la prioridad y la composición está preparada para 1280, 1440 y 1920 px. Cada arcada usa scroll horizontal local, mantiene visibles los números FDI y evita ampliar el viewport completo. Tablet conserva controles táctiles y edición completa mediante los mismos scrollers.

En móvil se priorizan consulta, contexto sticky y edición focal de una pieza; no se intenta comprimir 32 piezas en 390 px. La captura completa móvil es posible mediante scroll local, pero no es la prioridad clínica del MVP.

El estado se organiza por pieza y las derivaciones se calculan en memoria sobre un máximo fijo de 32 piezas y 192 sitios. La red solo interviene al guardar el lote; no existe patrón N+1 ni request por input.

## Accesibilidad

- Inputs `number` nativos con `inputMode` apropiado.
- Foco visible en inputs y controles.
- Labels accesibles con pieza, cara, sitio y medición.
- Estado activo y estados tri-state no dependen únicamente del color.
- Controles de pieza y modo exponen `aria-pressed`.
- Cambios guardados/sin guardar y contexto activo usan regiones informativas legibles.
- La interacción no depende de hover.

## Pruebas

`periodontogram-rapid-charting-tests.mjs` cubre:

- orden maxilar 18→28 y mandibular 48→38;
- distal/medio/mesial en lado derecho y mesial/medio/distal en lado izquierdo;
- modos PD, GM y PD+GM, incluida exclusión de ausentes;
- CAL con margen negativo y positivo;
- umbral de bolsa en PD 3, 4 y 5;
- ciclo tri-state y diferencia `null`/`false`;
- cobertura e índices con naturales, implantes y ausentes;
- presencia de navegación Enter, Shift+Tab, Backspace, labels accesibles y guardado batch sin autosave.

Las pruebas de PERIO-1/2 siguen cubriendo lifecycle, validaciones del modelo, implantes, supuración, movilidad, furcación, snapshots, hash, inmutabilidad, tenant, sede y RBAC.

## Decisiones diferidas

PERIO-4 deberá validar y diseñar la representación periodontal avanzada —incluidos gráfico, curvas y comparación visual— sin cambiar el contrato clínico congelado. También queda diferida cualquier secuencia configurable o captura por voz hasta contar con validación clínica específica.
