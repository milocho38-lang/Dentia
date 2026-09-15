# ORT-6 — Plan de piloto clínico de Ortodoncia

## Propósito

Validar terminología, velocidad y fidelidad clínica del módulo ya protegido por
ORT-1–5. Este documento no habilita producción ni ejecuta el piloto.

## Participantes y entorno

- un odontólogo con práctica real en Ortodoncia;
- un observador de producto de Dentia;
- opcionalmente un administrador de clínica para validar seats y handoff;
- tenant piloto aislado, entitlement explícito y un assignment activo;
- primera ronda solo con pacientes sintéticos; datos reales únicamente mediante
  autorización, consentimiento y controles operativos aprobados.

Duración sugerida: dos sesiones de 60–90 minutos y una semana de uso controlado.
El feature gate es el entitlement + seat existente; no se crea otro flag.

## Flujo a probar

1. Habilitar entitlement y asignar cupo.
2. Abrir paciente sintético e iniciar caso.
3. Activar caso y completar plan/aparatología.
4. Crear una evolución estructurada, guardar draft y firmar.
5. Comprobar resumen y timeline general.
6. Crear la ficha, completar secciones relevantes y finalizar V1.
7. Crear V2 desde V1 y comprobar lineage/historia.
8. Suspender, verificar modo read-only y reactivar.
9. Cambiar responsable a otro ortodoncista válido.
10. Completar un caso y crear otro caso futuro separado.
11. Repetir interrupción con motivo obligatorio.
12. Retirar seat/entitlement y verificar conservación histórica sin escritura.

## Medición de usabilidad

- tiempo y número de clicks para evolución y ficha;
- campos repetitivos o difíciles de encontrar;
- utilidad de dropdowns y opciones custom;
- uso en desktop y tablet horizontal;
- claridad de errores de concurrencia, caso suspendido/cerrado y seat retirado;
- capacidad de regresar desde Ortodoncia a Historia Clínica general.

## Preguntas clínicas

- ¿Los campos de alineadores y elásticos representan la práctica real?
- ¿Cómo debe registrarse la medida/unidad de microtornillos?
- ¿ATM, Jarabak y clase esqueletal son single o multi?
- ¿Qué unidades deben exigirse en cefalometría, CPI y vía aérea?
- ¿Qué alertas deben ser estructuradas?
- ¿“Sin cambios” debe conservar valores previos o ser un registro explícito?
- ¿Una adenda legal debe permitirse después de retirar entitlement/seat y bajo
  qué autorización excepcional?
- ¿Una adenda corrige el resumen vigente o solo aclara la historia?

## Criterios de aceptación

- lifecycle comprendido sin explicación técnica;
- cero pérdida o mutación de historia firmada/finalizada;
- resumen coincide con la última evolución firmada;
- campos pendientes quedan clasificados por el odontólogo;
- tareas principales utilizables en tablet y desktop;
- cross-tenant, RBAC, scope y concurrencia permanecen verdes;
- no aparecen códigos internos ni errores 500;
- decisión explícita sobre las dos políticas de adenda pendientes.

## Rollback operativo

El piloto se detiene deshabilitando el entitlement o revocando assignments. Esa
acción bloquea nuevas escrituras y conserva toda la historia. No se eliminan
casos, evoluciones, fichas, catálogos ni auditoría. La reanudación requiere una
habilitación y asignación explícitas.

## Fuera del piloto

No incluye pricing, billing, PDF ortodóncico, integración con Treatment,
periodontograma, scanner, IA, cefalometría automática, RIPS ni cambios a la
Historia Clínica general.
