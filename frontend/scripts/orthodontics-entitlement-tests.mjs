import assert from "node:assert/strict";
import fs from "node:fs";

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const nav = read("config/navigation.ts");
const tenant = read("components/orthodontics/OrthodonticsAssignmentPage.tsx");
const platform = read("components/orthodontics/PlatformOrthodonticsEntitlementCard.tsx");
const service = read("services/orthodonticsService.ts");

assert.match(nav, /orthodontics\.assignment\.view/);
assert.match(tenant, /Cupos/);
assert.match(tenant, /Asignados/);
assert.match(tenant, /Disponibles/);
assert.match(tenant, /El módulo no está habilitado/);
assert.match(platform, /Habilitación comercial y cupos por odontólogo/);
assert.match(service, /\/api\/orthodontics\/assignments/);
assert.match(service, /orthodontics-entitlement/);
console.log("orthodontics-entitlement-tests OK");
