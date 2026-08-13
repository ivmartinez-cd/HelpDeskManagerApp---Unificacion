import { expect, test, type Page } from "@playwright/test";

function isoDesdeHoy(dias: number): string {
  const d = new Date();
  d.setDate(d.getDate() + dias);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

// ── Contadores: wire snake_case (sin serialization_alias en los schemas) ────

const OVERRIDE_ACTIVA = {
  id: "11111111-1111-1111-1111-111111111111",
  operador_ausente_id: "vipaez",
  operador_ausente_nombre: "Victor Paez",
  operador_reemplazante_id: "mgonzalez",
  operador_reemplazante_nombre: "María González",
  vigente_desde: isoDesdeHoy(-2),
  vigente_hasta: isoDesdeHoy(5),
  alcance_total: true,
  clientes: [],
  estado: "ACTIVA",
  motivo: "Vacaciones",
};

const OVERRIDE_CANCELADA = {
  ...OVERRIDE_ACTIVA,
  id: "22222222-2222-2222-2222-222222222222",
  operador_ausente_id: "jlopez",
  operador_ausente_nombre: "Juan López",
  estado: "CANCELADA",
  motivo: "Ausencia",
};

const OPERADORES_CONTADORES = [
  { id: "vipaez", nombre: "Victor Paez", color: "#888200" },
  { id: "mgonzalez", nombre: "María González", color: "#2266aa" },
  { id: "jlopez", nombre: "Juan López", color: null },
];

async function mockContadores(page: Page, overrides: unknown[] = [OVERRIDE_ACTIVA, OVERRIDE_CANCELADA]) {
  await page.route("**/api/contadores/calendario/operadores**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: OPERADORES_CONTADORES, total: 3, page: 1, size: 2000 }),
    });
  });
  await page.route("**/api/contadores/calendario/overrides", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: overrides, total: overrides.length, page: 1, size: 2000 }),
      });
    } else {
      await route.fallback();
    }
  });
}

// ── Prestadores: wire camelCase (serialization_alias en los schemas) ────────

const PST_A = "aaaaaaaa-0000-0000-0000-000000000001";
const PST_B = "aaaaaaaa-0000-0000-0000-000000000002";
const OP_UUID_1 = "bbbbbbbb-0000-0000-0000-000000000001";
const OP_UUID_2 = "bbbbbbbb-0000-0000-0000-000000000002";

const OVERRIDE_PST = {
  id: "33333333-3333-3333-3333-333333333333",
  operadorAusenteId: OP_UUID_1,
  operadorAusenteNombre: "Victor Paez",
  operadorReemplazanteId: OP_UUID_2,
  operadorReemplazanteNombre: "María González",
  desde: isoDesdeHoy(10),
  hasta: isoDesdeHoy(20),
  alcanceTotal: false,
  prestadorIds: [PST_A, PST_B],
  estado: "ACTIVA",
  motivo: "Vacaciones",
};

async function mockPst(page: Page) {
  await page.route("**/api/prestadores/overrides", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [OVERRIDE_PST], total: 1, page: 1, size: 200 }),
      });
    } else {
      await route.fallback();
    }
  });
  await page.route("**/api/prestadores/operadores**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          { id: OP_UUID_1, fullName: "Victor Paez", color: "#888200" },
          { id: OP_UUID_2, fullName: "María González", color: null },
        ],
        total: 2,
        page: 1,
        size: 500,
      }),
    });
  });
  await page.route(
    (url) => url.pathname === "/api/prestadores",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          totalPrestadores: 2,
          totalActivos: 2,
          operadoresConPst: 1,
          sinAsignar: 0,
          grupos: [
            {
              operadorId: OP_UUID_1,
              operadorNombre: "Victor Paez",
              operadorColor: "#888200",
              prestadores: [
                { id: PST_A, denComercial: "BAHIA SERVICE" },
                { id: PST_B, denComercial: "TANDIL SERVICE" },
              ],
            },
          ],
        }),
      });
    },
  );
}

