import { expect, test, type Page } from "@playwright/test";

// Mismo user id que USER_MOCK en global-setup.ts.
const USER_ID = "00000000-0000-0000-0000-000000000001";

function pageOf(items: unknown[]) {
  return JSON.stringify({ items, total: items.length, page: 1, size: 200 });
}

// Franjas 00:00–23:59 = siempre "activa" sin depender de la hora real en la
// que corra el test (ver MiTurnoBanner/WatiHeaderLink: comparan strings
// HH:MM:SS contra la hora actual).
const SHIFT_PROPIO_INSUMOS = {
  slotId: "slot-1",
  casillaId: "casilla-1",
  casillaNombre: "INSUMOS",
  casillaColor: "#F7941D",
  horaInicio: "00:00:00",
  horaFin: "23:59:59",
  diaSemana: 4,
  operadores: [{ userId: USER_ID, userName: "Test Admin", color: "#05c002" }],
  isCurrent: true,
  isNext: false,
};

const SHIFT_ST_DE_OTRO_OPERADOR = {
  slotId: "slot-2",
  casillaId: "casilla-2",
  casillaNombre: "ST",
  casillaColor: "#58595B",
  horaInicio: "00:00:00",
  horaFin: "23:59:59",
  diaSemana: 4,
  operadores: [{ userId: "11111111-0000-0000-0000-000000000002", userName: "Otro Operador" }],
  isCurrent: true,
  isNext: false,
};

async function mockTurnos(page: Page, shifts: unknown[]) {
  await page.route("**/api/turnos/current", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: shifts,
        total: shifts.length,
        page: 1,
        size: 200,
        varianteActiva: null,
      }),
    }),
  );
}

async function mockAccesos(page: Page, ranking: string[]) {
  await page.route("**/api/me/route-visits/top**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: pageOf(
        ranking.map((route_) => ({
          route: route_,
          moduleKey: route_.slice(1).split("/")[0],
          visits: 9,
          lastVisit: "2026-08-20",
        })),
      ),
    }),
  );
  // El RouteTracker postea en cada navegación a una ruta catalogada -- sin
  // mockear esto, la request cae en el 404 default del mock backend (no
  // rompe nada, RouteTracker falla en silencio, pero mockearlo evita ruido).
  await page.route("**/api/me/route-visits", (route) => route.fulfill({ status: 204, body: "" }));
}

test.describe("Inicio", () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: "hdm_session", value: "playwright-test", domain: "localhost", path: "/" },
    ]);
  });

  test("el banner de turno muestra la casilla asignada al usuario logueado", async ({ page }) => {
    await mockTurnos(page, [SHIFT_PROPIO_INSUMOS]);
    await mockAccesos(page, []);
    await page.goto("/");

    // La franja mock cubre todo el día, así que siempre está "en curso" →
    // leyenda "Ahora estás en:" (si ninguna estuviera en curso diría "Hoy te toca:").
    await expect(page.getByText("Ahora estás en:")).toBeVisible();
    await expect(page.getByText("INSUMOS 00:00–23:59")).toBeVisible();
  });

  test("sin turno propio hoy, el banner no se muestra", async ({ page }) => {
    // Turno real, pero de OTRO operador -- no del usuario logueado.
    await mockTurnos(page, [SHIFT_ST_DE_OTRO_OPERADOR]);
    await mockAccesos(page, []);
    await page.goto("/");

    await expect(page.getByText("Ahora estás en:")).not.toBeVisible();
    await expect(page.getByText("Hoy te toca:")).not.toBeVisible();
  });

  test("accesos directos: el ranking real se antepone al respaldo fijo", async ({ page }) => {
    await mockTurnos(page, []);
    await mockAccesos(page, ["/liquidaciones/lista"]);
    await page.goto("/");

    await expect(page.getByRole("link", { name: "Liquidaciones" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Calendario" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Anexos sin facturar" })).toBeVisible();
  });

  test("accesos directos: sin ranking todavía, se muestra el respaldo fijo completo", async ({
    page,
  }) => {
    await mockTurnos(page, []);
    await mockAccesos(page, []);
    await page.goto("/");

    await expect(page.getByRole("link", { name: "Calendario" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Anexos sin facturar" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Liquidaciones" })).toBeVisible();
  });

  test("el ícono de WATI se destaca dentro del horario de Servicio Técnico", async ({ page }) => {
    await mockTurnos(page, [SHIFT_ST_DE_OTRO_OPERADOR]);
    await mockAccesos(page, []);
    await page.goto("/");

    await expect(page.getByTitle("WATI — revisar ahora")).toBeVisible();
    await expect(page.getByText("Revisar ahora")).toBeVisible();
  });

  test("el ícono de WATI queda neutro sin turno ST activo", async ({ page }) => {
    await mockTurnos(page, []);
    await mockAccesos(page, []);
    await page.goto("/");

    await expect(page.getByTitle("WATI", { exact: true })).toBeVisible();
    await expect(page.getByText("Revisar ahora")).not.toBeVisible();
  });
});
