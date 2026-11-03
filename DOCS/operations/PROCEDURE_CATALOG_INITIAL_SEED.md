# Catálogo inicial de procedimientos

El lote inicial contiene exclusivamente las 173 filas `NO_CHANGE` conciliadas del Excel
definitivo de Kimberly (`source_sha256` del manifiesto:
`1d77bd1c0723fdfaf05e57f78dd4aed15f04eabc95797a2f7589b1446c8de5df`). Las 311 filas
restantes permanecen en el manifiesto de revisión y no se cargan automáticamente.

La carga usa inserción PostgreSQL `ON CONFLICT DO NOTHING` sobre el nombre normalizado:
agrega faltantes, nunca actualiza ni elimina procedimientos existentes y puede repetirse.
Nuevas empresas reciben el lote durante onboarding cuando
`PROCEDURE_CATALOG_SEED_ENABLED=true`. Para empresas existentes se ejecuta por empresa:

```bash
PYTHONPATH=backend python -m app.cli.seed_procedure_catalog \
  --company-id <UUID_EMPRESA> --actor-id <UUID_USUARIO> --dry-run
```

Para Colombia, primero ensayar y luego repetir sin `--dry-run` con una tasa vigente:

```bash
PYTHONPATH=backend python -m app.cli.seed_procedure_catalog \
  --company-id <UUID_EMPRESA_CO> --actor-id <UUID_USUARIO_CO> \
  --clp-cop-rate <TASA_VIGENTE> \
  --rate-source '<URL_O_REFERENCIA_DE_LA_FUENTE>' \
  --rate-observed-at-utc '<YYYY-MM-DDTHH:MM:SSZ>' \
  --dry-run
```

Chile conserva los valores fuente CLP. Colombia requiere una tasa CLP/COP vigente,
fuente y fecha UTC; la conversión ocurre una sola vez al generar el catálogo y redondea
al millar COP. La tasa de referencia de pruebas no puede utilizarse en una carga real.
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
