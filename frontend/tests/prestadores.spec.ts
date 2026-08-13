import { expect, test } from "@playwright/test";

const OPERADOR_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
const PST_BAHIA_ID = "11111111-1111-1111-1111-111111111111";
const PST_TANDIL_ID = "22222222-2222-2222-2222-222222222222";
const PST_SIN_ID = "33333333-3333-3333-3333-333333333333";

const CONTACTO_BAHIA = {
  id: "44444444-4444-4444-4444-444444444444",
  prestadorId: PST_BAHIA_ID,
  nombre: "Carlos Gómez",
  telefono: "0291-455-0000",
  email: "cgomez@bahiaservice.com.ar",
  isPrincipal: true,
  sortOrder: 0,
};

const PST_BAHIA = {
  id: PST_BAHIA_ID,
  sigesEmpresaId: 765,
  denComercial: "BAHIA SERVICE",
  razonSocial: "Bahía Service SRL",
  cuit: "30-11111111-1",
  equipos: 120,
  operadorId: OPERADOR_ID,
  operadorNombre: "Victor Paez",
  operadorColor: "#888200",
  isActive: true,
  contactos: [CONTACTO_BAHIA],
};

const PST_TANDIL = {
  id: PST_TANDIL_ID,
  sigesEmpresaId: 812,
  denComercial: "TANDIL SERVICE",
  razonSocial: null,
  cuit: null,
  equipos: null,
  operadorId: OPERADOR_ID,
  operadorNombre: "Victor Paez",
  operadorColor: "#888200",
  isActive: false,
  contactos: [],
};

const PST_SIN_ASIGNAR = {
  id: PST_SIN_ID,
  sigesEmpresaId: 900,
  denComercial: "RECONQUISTA SERVICE",
  razonSocial: null,
  cuit: null,
  equipos: 40,
  operadorId: null,
  operadorNombre: null,
  operadorColor: null,
  isActive: true,
  contactos: [],
};

// GET /api/prestadores devuelve un resumen agregado, no Page[T] (ADR-011)
const RESUMEN = {
  totalPrestadores: 3,
  totalActivos: 2,
  operadoresConPst: 1,
  sinAsignar: 1,
  grupos: [
    {
      operadorId: OPERADOR_ID,
      operadorNombre: "Victor Paez",
      operadorColor: "#888200",
      prestadores: [PST_BAHIA, PST_TANDIL],
    },
    {
      operadorId: null,
      operadorNombre: null,
      operadorColor: null,
      prestadores: [PST_SIN_ASIGNAR],
    },
  ],
};

const OPERADORES_PAGE = {
  items: [{ id: OPERADOR_ID, fullName: "Victor Paez", color: "#888200" }],
  total: 1,
  page: 1,
  size: 500,
};

const HISTORIAL_PAGE = {
  items: [
    {
      id: "55555555-5555-5555-5555-555555555555",
      operadorId: OPERADOR_ID,
      operadorNombre: "Victor Paez",
      desde: "2026-03-01",
      hasta: null,
    },
    {
      id: "66666666-6666-6666-6666-666666666666",
      operadorId: null,
      operadorNombre: "Pollero",
      desde: "2020-01-01",
      hasta: "2024-02-29",
    },
  ],
  total: 2,
  page: 1,
  size: 200,
};

