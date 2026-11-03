# Catálogo inicial de procedimientos

El lote inicial contiene exclusivamente las 173 filas `NO_CHANGE` conciliadas del Excel
definitivo de Kimberly (`source_sha256` del manifiesto:
`1d77bd1c0723fdfaf05e57f78dd4aed15f04eabc95797a2f7589b1446c8de5df`). Las 311 filas
restantes permanecen en el manifiesto de revisión y no se cargan automáticamente.
La versión con precios fijos por país es
`KIMBERLY-2026-11-03-FIXED-CLP-COP-173-V2`; la huella aprobada cubre versión, SHA de
origen, base histórica COP y las 173 filas completas.
La huella también se registra en la procedencia de cada fila nueva y en el evento de
auditoría de la carga; no se reescribe en filas históricas existentes.

La carga usa inserción PostgreSQL `ON CONFLICT DO NOTHING` sobre el nombre normalizado:
agrega faltantes, nunca actualiza ni elimina procedimientos existentes y puede repetirse.
Nuevas empresas reciben el lote durante onboarding cuando
`PROCEDURE_CATALOG_SEED_ENABLED=true`. Para empresas existentes se ejecuta por empresa:

```bash
PYTHONPATH=backend python -m app.cli.seed_procedure_catalog \
  --company-id <UUID_EMPRESA> --actor-id <UUID_USUARIO> --dry-run
```

Para Colombia se usa el precio COP fijo aprobado en el mismo manifiesto. Primero se
ensaya y luego se repite sin `--dry-run`; no se recibe ni consulta una tasa durante la
carga:

```bash
PYTHONPATH=backend python -m app.cli.seed_procedure_catalog \
  --company-id <UUID_EMPRESA_CO> --actor-id <UUID_USUARIO_CO> \
  --dry-run
```

Chile conserva los valores fuente CLP. Colombia utiliza los valores COP fijos que ya
fueron aprobados y publicados: se calcularon una sola vez con 1 CLP = 3,291243 COP,
fuente XE y observación 2026-11-03T03:33:00Z, con redondeo al millar COP más cercano.
La huella inmutable del manifiesto impide cargar un lote modificado o incompleto.
La procedencia guarda moneda y valor usados al importar (`generated_currency` y
`generated_value`) exclusivamente como origen histórico del número; no representan la
moneda vigente de la clínica ni provocan conversiones posteriores.
Si el país está ausente o no es Chile/Colombia, el onboarding continúa pero omite la
precarga y registra `PROCEDURE_CATALOG_SEED_SKIPPED`; la aplicación sigue mostrando
`moneda local`. La CLI se detiene con un mensaje explícito y nunca infiere Colombia.

Dentia no maneja contabilidad multimoneda. Tratamientos, presupuestos, pagos, cartera y
reportes mantienen sus sumas originales sin conversiones, filtros ni snapshots monetarios.
La moneda es solamente una etiqueta derivada del país actual de la empresa: Chile muestra
`CLP`, Colombia `COP` y cualquier otro país muestra `moneda local`. Esta etiqueta también
se aplica a datos históricos y PDF sin modificar sus importes.
Cambiar el país de la empresa reetiqueta todos los valores visibles según el país nuevo,
pero conserva exactamente los mismos números y la procedencia original del catálogo.

## Habilitación para clínicas nuevas

La única configuración operativa es `PROCEDURE_CATALOG_SEED_ENABLED=true`. No se deben
configurar tasas ni fechas: el alta selecciona `source_price_clp` para Chile y
`suggested_price_cop` para Colombia directamente desde el manifiesto aprobado. Un país
ausente o distinto no infiere moneda, no bloquea el alta y registra la omisión auditada.

Plan de despliegue seguro:

1. Publicar primero el código con la bandera todavía deshabilitada y comprobar salud,
   revisión de migración y huella del manifiesto.
2. Crear y restaurar temporalmente un respaldo completo.
3. Habilitar solamente `PROCEDURE_CATALOG_SEED_ENABLED=true`, recrear el backend y
   comprobar un alta sintética CL y otra CO en un entorno aislado equivalente.
4. Mantener el backfill de clínicas existentes como operación explícita e idempotente;
   nunca actualizar ni eliminar filas que ya existan.
5. Ante un manifiesto inválido, conservar la bandera deshabilitada o volver al código
   anterior. La validación ocurre antes de insertar y el alta completa se revierte.
