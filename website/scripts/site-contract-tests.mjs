import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const read = (path) => readFileSync(resolve(root, path), "utf8");

const pages = {
  home: read("app/page.tsx"),
  product: read("app/producto/page.tsx"),
  pricing: read("app/precios/page.tsx"),
  security: read("app/seguridad/page.tsx"),
  demo: read("app/demo/page.tsx"),
};
const source = Object.values(pages).join("\n");

for (const route of ["/producto", "/precios", "/seguridad", "/demo"]) {
  assert.match(read("lib/site.ts"), new RegExp(route.replace("/", "\\/")), `Missing navigation route ${route}`);
}

assert.match(read("lib/site.ts"), /https:\/\/app\.dentiapro\.com/, "The app login origin must remain canonical");
assert.match(pages.home, /Toda tu consulta odontológica en un solo lugar\./);
assert.match(pages.home, /En validación con prácticas odontológicas reales en Colombia y Chile\./);
assert.match(pages.product, /Agenda/);
assert.match(pages.product, /Odontograma/);
assert.match(pages.product, /Configuración y gestión de plantillas de consentimientos/);

for (const price of ["$85.000 COP", "$168.000 COP", "$252.000 COP", "$420.000 COP"]) {
  assert.ok(pages.pricing.includes(price), `Missing Colombia price ${price}`);
}
for (const price of ["$23.900 CLP", "$47.900 CLP", "$70.900 CLP", "$118.900 CLP"]) {
  assert.ok(pages.pricing.includes(price), `Missing Chile price ${price}`);
}
assert.match(pages.pricing, /impuestos aplicables incluidos/);
assert.match(pages.pricing, /tarifa especial de lanzamiento/);

assert.match(pages.security, /Separación entre organizaciones/);
assert.match(pages.security, /Usuarios, roles y permisos/);
assert.match(pages.security, /Conexiones protegidas/);
assert.match(pages.security, /Trazabilidad de acciones críticas/);

const demoForm = read("components/DemoForm.tsx");
for (const field of ["demo-name", "demo-email", "demo-phone", "demo-country", "demo-practice", "demo-dentists", "demo-message"]) {
  assert.ok(demoForm.includes(`htmlFor=\"${field}\"`), `Missing accessible label for ${field}`);
}
assert.match(demoForm, /type="submit" disabled/, "Demo submission must remain disabled until a safe lead channel exists");
assert.match(demoForm, /no transmite ni almacena información/);

const prohibitedClaims = [
  /100\s*% legal/i,
  /cumplimiento garantizado/i,
  /firma digital certificada/i,
  /seguridad bancaria/i,
  /imposible de hackear/i,
  /HIPAA/i,
  /líder del mercado/i,
  /miles de usuarios/i,
  /RIPS automático/i,
  /CUV automático/i,
  /facturación electrónica/i,
  /WhatsApp automático/i,
];
for (const claim of prohibitedClaims) {
  assert.doesNotMatch(source, claim, `Prohibited or unsupported claim found: ${claim}`);
}

const assetDirectory = resolve(root, "assets/screenshots");
const expectedAssets = [
  "hero-dashboard.png",
  "home-agenda.png",
  "home-pacientes.png",
  "home-historia-clinica.png",
  "home-odontograma.png",
  "home-tratamientos.png",
  "home-presupuesto.png",
  "home-consentimientos.png",
  "home-finanzas.png",
  "home-seguimientos.png",
  "home-configuracion.png",
];
const pngAssets = readdirSync(assetDirectory).filter((name) => name.endsWith(".png")).sort();
assert.deepEqual(pngAssets, [...expectedAssets].sort(), "The official marketing set must contain exactly 11 PNG files");

const manifest = read("assets/screenshots/manifest.txt");
for (const filename of expectedAssets) {
  const path = resolve(assetDirectory, filename);
  assert.ok(existsSync(path), `Missing screenshot ${filename}`);
  const hash = createHash("sha256").update(readFileSync(path)).digest("hex");
  const size = statSync(path).size;
  assert.match(manifest, new RegExp(`${filename.replace(".", "\\.")} \\| \\d+x\\d+ \\| ${size} \\| ${hash}`));
}

assert.match(read("app/robots.ts"), /siteIsIndexable/);
assert.match(read("app/sitemap.ts"), /\/producto/);
assert.match(read("app/globals.css"), /prefers-reduced-motion/);

console.log("site-contract-tests OK");
console.log(`official-screenshots ${expectedAssets.length}/11`);
