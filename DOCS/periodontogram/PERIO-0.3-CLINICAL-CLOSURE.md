# PERIO-0.3 — Cierre clínico definitivo del Periodontograma

**Estado:** `CLINICAL_CONTRACT_CLOSED`

**Fecha:** 2026-09-22

**Alcance:** decisiones clínicas definitivas previas a PERIO-1. Este documento no implementa código, no autoriza RBAC y no crea migraciones.

## 1. Precedencia

Este cierre tiene precedencia clínica sobre PERIO-0, PERIO-0.1 y las propuestas pendientes de PERIO-0.2. El contrato funcional y la adenda PERIO-0.2 ya incorporan estas decisiones.

Los cuestionarios y alternativas anteriores se conservan como evidencia histórica, pero quedan `SUPERSEDED` cuando contradigan este documento.

## 2. Convención definitiva de GM y CAL

Estado: `APPROVED_BY_CLINICIAN`.

- GM negativo: encía desplazada hacia la raíz/apical.
- GM positivo: encía desplazada hacia la corona.
- GM cero: punto de referencia medido.
- Fórmula canónica: `CAL = PD - GM`.

Ejemplos canónicos:

```text
PD = 4 mm, GM = -2 mm → CAL = 6 mm
PD = 4 mm, GM = +2 mm → CAL = 2 mm
```

PD y GM se registran como milímetros enteros. CAL lo calcula Dentia. Cero nunca significa “no medido”; una medición ausente se representa con `null` o ausencia según el modelo autorizado en PERIO-1.

Quedan superseded:

- `CAL = PD + GM`;
- GM positivo como recesión/desplazamiento apical;
- GM negativo como margen coronal;
- cualquier uso de cero como sustituto de una medición ausente.

## 3. Bolsas periodontales

Estado: `APPROVED_BY_CLINICIAN`.

- Todo sitio con `PD >= 4 mm` se destaca visualmente como bolsa periodontal.
- Es una ayuda visual basada en la medición.
- No produce diagnóstico automático, clasificación de enfermedad ni recomendación terapéutica.
- El diagnóstico permanece bajo responsabilidad explícita del profesional.

## 4. Furcación MVP

Estado: `APPROVED_BY_CLINICIAN`.

- Aplica solo a molares elegibles.
- Registra presencia/ausencia, sin grados.
- Si está presente, permite marcar mesial, distal o ambas.
- La UI y el gráfico deben poder rellenar o señalar M y D por separado.

Quedan fuera del MVP las ubicaciones vestibular y palatina/lingual, y los grados I/II/III.

## 5. Corrección de un examen finalizado

Estados: `APPROVED_USER_EXPERIENCE` y `DENTIA_INTERNAL_TRACEABILITY_REQUIRED`.

Experiencia clínica:

```text
Periodontograma finalizado → Corregir → editar → guardar/finalizar
```

Contrato interno:

- el original no se sobrescribe silenciosamente;
- se conserva la versión anterior;
- la corrección crea una versión vinculada;
- se registran actor, fecha y motivo cuando el patrón clínico aplicable lo requiera;
- el profesional no necesita entender el versionado técnico.

## 6. Historial y comparación

Estado: `APPROVED_BY_CLINICIAN`.

El historial MVP muestra únicamente:

- fecha;
- profesional;
- estado;
- acción `Ver`.

No incluye `Comparar`. La comparación de dos periodontogramas se clasifica como `POST_MVP / HIGH_PRIORITY`. La arquitectura debe conservar snapshots suficientes para implementarla posteriormente sin alterar los exámenes históricos.

## 7. Nuevo examen y datos anteriores

- Cada periodontograma nuevo registra nuevamente sus mediciones.
- No se copian ni precargan como datos nuevos PD, GM, BOP, placa, movilidad o furcación.
- El historial anterior permanece disponible solo para consulta.
- Materializar el estado dental vigente desde el odontograma no equivale a copiar mediciones periodontales.

