const CONTROL_CHARACTERS = /[\u0000-\u001f\u007f-\u009f]/g;
const FORMULA_PREFIX = /^[=+\-@]/;

export function sanitizeSpreadsheetCell(value) {
  const withoutControls = String(value).replace(CONTROL_CHARACTERS, " ").trimStart();
  return FORMULA_PREFIX.test(withoutControls) ? `'${withoutControls}` : withoutControls;
}

export function quoteCsvCell(value) {
  const safe = sanitizeSpreadsheetCell(value);
  return `"${safe.replaceAll('"', '""')}"`;
}

export function buildPatientImportCsv(rows) {
  return rows.map((row) => row.map(quoteCsvCell).join(",")).join("\r\n");
}
