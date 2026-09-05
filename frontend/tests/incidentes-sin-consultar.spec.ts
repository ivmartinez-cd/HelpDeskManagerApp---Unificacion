import type { Page } from "@playwright/test";
import { expect, test } from "./fixtures";

// ── Servicio Técnico › Incidentes sin consultar (PST del interior, estado Derivado) ──

const INCIDENTE_PROPIO = {
  id_incidente: 843579,
  fecha_ingreso: "2026-08-01T09:00:00Z",
  tipo: "Correctivo",
  estado: "Derivado",
  cliente: "EDERSA S.A.",
  sucursal: "Casa Central",
  nro_serie: "XYZ123",
  modelo: "HP LaserJet",
  tecnico: "PST del Interior SA",
  id_tecnico: 11,
  operador: "Victor Paez",
  dias_desde_ingreso: 9,
  demorado: true,
};

const INCIDENTE_SIN_DEMORA = {
  ...INCIDENTE_PROPIO,
  id_incidente: 843580,
  cliente: "COOP SAN JUAN",
  dias_desde_ingreso: 3,
  demorado: false,
};

async function mockIncidentesDerivados(page: Page, items: unknown[] = [INCIDENTE_PROPIO, INCIDENTE_SIN_DEMORA]) {
  await page.route("**/api/prestadores/operadores**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, size: 500 }),
    });
  });
  await page.route("**/api/sla/incidentes-derivados?**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items, total: items.length, page: 1, size: 500 }),
      });
    } else {
      await route.fallback();
    }
  });
}

test.describe("Servicio Técnico › Incidentes sin consultar", () => {
  test("listado: título, período por defecto, incidentes derivados con días resaltados @smoke", async ({
    page,
  }) => {
    await mockIncidentesDerivados(page);
    await page.goto("/incidentes-sin-consultar");

    await expect(page.getByRole("heading", { name: "Incidentes sin consultar" })).toBeVisible();
    await expect(page.getByText("EDERSA S.A.")).toBeVisible();
    await expect(page.getByText("COOP SAN JUAN")).toBeVisible();
    await expect(page.getByText("Victor Paez").first()).toBeVisible();
    await expect(page.getByText("2 incidentes", { exact: false }).first()).toBeVisible();
  });

  test("empty state sin incidentes", async ({ page }) => {
    await mockIncidentesDerivados(page, []);
    await page.goto("/incidentes-sin-consultar");
    await expect(
      page.getByText("Sin incidentes derivados sin consultar para el período y filtro seleccionados."),
    ).toBeVisible();
  });
});
