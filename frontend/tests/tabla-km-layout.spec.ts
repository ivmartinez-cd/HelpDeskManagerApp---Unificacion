import { test } from "@playwright/test";

const PRESTADORES_MOCK = [
  { id: "aaa", nombre: "Bahia Blanca - Eduardo Lledos", nombreCorto: "BAHIA", cuit: null, region: "BAHIA BLANCA", activo: true, sigesEmpresaId: 1303, cdPrestadorId: null, sigesBaseSucursalId: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
];

const TABLA_KM_MOCK = [
  { id: "1", prestadorId: "aaa", spstId: null, empresaNombre: "Adecoagro", sucursalNombre: "Las Horquetas", observaciones: null, domicilioCliente: null, localidadCliente: "Las Horquetas", provinciaCliente: "Buenos Aires", kmsRecorrido: 199.294, umbralViatico: 80, aplicaViatico: true, kmsAFacturar: 200, urlMaps: "https://maps.google.com/?q=-38.5,-62.1", createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
  { id: "2", prestadorId: "aaa", spstId: null, empresaNombre: "Adecoagro", sucursalNombre: "Las Horquetas PDS", observaciones: null, domicilioCliente: null, localidadCliente: "Las Horquetas", provinciaCliente: "Buenos Aires", kmsRecorrido: 319.281, umbralViatico: 80, aplicaViatico: true, kmsAFacturar: 320, urlMaps: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
  { id: "3", prestadorId: "aaa", spstId: null, empresaNombre: "ADM Agro S.R.L", sucursalNombre: "Piedrabuena", observaciones: null, domicilioCliente: null, localidadCliente: "Piedrabuena", provinciaCliente: "Santa Cruz", kmsRecorrido: 10.341, umbralViatico: 80, aplicaViatico: false, kmsAFacturar: 0, urlMaps: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
  { id: "4", prestadorId: "aaa", spstId: null, empresaNombre: "Aerolineas Argentinas", sucursalNombre: "Aeropuerto de Bahia Blanca", observaciones: null, domicilioCliente: null, localidadCliente: "Bahia Blanca", provinciaCliente: "Buenos Aires", kmsRecorrido: 11.743, umbralViatico: 80, aplicaViatico: false, kmsAFacturar: 0, urlMaps: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
  { id: "5", prestadorId: "aaa", spstId: null, empresaNombre: "Aerolineas Argentinas", sucursalNombre: "BHI - Bahia Blanca", observaciones: null, domicilioCliente: null, localidadCliente: "Bahia Blanca", provinciaCliente: "Buenos Aires", kmsRecorrido: 0.669, umbralViatico: 80, aplicaViatico: false, kmsAFacturar: 0, urlMaps: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
  { id: "6", prestadorId: "aaa", spstId: null, empresaNombre: "Banco Credicoop", sucursalNombre: "080 - Puan", observaciones: null, domicilioCliente: null, localidadCliente: "Puan", provinciaCliente: "Buenos Aires", kmsRecorrido: 635.176, umbralViatico: 80, aplicaViatico: true, kmsAFacturar: 636, urlMaps: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
  { id: "7", prestadorId: "aaa", spstId: null, empresaNombre: "Banco Credicoop", sucursalNombre: "090 - Ingeniero White", observaciones: null, domicilioCliente: null, localidadCliente: "Ingeniero White", provinciaCliente: "Buenos Aires", kmsRecorrido: 10.129, umbralViatico: 80, aplicaViatico: false, kmsAFacturar: 0, urlMaps: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
  { id: "8", prestadorId: "aaa", spstId: null, empresaNombre: "Banco Credicoop", sucursalNombre: "106 - Hilario Ascasubi", observaciones: null, domicilioCliente: null, localidadCliente: "Hilario Ascasubi", provinciaCliente: "Buenos Aires", kmsRecorrido: 108.219, umbralViatico: 80, aplicaViatico: true, kmsAFacturar: 109, urlMaps: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
  { id: "9", prestadorId: "aaa", spstId: null, empresaNombre: "Banco Credicoop", sucursalNombre: "111 - Pigue", observaciones: null, domicilioCliente: null, localidadCliente: "Pigue", provinciaCliente: "Buenos Aires", kmsRecorrido: 134.074, umbralViatico: 80, aplicaViatico: true, kmsAFacturar: 135, urlMaps: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
];

async function setFakeSession(page: import("@playwright/test").Page) {
  await page.context().addCookies([{ name: "hdm_session", value: "test-session-token", domain: "localhost", path: "/", httpOnly: true, secure: false }]);
}

test("tabla KM layout mejorado @smoke", async ({ page }) => {
  await setFakeSession(page);

  await page.route("**/api/liquidaciones/prestadores**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: PRESTADORES_MOCK, total: 1, page: 1, size: 1000 }) })
  );
  await page.route("**/api/liquidaciones/tabla-km**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: TABLA_KM_MOCK, total: TABLA_KM_MOCK.length, page: 1, size: 1000 }) })
  );
  await page.route("**/api/liquidaciones/spsts**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: [], total: 0, page: 1, size: 1000 }) })
  );

  await page.goto("/liquidaciones/configuracion/tabla-km");
  await page.waitForLoadState("networkidle");

  // Seleccionar el prestador BAHIA
  await page.selectOption('select[aria-label="Filtrar por PST"]', "aaa");
  await page.waitForLoadState("networkidle");

  await page.screenshot({ path: "test-results/tabla-km-layout.png", fullPage: false });
});
