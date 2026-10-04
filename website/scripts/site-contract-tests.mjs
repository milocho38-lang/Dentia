import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const read = (path) => readFileSync(resolve(root, path), "utf8");
const publicSourceDirectories = ["app", "components", "lib"];
const approvedPublicEmails = new Set(["dentiapro.notificaciones@gmail.com"]);

function sourceFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) return sourceFiles(path);
    return /\.(?:ts|tsx|js|jsx)$/.test(entry.name) ? [path] : [];
  });
}

const pages = {
  home: read("app/page.tsx"),
  product: read("app/producto/page.tsx"),
  pricing: read("app/precios/page.tsx"),
  security: read("app/seguridad/page.tsx"),
  demo: read("app/demo/page.tsx"),
  privacy: read("app/privacidad/page.tsx"),
  terms: read("app/terminos/page.tsx"),
};
const source = Object.values(pages).join("\n");
const carousel = read("components/ProductCarousel.tsx");
const carouselAutoplay = read("lib/carouselAutoplay.ts");
const globalStyles = read("app/globals.css");

for (const route of ["/producto", "/precios", "/seguridad", "/demo"]) {
  assert.match(read("lib/site.ts"), new RegExp(route.replace("/", "\\/")), `Missing navigation route ${route}`);
}

assert.match(read("lib/site.ts"), /https:\/\/app\.dentiapro\.com/, "The app login origin must remain canonical");
assert.match(pages.home, /Tu consulta, del primer contacto al seguimiento, en un solo contexto\./);
assert.match(pages.home, /En lanzamiento y validación con prácticas odontológicas reales en Colombia y Chile\./);
assert.match(pages.home, /<ProductCarousel \/>/, "The compact home must render the product carousel");
assert.doesNotMatch(pages.home, /story-stack|journey__step/, "The old repeated vertical product story must be removed");
assert.doesNotMatch(pages.home, /Ortodoncia/, "Orthodontics must not be marketed from the home");
assert.match(pages.product, /Agenda/);
assert.match(pages.product, /Odontograma/);
assert.match(pages.product, /periodontograma general/i);
assert.match(pages.product, /Configuración y gestión de plantillas de consentimientos/);

const publicSources = publicSourceDirectories.flatMap((directory) =>
  sourceFiles(resolve(root, directory)),
);
for (const path of publicSources) {
  const publicSource = readFileSync(path, "utf8");
  assert.doesNotMatch(
    publicSource,
    /\$\s*[\d.]+|\b(?:COP|CLP|USD)\b|tarifa especial|\b(?:85\.000|168\.000|252\.000|420\.000|23\.900|47\.900|70\.900|118\.900)\b/i,
    `Public pricing details must remain hidden: ${path}`,
  );
  const publicEmails = publicSource.match(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/g) ?? [];
  for (const email of publicEmails) {
    assert.ok(approvedPublicEmails.has(email.toLowerCase()), `Unapproved public email found in ${path}`);
  }
}
assert.match(pages.pricing, /Práctica independiente/);
assert.match(pages.pricing, /Consultorio o clínica/);
assert.match(pages.pricing, /Conocer Dentia y la propuesta/);

assert.match(pages.security, /Separación entre organizaciones/);
assert.match(pages.security, /Usuarios, roles y permisos/);
assert.match(pages.security, /Conexiones protegidas/);
assert.match(pages.security, /Trazabilidad de acciones críticas/);

