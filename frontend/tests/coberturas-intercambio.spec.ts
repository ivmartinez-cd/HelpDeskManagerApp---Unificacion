import { expect, test, type Page } from "@playwright/test";

/** Intercambio de turnos (ADR-026) en Coberturas de Turnos: el listado plano
 * agrupa el par en una fila, el modal ofrece el toggle Cobertura |
 * Intercambio y el alta/cancelación pegan a /api/turnos/intercambios. */

function isoDesdeHoy(dias: number): string {
  const d = new Date();
  d.setDate(d.getDate() + dias);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

const MAJO = "cccccccc-0000-0000-0000-000000000001";
const LUNA = "cccccccc-0000-0000-0000-000000000002";
const VICTOR = "cccccccc-0000-0000-0000-000000000003";
const INTERCAMBIO_ID = "dddddddd-0000-0000-0000-000000000001";
const CASILLA = "eeeeeeee-0000-0000-0000-000000000001";
const SLOT_A = "ffffffff-0000-0000-0000-000000000001";
const SLOT_B = "ffffffff-0000-0000-0000-000000000002";

const base = {
  desde: isoDesdeHoy(0),
  hasta: isoDesdeHoy(0),
  alcanceTotal: true,
  slotIds: [] as string[],
  estado: "ACTIVA",
  motivo: "Intercambio",
  intercambioId: INTERCAMBIO_ID,
};

const IDA = {
  ...base,
  id: "11111111-0000-0000-0000-000000000001",
  operadorAusenteId: MAJO,
  operadorAusenteNombre: "Maria Jose Vela",
  operadorReemplazanteId: LUNA,
  operadorReemplazanteNombre: "Luna Perez",
};

const VUELTA = {
  ...base,
  id: "11111111-0000-0000-0000-000000000002",
  operadorAusenteId: LUNA,
  operadorAusenteNombre: "Luna Perez",
  operadorReemplazanteId: MAJO,
  operadorReemplazanteNombre: "Maria Jose Vela",
};

const COMUN = {
  ...base,
  id: "11111111-0000-0000-0000-000000000003",
  operadorAusenteId: VICTOR,
  operadorAusenteNombre: "Victor Paez",
  operadorReemplazanteId: MAJO,
  operadorReemplazanteNombre: "Maria Jose Vela",
  desde: isoDesdeHoy(5),
  hasta: isoDesdeHoy(9),
  motivo: "Vacaciones",
  intercambioId: null,
};

function page200(items: unknown[]) {
  return {
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ items, total: items.length, page: 1, size: 200 }),
  };
}

async function mockTurnos(page: Page, overrides: unknown[] = [IDA, VUELTA, COMUN]) {
  await page.route("**/api/turnos/overrides", async (route) => {
    if (route.request().method() === "GET") await route.fulfill(page200(overrides));
    else await route.fallback();
  });
  await page.route("**/api/turnos/users**", async (route) => {
    await route.fulfill(
      page200([
        { id: MAJO, fullName: "Maria Jose Vela", color: "#a855f7" },
        { id: LUNA, fullName: "Luna Perez", color: "#2266aa" },
        { id: VICTOR, fullName: "Victor Paez", color: "#888200" },
      ]),
    );
  });
  await page.route("**/api/turnos/casillas**", async (route) => {
    await route.fulfill(page200([{ id: CASILLA, nombre: "INSUMOS" }]));
  });
  await page.route("**/api/turnos/slots**", async (route) => {
    await route.fulfill(
      page200([
        { id: SLOT_A, casillaId: CASILLA, horaInicio: "08:00:00", horaFin: "12:00:00", diaSemana: 0 },
        { id: SLOT_B, casillaId: CASILLA, horaInicio: "12:00:00", horaFin: "16:00:00", diaSemana: 0 },
      ]),
    );
  });
}

