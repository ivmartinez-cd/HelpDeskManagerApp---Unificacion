import { expect, test, type Page } from "@playwright/test";

function isoDesdeHoy(dias: number): string {
  const d = new Date();
  d.setDate(d.getDate() + dias);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

// Wire real de GET /api/contadores/calendario (snake_case, ver
// CalendarEventSchema + CoberturaEventoSchema en calendario_schemas.py).
const EVENTO_CUBIERTO = {
  id: "evt-cubierto",
  title: "[Facturación]: ACME",
  start: `${isoDesdeHoy(0)}T00:00:00-03:00`,
  operador_id: "vipaez",
  all_day: true,
  background_color: "#888200",
  border_color: "#888200",
  string_tipo_evento: "Facturación",
  cliente: "ACME SRL",
  cobertura: {
    override_id: "11111111-1111-1111-1111-111111111111",
    operador_ausente_id: "vipaez",
    operador_ausente_nombre: "Victor Paez",
    operador_reemplazante_id: "mgonzalez",
    operador_reemplazante_nombre: "María González",
    operador_reemplazante_color: "#2266aa",
    vigente_desde: isoDesdeHoy(-2),
    vigente_hasta: isoDesdeHoy(5),
    alcance_total: true,
  },
};

const EVENTO_PROPIO = {
  id: "evt-propio",
  title: "[Facturación]: ROSMI",
  start: `${isoDesdeHoy(0)}T00:00:00-03:00`,
  operador_id: "mgonzalez",
  all_day: true,
  background_color: "#2266aa",
  border_color: "#2266aa",
  string_tipo_evento: "Facturación",
  cliente: "NEUMATICOS ROSMI SRL",
  cobertura: null,
};

async function mockCalendario(page: Page) {
  await page.route(
    (url) => url.pathname === "/api/contadores/calendario",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [EVENTO_CUBIERTO, EVENTO_PROPIO],
          total: 2,
          page: 1,
          size: 500,
        }),
      });
    },
  );
  await page.route("**/api/contadores/calendario/sync/status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ last_synced_at: null, total_events: 2 }),
    });
  });
  await page.route("**/api/contadores/calendario/operadores**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, size: 2000 }),
    });
  });
}

test.describe("Calendario: indicadores de cobertura (ADR-013 fase 2)", () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: "hdm_session", value: "playwright-test", domain: "localhost", path: "/" },
    ]);
  });

  test("modo efectivo (default): badge CUBIERTO POR + leyenda, evento propio sin badge", async ({
    page,
  }) => {
    await mockCalendario(page);
    await page.goto("/contadores/calendario");

    await expect(page.getByText("CUBIERTO POR MG")).toBeVisible();
    await expect(page.getByText("(Facturación) ACME")).toBeVisible();
    // El evento sin cobertura no lleva badge
    const propio = page.getByText("(Facturación) ROSMI");
    await expect(propio).toBeVisible();
    await expect(page.getByText("↩ MG cubre")).toBeHidden();
    // Leyenda visible porque hay al menos un evento cubierto
    await expect(page.getByText("Evento cubierto (operador efectivo)")).toBeVisible();
  });

  test("switch a Operador real: badge muted '↩ MG cubre', mismo set de eventos", async ({
    page,
  }) => {
    await mockCalendario(page);
    await page.goto("/contadores/calendario");
    await expect(page.getByText("CUBIERTO POR MG")).toBeVisible();

    await page.getByRole("radio", { name: "Operador real" }).click();

    await expect(page.getByText("↩ MG cubre")).toBeVisible();
    await expect(page.getByText("CUBIERTO POR MG")).toBeHidden();
    // El switch no re-fetchea ni cambia el set: los dos eventos siguen ahí
    await expect(page.getByText("(Facturación) ACME")).toBeVisible();
    await expect(page.getByText("(Facturación) ROSMI")).toBeVisible();
  });

  test("tooltip al hover: ausente, reemplazante, vigencia, alcance y link a coberturas", async ({
    page,
  }) => {
    await mockCalendario(page);
    await page.goto("/contadores/calendario");

    await page.getByText("(Facturación) ACME").hover();

    const tooltip = page.getByRole("tooltip");
    await expect(tooltip).toBeVisible();
    await expect(tooltip.getByText("Cobertura activa")).toBeVisible();
    await expect(tooltip.getByText("Victor Paez (@vipaez)")).toBeVisible();
    await expect(tooltip.getByText("María González (@mgonzalez)")).toBeVisible();
    await expect(tooltip.getByText("Total", { exact: true })).toBeVisible();
    await expect(tooltip.getByRole("link", { name: "Ver detalle" })).toHaveAttribute(
      "href",
      "/contadores/coberturas",
    );

    // Escape cierra el tooltip
    await page.keyboard.press("Escape");
    await expect(tooltip).toBeHidden();
  });
});
