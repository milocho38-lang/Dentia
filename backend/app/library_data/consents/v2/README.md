# Dentia Consent Library — LIB1 NORM4

Paquete local v2 de la Biblioteca Dentia para C019A.4-LIB1.

## Contrato

- `source_text` conserva el texto de procedencia y nunca debe renderizarse al paciente.
- `normalized_content_markdown` y `content` son el contenido Markdown restringido visible al paciente.
- `content` debe coincidir exactamente con `normalized_content_markdown`.
- `normalization_schema_version` es `LIB1_NORM_V2_CONTEXTUAL`.
- Ninguna versión queda aprobada automáticamente. Todas permanecen en `PENDING_EQUIVALENCE_REVIEW`.

## Clasificación contextual NORM4

NORM4 diferencia entre:

- adulto en nombre propio;
- texto adulto/representante que requiere decisión humana;
- representante real o flujo pediátrico;
- documentos especiales;
- documentos que no requieren firma.

Las propuestas de variante adulta se registran únicamente en el reporte NORM4. No se importan como versiones publicadas ni aprobadas.

## Reportes

- `DOCS/product/C019A4-LIB1-NORM4-Report.json`
- `DOCS/product/C019A4-LIB1-NORM4-Human-Review.md`
- `DOCS/product/C019A4-LIB1-NORM4-Human-Review.html`
