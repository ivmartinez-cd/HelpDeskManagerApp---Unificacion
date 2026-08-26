import { test, expect } from "./fixtures";

// Insumos es el módulo más grande del frontend y, hasta este spec, no tenía
// ningún test e2e (ver auditoría 2026-08-26). Cubre solo el Dashboard
// (`/insumos`, Patrón 1) como smoke -- el resto de las pantallas del módulo
// (clientes, estadísticas, historial, configuración) queda para specs futuros.
const DASHBOARD_MOCK = {
  totals: { pending: 3, critical: 1, urgent: 1, warning: 1, good: 5, loaded: 2 },
  loadedToday: 2,
  customersEnabled: 4,
  perCustomer: [],
  thresholds: { critical: 2, urgent: 5, warning: 10 },
  refreshMinutes: 15,
};

test.describe("Insumos", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/insumos/dashboard", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(DASHBOARD_MOCK) }),
    );
    await page.route("**/api/insumos/requests**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, size: 200 }),
      }),
    );
    await page.route("**/api/insumos/alerts**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, size: 200 }),
      }),
    );
  });

  test("dashboard muestra los tiles de KPI y la tabla vacía @smoke", async ({ page }) => {
    await page.goto("/insumos");

    await expect(page.getByText("Pendientes", { exact: true })).toBeVisible();
    await expect(page.getByText("3", { exact: true })).toBeVisible();
    await expect(page.getByText("Cargados hoy")).toBeVisible();
  });
});