## 8. Gráfico periodontal MVP

Estado: `MVP_REQUIRED`.

El diseño propio de Dentia debe representar de forma clínica, simple y legible:

- piezas permanentes, ausencias e implantes;
- PD, GM y CAL;
- BOP y placa;
- furcación M/D;
- bolsas `PD >= 4 mm`.

El gráfico es una proyección de los datos y no una segunda fuente editable. No debe copiar exactamente el diseño de herramientas externas.

## 9. Dentición, sitios y recorrido

Estado: `APPROVED_BY_CLINICIAN`.

- MVP exclusivo para dentición permanente.
- Incluye terceros molares presentes: 18, 28, 38 y 48.
- Excluye dentición temporal y mixta.
- Usa seis sitios por diente natural o implante: distal, medio y mesial en vestibular; distal, medio y mesial en palatino/lingual.
- Maxilar: 18 → 28.
- Mandíbula: 48 → 38.
- Lado derecho: distal → medio → mesial.
- Lado izquierdo: mesial → medio → distal.

## 10. Movilidad e implantes

Estado: `APPROVED_BY_CLINICIAN`.

Movilidad:

- valores exclusivos 0, 1, 2 y 3;
- grado 0 registrable explícitamente;
- sin campos horizontal/vertical separados;
- no aplica a implantes.

Implantes:

- mismos seis sitios;
- PD, GM, BOP, placa y supuración;
- sin movilidad;
- representación de raíz claramente diferenciada como implante;
- BOP y placa participan en los indicadores generales.

## 11. Indicadores y completitud

Estado: `APPROVED_BY_CLINICIAN`.

Indicadores obligatorios del MVP:

- `% BOP`;
- `% placa`.

El denominador incluye solo sitios efectivamente evaluados. Un sitio no medido no se cuenta como negativo. PD media, CAL media y rangos no son KPI obligatorios del MVP.

El examen puede finalizarse parcialmente. Dentia muestra cobertura y advierte si está incompleto, pero no bloquea la finalización por no alcanzar el 100 %.

## 12. Integración clínica

- El periodontograma es un registro clínico independiente.
- Puede vincularse opcionalmente a una evolución.
- No crea una evolución automáticamente.
- No emite diagnóstico periodontal automático.

## 13. Alcance cerrado

### MVP

- dentición permanente y terceros molares presentes;
- seis sitios;
- PD, GM, CAL, BOP, placa y supuración;
- movilidad 0–3 en dientes naturales;
- furcación M/D sin grados;
- implantes sin movilidad;
- indicadores `% BOP` y `% placa` sobre sitios evaluados;
- cobertura y finalización parcial con advertencia;
- gráfico periodontal obligatorio;
- resalte visual `PD >= 4 mm`;
- historial simple con `Ver`;
- corrección simple con versionado interno e inmutabilidad del original;
- vínculo opcional con evolución.

### Post-MVP

- comparación de dos periodontogramas, con prioridad alta;
- PDF con mediciones, gráfico, paciente/remisión y datos profesionales;
- dentición temporal o mixta;
- ubicaciones o grados adicionales de furcación;
- voz, tendencias, índices y métricas avanzadas.

## 14. Decisiones superseded

Quedan expresamente sin vigencia:

- `CAL = PD + GM` y su convención de signos asociada;
- furcación vestibular o palatina/lingual en el MVP;
- grados de furcación en el MVP;
- acción `Comparar` dentro del historial MVP;
- copia o precarga de mediciones del examen anterior;
- bloqueo de finalización por cobertura inferior al 100 %;
- PDF como requisito del MVP;
- cualquier diagnóstico periodontal automático.

## 15. Gate clínico

No quedan preguntas clínicas que impidan definir el modelo base de PERIO-1.

`READY_FOR_PERIO_1`

La matriz RBAC, las migraciones y la implementación continúan requiriendo autorización separada.