test.describe("Coberturas de turnos: intercambio (ADR-026)", () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: "hdm_session", value: "playwright-test", domain: "localhost", path: "/" },
    ]);
  });

  test("el par se agrupa en una sola fila A ⇄ B y la común queda aparte", async ({ page }) => {
    await mockTurnos(page);
    await page.goto("/admin/turnos/coberturas");

    await expect(page.getByRole("heading", { name: "Coberturas" })).toBeVisible();
    // Dos filas: el intercambio (una sola, aunque son dos coberturas) y la común.
    await expect(page.getByRole("row").filter({ hasText: "Intercambio" })).toHaveCount(1);
    await expect(page.getByLabel("intercambia con")).toHaveCount(1);
    await expect(page.getByRole("cell", { name: "Total", exact: true })).toHaveCount(2);
    await expect(
      page.getByRole("button", { name: "Cancelar intercambio de Maria Jose Vela y Luna Perez" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Cancelar cobertura de Victor Paez" }),
    ).toBeVisible();
  });

  test("alta con el toggle Intercambio hace POST /api/turnos/intercambios", async ({ page }) => {
    await mockTurnos(page, [COMUN]);
    let postBody: Record<string, unknown> | null = null;
    await page.route("**/api/turnos/intercambios", async (route) => {
      if (route.request().method() === "POST") {
        postBody = route.request().postDataJSON() as Record<string, unknown>;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ intercambioId: INTERCAMBIO_ID, coberturas: [IDA, VUELTA] }),
        });
      } else {
        await route.fallback();
      }
    });

    await page.goto("/admin/turnos/coberturas");
    await page.getByRole("button", { name: "Nueva cobertura" }).click();
    const dialog = page.getByRole("dialog", { name: "Nueva cobertura" });
    await dialog.getByRole("radio", { name: "Intercambio" }).click();

    const guardar = dialog.getByRole("button", { name: "Guardar intercambio" });
    await expect(guardar).toBeDisabled();

    await dialog.getByRole("combobox", { name: "Operador A" }).click();
    await page.getByRole("option", { name: /Maria Jose Vela/ }).click();
    await dialog.getByRole("combobox", { name: "Operador B" }).click();
    // A ya elegido no aparece como B
    await expect(page.getByRole("option", { name: /Maria Jose Vela/ })).toBeHidden();
    await page.getByRole("option", { name: /Luna Perez/ }).click();
    await dialog.getByLabel("Desde").fill(isoDesdeHoy(1));
    // Hasta se precarga con Desde (cambio de un solo día)
    await expect(dialog.getByLabel("Hasta")).toHaveValue(isoDesdeHoy(1));

    await expect(guardar).toBeEnabled();
    await guardar.click();

    await expect(async () => {
      expect(postBody).toEqual({
        operadorAId: MAJO,
        operadorBId: LUNA,
        desde: isoDesdeHoy(1),
        hasta: isoDesdeHoy(1),
        slotIdsA: null,
        slotIdsB: null,
        motivo: null,
      });
    }).toPass();
    await expect(dialog).toBeHidden();
  });

  test("alcance por franjas exige una franja de cada lado y manda slotIdsA/slotIdsB", async ({
    page,
  }) => {
    await mockTurnos(page, []);
    let postBody: Record<string, unknown> | null = null;
    await page.route("**/api/turnos/intercambios", async (route) => {
      postBody = route.request().postDataJSON() as Record<string, unknown>;
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ intercambioId: INTERCAMBIO_ID, coberturas: [IDA, VUELTA] }),
      });
    });

    await page.goto("/admin/turnos/coberturas");
    await page.getByRole("button", { name: "Nueva cobertura" }).click();
    const dialog = page.getByRole("dialog", { name: "Nueva cobertura" });
    await dialog.getByRole("radio", { name: "Intercambio" }).click();
    await dialog.getByRole("combobox", { name: "Operador A" }).click();
    await page.getByRole("option", { name: /Maria Jose Vela/ }).click();
    await dialog.getByRole("combobox", { name: "Operador B" }).click();
    await page.getByRole("option", { name: /Luna Perez/ }).click();
    await dialog.getByLabel("Desde").fill(isoDesdeHoy(1));

    await dialog.getByRole("radio", { name: "Franjas específicas" }).click();
    const guardar = dialog.getByRole("button", { name: "Guardar intercambio" });
    await expect(guardar).toBeDisabled();
    await expect(dialog.getByText("Seleccioná al menos una franja.")).toHaveCount(2);

    const franjasA = dialog.getByRole("combobox", {
      name: "Franjas de Maria Jose Vela que toma Luna Perez",
    });
    await franjasA.click();
    await page.getByRole("option", { name: "INSUMOS · Lun 08:00-12:00" }).click();
    // El multi-select queda abierto tras elegir (permite seguir sumando):
    // se cierra para que no tape al selector de abajo.
    await franjasA.click();
    await dialog
      .getByRole("combobox", { name: "Franjas de Luna Perez que toma Maria Jose Vela" })
      .click();
    await page.getByRole("option", { name: "INSUMOS · Lun 12:00-16:00" }).click();

    await expect(guardar).toBeEnabled();
    await guardar.click();
    await expect(async () => {
      expect(postBody).toMatchObject({ slotIdsA: [SLOT_A], slotIdsB: [SLOT_B] });
    }).toPass();
  });

  test("cancelar un intercambio confirma y pega a /intercambios/{id}/cancelar", async ({
    page,
  }) => {
    await mockTurnos(page);
    let cancelUrl: string | null = null;
    await page.route("**/api/turnos/intercambios/*/cancelar", async (route) => {
      cancelUrl = route.request().url();
      await route.fulfill({ status: 204 });
    });

    await page.goto("/admin/turnos/coberturas");
    await page
      .getByRole("button", { name: "Cancelar intercambio de Maria Jose Vela y Luna Perez" })
      .click();
    const confirm = page.getByRole("dialog", { name: "Cancelar intercambio" });
    await expect(confirm.getByText("Las dos coberturas del par quedan registradas")).toBeVisible();
    await confirm.getByRole("button", { name: "Cancelar intercambio" }).click();

    await expect(async () => {
      expect(cancelUrl).toContain(`/api/turnos/intercambios/${INTERCAMBIO_ID}/cancelar`);
    }).toPass();
  });

  test("editar un intercambio abre el modal en modo intercambio con el par precargado", async ({
    page,
  }) => {
    await mockTurnos(page);
    await page.goto("/admin/turnos/coberturas");
    await page
      .getByRole("button", { name: "Editar intercambio de Maria Jose Vela y Luna Perez" })
      .click();

    const dialog = page.getByRole("dialog", { name: "Editar intercambio" });
    await expect(dialog).toBeVisible();
    // Sin toggle en edición: una regla existente ya es una cosa o la otra.
    await expect(dialog.getByRole("radio", { name: "Cobertura" })).toHaveCount(0);
    await expect(dialog.getByRole("combobox", { name: "Operador A" })).toContainText(
      "Maria Jose Vela",
    );
    await expect(dialog.getByRole("combobox", { name: "Operador B" })).toContainText("Luna Perez");
    await expect(dialog.getByRole("button", { name: "Guardar cambios" })).toBeEnabled();
  });
});
