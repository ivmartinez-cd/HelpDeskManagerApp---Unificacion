import { test, expect } from "@playwright/test";

const PRESTADORES_MOCK = [
  { id: "aaa", nombre: "Bahia Blanca - Eduardo Lledos", nombreCorto: "BAHIA", cuit: null, region: "BAHIA BLANCA", activo: true, sigesEmpresaId: 1303, cdPrestadorId: null, sigesBaseSucursalId: null, createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
];
const TABLA_KM_MOCK = [
  { id: "1", prestadorId: "aaa", spstId: null, empresaNombre: "Adecoagro", sucursalNombre: "Las Horquetas", observaciones: null, domicilioCliente: "Ruta Nacional 33 KM 167", localidadCliente: "GUAMINI", provinciaCliente: "Buenos Aires", kmsRecorrido: 199.294, umbralViatico: 30, aplicaViatico: true, kmsAFacturar: 199.294, urlMaps: "https://www.google.com/maps/dir/?api=1&origin=-38.5,-62.1&destination=-37.0,-62.4&travelmode=driving", createdAt: "2025-01-01T00:00:00Z", updatedAt: "2025-01-01T00:00:00Z" },
];

async function setFakeSession(page: import("@playwright/test").Page) {
  await page.context().addCookies([{ name: "hdm_session", value: "test-session-token", domain: "localhost", path: "/", httpOnly: true, secure: false }]);
}

test("modal editar muestra link Abrir en Maps", async ({ page }) => {
  await setFakeSession(page);
  await page.route("**/api/liquidaciones/prestadores**", (r) => r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: PRESTADORES_MOCK, total: 1, page: 1, size: 1000 }) }));
  await page.route("**/api/liquidaciones/tabla-km**", (r) => r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: TABLA_KM_MOCK, total: 1, page: 1, size: 1000 }) }));
  await page.route("**/api/liquidaciones/spsts**", (r) => r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: [], total: 0, page: 1, size: 1000 }) }));

  await page.goto("/liquidaciones/configuracion/tabla-km");
  await page.waitForLoadState("networkidle");
  await page.selectOption('select[aria-label="Filtrar por PST"]', "aaa");
  await page.waitForLoadState("networkidle");

  await page.getByRole("button", { name: "Editar" }).first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByRole("link", { name: /Abrir en Maps/ })).toBeVisible();

  await page.screenshot({ path: "test-results/tabla-km-modal-maps.png", fullPage: false });
});