const demoForm = read("components/DemoForm.tsx");
for (const field of ["demo-name", "demo-last-name", "demo-email", "demo-phone", "demo-country", "demo-city", "demo-practice", "demo-dentists", "demo-message"]) {
  assert.ok(demoForm.includes(`htmlFor=\"${field}\"`), `Missing accessible label for ${field}`);
}
assert.match(demoForm, /fetch\("\/api\/public\/demo-requests"/, "The demo form must use the same-origin public endpoint");
assert.match(demoForm, /privacyConsent/);
assert.match(demoForm, /Solicitud recibida/);
assert.doesNotMatch(demoForm, /no transmite ni almacena información/);
assert.match(demoForm, /No incluyas información de pacientes\./);
assert.match(demoForm, /Autorizo a Camilo Andres Medina Romero/);
assert.match(demoForm, /dentiapro\.notificaciones@gmail\.com/);
assert.match(demoForm, /DENTIA_PRIVACY_POLICY_V2_2026_10_04/);
assert.match(demoForm, /consent_version: DEMO_CONSENT_VERSION/);

assert.doesNotMatch(pages.privacy, /borrador|pendiente de revisión|se incorporará el día de la publicación/i);
assert.doesNotMatch(pages.terms, /borrador|pendiente de revisión|se incorporará el día de la publicación/i);
assert.match(pages.privacy, /<strong>Versión:<\/strong> DENTIA_PRIVACY_POLICY_V2_2026_10_04/);
assert.match(pages.privacy, /<strong>Fecha de entrada en vigor:<\/strong> 3 de octubre de 2026\./);
assert.match(pages.terms, /<strong>Fecha de entrada en vigor:<\/strong> 3 de octubre de 2026\./);
assert.match(pages.privacy, /12 meses desde el último contacto/);
assert.match(pages.privacy, /dentiapro\.notificaciones@gmail\.com/);
assert.match(pages.privacy, /Ley 19\.628 vigente/);
assert.match(pages.terms, /No permite contratar/);
assert.match(pages.terms, /no imponen arbitraje obligatorio/);

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

const carouselSlides = [
  "Agenda organizada",
  "Pacientes en contexto",
  "Historia clínica trazable",
  "Odontograma clínico",
  "Tratamientos conectados",
  "Consentimientos gestionados",
  "Finanzas del paciente",
  "Seguimientos visibles",
];
for (const slide of carouselSlides) {
  assert.ok(carousel.includes(slide), `Missing carousel slide ${slide}`);
}
assert.match(carouselAutoplay, /AUTOPLAY_DELAY_MS = 6000/, "Carousel autoplay must use the approved six-second interval");
assert.match(carouselAutoplay, /MANUAL_INTERACTION_PAUSE_MS = 10000/, "Manual interaction pause must be temporary");
assert.match(carousel, /prefers-reduced-motion: reduce/, "Carousel must disable autoplay for reduced motion");
assert.match(carousel, /visibilitychange/, "Carousel must pause while the page is hidden");
assert.match(carousel, /onMouseEnter=.*setHoverPaused\(true\)/, "Carousel must pause on hover");
assert.match(carousel, /onFocusCapture=.*handleFocus/, "Carousel must pause for keyboard-visible focus");
assert.match(carousel, /onPointerDown=.*pauseForManualInteraction/, "Swipe interaction must pause autoplay temporarily");
assert.match(carousel, /setInteractionPaused\(false\)/, "Autoplay must resume after manual interaction");
assert.match(carousel, /ArrowLeft/);
assert.match(carousel, /ArrowRight/);
assert.match(carousel, /aria-live="polite"/);
assert.match(globalStyles, /scroll-snap-type: x mandatory/);
assert.match(globalStyles, /overscroll-behavior-inline: contain/);
assert.match(globalStyles, /min-width: calc\(100% - 1\.4rem\)/, "Mobile must preserve a visible next-slide affordance");

const nextConfig = read("next.config.ts");
assert.match(nextConfig, /source: "\/api\/public\/demo-requests"/);
assert.match(nextConfig, /destination: `\$\{apiProxyTarget\}\/api\/public\/demo-requests`/);
assert.match(nextConfig, /source: "\/consentimiento\/:path\*"/);
assert.match(nextConfig, /destination: `\$\{appUrl\}\/consentimiento\/:path\*`/);
for (const route of ["/login", "/dashboard", "/pacientes/:path*", "/agenda/:path*"]) {
  assert.ok(nextConfig.includes(`\"${route}\"`), `Missing legacy application redirect ${route}`);
}
for (const header of ["Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy", "Permissions-Policy"]) {
  assert.ok(nextConfig.includes(header), `Missing security header ${header}`);
}

console.log("site-contract-tests OK");
console.log(`official-screenshots ${expectedAssets.length}/11`);