test.describe("Módulo de Prestadores", () => {
  test.beforeEach(async ({ page, context }) => {
    // El proxy (proxy.ts/middleware) redirige a /login si no hay cookie hdm_session.
    // Solo necesita existir — la validez real la chequea el layout contra el mock backend.
    await context.addCookies([
      { name: "hdm_session", value: "playwright-test", domain: "localhost", path: "/" },
    ]);

    // auth/me y auth/modules los maneja el mock backend global (global-setup.ts).
    // Acá solo mockeamos los datos de negocio (llamadas client-side).

    // Función predicate para no matchear /api/prestadores/operadores ni /{id}
    await page.route(
      (url) => url.pathname === "/api/prestadores",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(RESUMEN),
        });
      },
    );

    await page.route("**/api/prestadores/operadores**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(OPERADORES_PAGE),
      });
    });
  });

  // ── Hub agrupado ──────────────────────────────────────────────────────────

  test("hub muestra los KPIs y los grupos por operador colapsados", async ({ page }) => {
    await page.goto("/prestadores");

    await expect(
      page.getByRole("heading", { name: "Prestadores de Servicio Técnico" }),
    ).toBeVisible();

    await expect(page.getByText("Total PST")).toBeVisible();
    await expect(page.getByText("Operadores activos")).toBeVisible();
    // "Sin asignar" aparece dos veces: el KPI y el header del grupo sin operador
    await expect(page.getByText("Sin asignar")).toHaveCount(2);

    await expect(page.getByText("Victor Paez")).toBeVisible();
    await expect(page.getByText("2 prestadores")).toBeVisible();
    await expect(page.getByText("1 prestador", { exact: true })).toBeVisible();

    // Colapsado por default: la tabla del grupo no se renderiza todavía
    await expect(page.getByText("BAHIA SERVICE")).toBeHidden();
  });

  test("hub muestra Nuevo PST y Sincronizar desde Siges para el superadmin", async ({
    page,
  }) => {
    await page.goto("/prestadores");

    await expect(page.getByRole("button", { name: "Nuevo PST" })).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Sincronizar desde Siges" }),
    ).toBeVisible();
  });

  test("expandir un grupo muestra la tabla con contacto principal y equipos", async ({
    page,
  }) => {
    await page.goto("/prestadores");

    await page.getByRole("button", { name: /Victor Paez/ }).click();

    await expect(page.getByText("BAHIA SERVICE")).toBeVisible();
    await expect(page.getByText("120")).toBeVisible();
    await expect(page.getByText("Carlos Gómez")).toBeVisible();
    const mailLink = page.getByRole("link", { name: "cgomez@bahiaservice.com.ar" });
    await expect(mailLink).toBeVisible();
    await expect(mailLink).toHaveAttribute("href", "mailto:cgomez@bahiaservice.com.ar");

    // El PST inactivo del mismo grupo muestra la marca "inactivo"
    await expect(page.getByText("TANDIL SERVICE")).toBeVisible();
    await expect(page.getByText("inactivo", { exact: true })).toBeVisible();
  });

  // ── Búsqueda ──────────────────────────────────────────────────────────────

  test("la búsqueda filtra PST y oculta los grupos sin coincidencias", async ({ page }) => {
    await page.goto("/prestadores");

    // exact: el sidebar tiene un buscador deshabilitado "Buscar (próximamente)"
    await page.getByLabel("Buscar", { exact: true }).fill("bahia");

    // El grupo de Victor Paez queda con 1 solo PST; el grupo sin operador desaparece
    await expect(page.getByText("1 prestador", { exact: true })).toBeVisible();
    await expect(page.getByText("Sin asignar")).toHaveCount(1); // queda solo el KPI
  });

  test("la búsqueda sin coincidencias muestra el empty state", async ({ page }) => {
    await page.goto("/prestadores");

    await page.getByLabel("Buscar", { exact: true }).fill("zzz-no-existe");

    await expect(page.getByText("Sin resultados")).toBeVisible();
    await expect(page.getByText("No hay PST que coincidan con la búsqueda.")).toBeVisible();
  });

  // ── Sincronización ────────────────────────────────────────────────────────

  test("Sincronizar llama POST /sync y muestra el resultado", async ({ page }) => {
    let syncCalled = false;
    await page.route("**/api/prestadores/sync", async (route) => {
      syncCalled = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ actualizados: ["BAHIA SERVICE"], sinCambios: 2 }),
      });
    });

    await page.goto("/prestadores");

    await page.getByRole("button", { name: "Sincronizar desde Siges" }).click();

    await expect(async () => {
      expect(syncCalled).toBe(true);
    }).toPass();

    await expect(page.getByText("1 actualizados, 2 sin cambios.")).toBeVisible();
  });

  // ── Detalle ───────────────────────────────────────────────────────────────

  test("Ver abre el modal de detalle con badges e historial de asignación", async ({
    page,
  }) => {
    await page.route(`**/api/prestadores/${PST_BAHIA_ID}/historial**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(HISTORIAL_PAGE),
      });
    });

    await page.goto("/prestadores");

    await page.getByRole("button", { name: /Victor Paez/ }).click();
    await page.getByRole("button", { name: "Ver" }).first().click();

    const dialog = page.getByRole("dialog", { name: "BAHIA SERVICE" });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText("Activo", { exact: true })).toBeVisible();
    await expect(dialog.getByText("Siges #765")).toBeVisible();

    // Historial: tramo vigente + tramo histórico cerrado (fechas es-AR en UTC)
    await expect(dialog.getByText(/01\/03\/2026 \(vigente\)/)).toBeVisible();
    await expect(dialog.getByText("Pollero")).toBeVisible();
    await expect(dialog.getByText(/01\/01\/2020 a 29\/02\/2024/)).toBeVisible();
  });

  test("Nuevo PST abre el modal de alta", async ({ page }) => {
    await page.goto("/prestadores");

    await page.getByRole("button", { name: "Nuevo PST" }).click();

    await expect(page.getByRole("dialog", { name: "Nuevo PST" })).toBeVisible();
  });
});