test.describe("Coberturas (overrides temporales de asignación)", () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: "hdm_session", value: "playwright-test", domain: "localhost", path: "/" },
    ]);
  });

  test("contadores: listado muestra tabla con estados derivados y copy de pie", async ({ page }) => {
    await mockContadores(page);
    await page.goto("/contadores/coberturas");

    await expect(page.getByRole("heading", { name: "Coberturas" })).toBeVisible();
    await expect(page.getByText("Victor Paez")).toBeVisible();
    await expect(page.getByText("@vipaez")).toBeVisible();
    // María González es reemplazante en las dos filas del mock
    await expect(page.getByText("María González")).toHaveCount(2);
    await expect(page.getByLabel("Estado: Activa")).toBeVisible();
    await expect(page.getByLabel("Estado: Cancelada")).toBeVisible();
    await expect(page.getByRole("cell", { name: "Total", exact: true })).toHaveCount(2);
    await expect(
      page.getByText("Las coberturas no modifican el Calendario de Gestión.", { exact: false }),
    ).toBeVisible();
  });

  test("contadores: filtro por estado y limpiar filtros", async ({ page }) => {
    await mockContadores(page);
    await page.goto("/contadores/coberturas");

    await page.getByRole("radio", { name: "Cancelada" }).click();
    await expect(page.getByText("Juan López")).toBeVisible();
    await expect(page.getByText("Victor Paez")).toBeHidden();

    await page.getByRole("button", { name: "Limpiar filtros" }).click();
    await expect(page.getByText("Victor Paez")).toBeVisible();
  });

  test("contadores: empty state sin coberturas", async ({ page }) => {
    await mockContadores(page, []);
    await page.goto("/contadores/coberturas");

    await expect(page.getByText("No hay coberturas todavía")).toBeVisible();
  });

  test("contadores: alta completa hace POST snake_case y refresca", async ({ page }) => {
    await mockContadores(page);
    let postBody: Record<string, unknown> | null = null;
    await page.route("**/api/contadores/calendario/overrides", async (route) => {
      if (route.request().method() === "POST") {
        postBody = route.request().postDataJSON() as Record<string, unknown>;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ ...OVERRIDE_ACTIVA, id: "99999999-9999-9999-9999-999999999999" }),
        });
      } else {
        await route.fallback();
      }
    });

    await page.goto("/contadores/coberturas");
    await page.getByRole("button", { name: "Nueva cobertura" }).click();

    const dialog = page.getByRole("dialog", { name: "Nueva cobertura" });
    const guardar = dialog.getByRole("button", { name: "Guardar cobertura" });
    await expect(guardar).toBeDisabled();

    await dialog.getByRole("combobox", { name: "¿Quién falta?" }).click();
    await page.getByRole("option", { name: /Victor Paez/ }).click();
    await dialog.getByRole("combobox", { name: "¿Quién lo cubre?" }).click();
    await page.getByRole("option", { name: /María González/ }).click();
    await dialog.getByLabel("Desde").fill(isoDesdeHoy(1));
    await dialog.getByLabel("Hasta").fill(isoDesdeHoy(8));

    await expect(guardar).toBeEnabled();
    await guardar.click();

    await expect(async () => {
      expect(postBody).toEqual({
        operador_ausente_id: "vipaez",
        operador_reemplazante_id: "mgonzalez",
        vigente_desde: isoDesdeHoy(1),
        vigente_hasta: isoDesdeHoy(8),
        clientes: null,
        motivo: "Vacaciones",
      });
    }).toPass();
    await expect(dialog).toBeHidden();
  });

  test("contadores: el reemplazante excluye al ausente y el 409 se muestra en el modal", async ({
    page,
  }) => {
    await mockContadores(page);
    await page.route("**/api/contadores/calendario/overrides", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 409,
          contentType: "application/json",
          body: JSON.stringify({
            message: "Ya existe un override activo que se solapa con ese rango.",
            code: "OVERLAPPING_OVERRIDE",
          }),
        });
      } else {
        await route.fallback();
      }
    });

    await page.goto("/contadores/coberturas");
    await page.getByRole("button", { name: "Nueva cobertura" }).click();
    const dialog = page.getByRole("dialog", { name: "Nueva cobertura" });

    await dialog.getByRole("combobox", { name: "¿Quién falta?" }).click();
    await page.getByRole("option", { name: /Victor Paez/ }).click();

    // El ausente elegido no aparece como opción de reemplazante
    await dialog.getByRole("combobox", { name: "¿Quién lo cubre?" }).click();
    await expect(page.getByRole("option", { name: /Victor Paez/ })).toBeHidden();
    await page.getByRole("option", { name: /Juan López/ }).click();

    await dialog.getByLabel("Desde").fill(isoDesdeHoy(1));
    await dialog.getByLabel("Hasta").fill(isoDesdeHoy(8));
    await dialog.getByRole("button", { name: "Guardar cobertura" }).click();

    await expect(
      dialog.getByText("Ya existe un override activo que se solapa con ese rango."),
    ).toBeVisible();
  });

  test("contadores: cancelar pide confirmación y hace POST /cancelar", async ({ page }) => {
    await mockContadores(page);
    let cancelCalled = false;
    await page.route(`**/api/contadores/calendario/overrides/${OVERRIDE_ACTIVA.id}/cancelar`, async (route) => {
      cancelCalled = true;
      await route.fulfill({ status: 204 });
    });

    await page.goto("/contadores/coberturas");
    await page.getByRole("button", { name: "Cancelar cobertura de Victor Paez" }).click();

    const confirm = page.getByRole("dialog", { name: "Cancelar cobertura" });
    await expect(confirm).toBeVisible();
    await confirm.getByRole("button", { name: "Cancelar cobertura" }).click();

    await expect(async () => {
      expect(cancelCalled).toBe(true);
    }).toPass();
  });

  test("pst: listado camelCase resuelve alcance por catálogo y deriva Programada", async ({
    page,
  }) => {
    await mockPst(page);
    await page.goto("/prestadores/coberturas");

    await expect(page.getByText("Victor Paez")).toBeVisible();
    await expect(page.getByLabel("Estado: Programada")).toBeVisible();
    const alcance = page.getByText("2 PST", { exact: true });
    await expect(alcance).toBeVisible();
    await expect(alcance).toHaveAttribute("title", "BAHIA SERVICE, TANDIL SERVICE");
  });

  test("pst: alcance parcial exige elegir PST del catálogo", async ({ page }) => {
    await mockPst(page);
    await page.goto("/prestadores/coberturas");
    await page.getByRole("button", { name: "Nueva cobertura" }).click();
    const dialog = page.getByRole("dialog", { name: "Nueva cobertura" });

    await dialog.getByRole("radio", { name: "PST específicos" }).click();
    await expect(dialog.getByText("Seleccioná al menos un PST.")).toBeVisible();

    await dialog.getByRole("combobox", { name: "Prestadores (PST)" }).click();
    await page.getByRole("option", { name: "BAHIA SERVICE" }).click();
    await expect(dialog.getByText("Seleccioná al menos un PST.")).toBeHidden();
  });
});
