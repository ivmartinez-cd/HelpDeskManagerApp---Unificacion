import { test, expect } from "@playwright/test";

const PRESTADORES_MOCK = [
  {
    id: "aaaaaaaa-0000-0000-0000-000000000001",
    nombre: "INFORMATICA SA",
    nombreCorto: "INFOMAC",
    cuit: "30-12345678-9",
    region: "amba",
    activo: true,
    sigesEmpresaId: 101,
    cdPrestadorId: null,
    sigesBaseSucursalId: null,
    createdAt: "2025-01-01T00:00:00Z",
    updatedAt: "2025-01-01T00:00:00Z",
  },
  {
    id: "bbbbbbbb-0000-0000-0000-000000000002",
    nombre: "TECNISERVICE SRL",
    nombreCorto: "TECNI",
    cuit: "30-98765432-1",
    region: "noa",
    activo: true,
    sigesEmpresaId: 202,
    cdPrestadorId: null,
    sigesBaseSucursalId: 5050,
    createdAt: "2025-01-01T00:00:00Z",
    updatedAt: "2025-01-01T00:00:00Z",
  },
  {
    id: "cccccccc-0000-0000-0000-000000000003",
    nombre: "SIN VINCULO SRL",
    nombreCorto: "SINVIN",
    cuit: null,
    region: null,
    activo: true,
    sigesEmpresaId: null,
    cdPrestadorId: null,
    sigesBaseSucursalId: null,
    createdAt: "2025-01-01T00:00:00Z",
    updatedAt: "2025-01-01T00:00:00Z",
  },
];

const SUCURSALES_MOCK = [
  {
    sigesSucursalId: 5001,
    descripcion: "Casa Central - Palermo",
    latitud: "-34.5890",
    longitud: "-58.4320",
    tieneCoords: true,
  },
  {
    sigesSucursalId: 5002,
    descripcion: "Sucursal Norte",
    latitud: null,
    longitud: null,
    tieneCoords: false,
  },
];

// Inyecta la cookie de sesión antes de navegar — el proxy.ts (Next.js 16 middleware)
// comprueba solo su existencia; la validación real la hace el backend mock.
async function setFakeSession(page: import("@playwright/test").Page) {
  await page.context().addCookies([{
    name: "hdm_session",
    value: "test-session-token",
    domain: "localhost",
    path: "/",
    httpOnly: true,
    secure: false,
  }]);
}

test("botón Base Siges aparece solo para prestadores con vínculo Siges", async ({ page }) => {
  await setFakeSession(page);
  await page.route("**/api/liquidaciones/prestadores**", (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: PRESTADORES_MOCK, total: 3, page: 1, size: 1000 }),
    });
  });

  await page.goto("/liquidaciones/configuracion/prestadores");
  await page.waitForLoadState("networkidle");

  // INFOMAC tiene sigesEmpresaId pero sin base → debe decir "Base Siges"
  await expect(page.getByRole("row", { name: /INFOMAC/ })).toContainText("Base Siges");
  // TECNI tiene sigesEmpresaId y con base → debe decir "Distancias"
  await expect(page.getByRole("row", { name: /TECNI/ })).toContainText("Distancias");
  // SINVIN no tiene vínculo → no debe mostrar ninguno de los dos
  await expect(page.getByRole("row", { name: /SINVIN/ })).not.toContainText("Base Siges");
  await expect(page.getByRole("row", { name: /SINVIN/ })).not.toContainText("Distancias");

  await page.screenshot({ path: "test-results/prestadores-botones.png", fullPage: false });
});

test("modal de sucursales abre al clickear Base Siges", async ({ page }) => {
  await setFakeSession(page);
  await page.route("**/api/liquidaciones/prestadores**", (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: PRESTADORES_MOCK, total: 3, page: 1, size: 1000 }),
    });
  });

  await page.route(
    "**/api/liquidaciones/siges/prestador/aaaaaaaa-0000-0000-0000-000000000001/sucursales-propia",
    (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(SUCURSALES_MOCK),
      });
    },
  );

  await page.goto("/liquidaciones/configuracion/prestadores");
  await page.waitForLoadState("networkidle");

  // Click "Base Siges" de INFOMAC
  await page.getByRole("row", { name: /INFOMAC/ }).getByRole("button", { name: "Base Siges" }).click();

  // Modal debe abrirse con el título correcto
  await expect(page.getByRole("dialog")).toContainText("Sucursal base — INFOMAC");

  // Sucursales deben estar listadas
  await expect(page.getByText("Casa Central - Palermo")).toBeVisible();
  await expect(page.getByText("Sucursal Norte")).toBeVisible();

  // Badges de coords
  await expect(page.getByText("Con coords").first()).toBeVisible();
  await expect(page.getByText("Sin coords").first()).toBeVisible();

  // Botón "Guardar base" visible (selección no guardada aún)
  await expect(page.getByRole("button", { name: "Guardar base" })).not.toBeVisible();

  await page.screenshot({ path: "test-results/modal-base-sucursal.png", fullPage: false });
});
