import { expect, test, type Page } from "@playwright/test";

/** Modo vacaciones de turnos (ADR-025): editor de grilla variante, listado,
 * badge de la home y CTA desde Aprobaciones. Caso real: vacaciones de
 * M. J. Vela 24–28/08/2026 (docs/coberturas/PLAN_COBERTURA_VACACIONES_MAJO). */

const INSUMOS = "aaaaaaaa-0000-0000-0000-000000000001";
const ST = "aaaaaaaa-0000-0000-0000-000000000002";
const MAJO = "bbbbbbbb-0000-0000-0000-000000000001";
const LUNA = "bbbbbbbb-0000-0000-0000-000000000002";
const MARIANO = "bbbbbbbb-0000-0000-0000-000000000003";
const VICTOR = "bbbbbbbb-0000-0000-0000-000000000004";
const MARIANA = "bbbbbbbb-0000-0000-0000-000000000005";

const USERS = [
  { id: MAJO, fullName: "Maria Jose Vela", color: "#F7941D" },
  { id: LUNA, fullName: "Luna Torres", color: "#58595B" },
  { id: MARIANO, fullName: "Mariano Gomez", color: null },
  { id: VICTOR, fullName: "Victor Paez", color: null },
  { id: MARIANA, fullName: "Mariana Rodriguez", color: null },
];

const CASILLAS = [
  { id: INSUMOS, nombre: "INSUMOS", color: "#F7941D", sortOrder: 0, isActive: true },
  { id: ST, nombre: "ST", color: "#58595B", sortOrder: 1, isActive: true },
];

const op = (id: string) => {
  const u = USERS.find((x) => x.id === id)!;
  return { userId: u.id, userName: u.fullName, color: u.color };
};

/** Grilla titular del lunes (dia 0): INSUMOS 8–11 Majo · 11–13 Luna · 13–17 Mariano · 17–18 Victor;
 * ST 9–13 Victor · 13–15 Majo · 15–18 Luna. */
const TITULAR_LUNES = [
  [INSUMOS, "08:00:00", "11:00:00", MAJO],
  [INSUMOS, "11:00:00", "13:00:00", LUNA],
  [INSUMOS, "13:00:00", "17:00:00", MARIANO],
  [INSUMOS, "17:00:00", "18:00:00", VICTOR],
  [ST, "09:00:00", "13:00:00", VICTOR],
  [ST, "13:00:00", "15:00:00", MAJO],
  [ST, "15:00:00", "18:00:00", LUNA],
] as const;

const SLOTS = TITULAR_LUNES.map(([casillaId, horaInicio, horaFin, user], i) => ({
  id: `cccccccc-0000-0000-0000-00000000000${i + 1}`,
  casillaId,
  horaInicio,
  horaFin,
  diaSemana: 0,
  sortOrder: i,
  asignaciones: [
    { id: `dddddddd-0000-0000-0000-00000000000${i + 1}`, slotId: "", userId: user, userName: op(user).userName, vigenteDesde: "2026-01-01", vigenteHasta: null },
  ],
}));

const PRECARGA = {
  ausenteUserId: MAJO,
  ausenteNombre: "Maria Jose Vela",
  desde: "2026-08-24",
  hasta: "2026-08-28",
  slots: TITULAR_LUNES.map(([casillaId, horaInicio, horaFin, user], i) => ({
    casillaId,
    casillaNombre: casillaId === INSUMOS ? "INSUMOS" : "ST",
    diaSemana: 0,
    horaInicio,
    horaFin,
    sortOrder: i,
    operadores: user === MAJO ? [] : [op(user)],
    requiereCobertura: user === MAJO,
  })),
  advertencias: [],
};

const VARIANTE_GUARDADA = {
  id: "eeeeeeee-0000-0000-0000-000000000001",
  motivo: "Vacaciones M. J. Vela",
  origenTexto: null,
  desde: "2026-08-24",
  hasta: "2026-08-28",
  estado: "ACTIVA",
  createdByUserId: MAJO,
  slots: [],
  advertencias: [
    { tipo: "HUECO", casillaId: INSUMOS, casillaNombre: "INSUMOS", diaSemana: 0, horaInicio: "08:00:00", horaFin: "08:30:00", userId: null, userName: null, desde: null, hasta: null },
  ],
};

function page_(items: unknown[]) {
  return { items, total: items.length, page: 1, size: 200 };
}

async function mockTurnos(page: Page, variantes: unknown[] = []) {
  await page.route("**/api/turnos/casillas**", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(page_(CASILLAS)) }),
  );
  await page.route("**/api/turnos/slots**", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(page_(SLOTS)) }),
  );
  await page.route("**/api/turnos/users**", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(page_(USERS)) }),
  );
  await page.route("**/api/turnos/grilla-variantes/precarga**", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(PRECARGA) }),
  );
  await page.route(
    (url) => url.pathname === "/api/turnos/grilla-variantes",
    async (r) => {
      if (r.request().method() === "GET") {
        await r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(page_(variantes)) });
      } else {
        await r.fallback();
      }
    },
  );
}

test.describe("Modo vacaciones (grilla variante de turnos)", () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: "hdm_session", value: "playwright-test", domain: "localhost", path: "/" },
    ]);
  });

  test("editor: precarga el caso Majo, re-corta, avisa hueco (no bloquea) y guarda el payload completo", async ({
    page,
  }) => {
    await mockTurnos(page);
    let postBody: Record<string, unknown> | null = null;
    await page.route(
      (url) => url.pathname === "/api/turnos/grilla-variantes",
      async (r) => {
        if (r.request().method() === "POST") {
          postBody = r.request().postDataJSON() as Record<string, unknown>;
          await r.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(VARIANTE_GUARDADA) });
        } else {
          await r.fallback();
        }
      },
    );

    await page.goto("/admin/turnos");
    await page.getByRole("radio", { name: "Modo vacaciones" }).click();
    await expect(page.getByText("No hay grillas de vacaciones")).toBeVisible();
    await page.getByRole("button", { name: "Nueva grilla de vacaciones" }).click();

    const editor = page.getByRole("region", { name: "Nueva grilla de vacaciones" });
    await editor.getByRole("combobox", { name: "¿Quién falta?" }).click();
    await page.getByRole("option", { name: /Maria Jose Vela/ }).click();
    await editor.getByLabel("Desde").fill("2026-08-24");
    await editor.getByLabel("Hasta").fill("2026-08-28");
    await editor.getByRole("button", { name: "Precargar" }).click();

    // 7 franjas del lunes, las 2 de Majo marcadas como hueco a resolver (sin operador)
    await expect(page.getByTestId("franja-fila")).toHaveCount(7);
    await expect(page.locator('[data-requiere-cobertura="true"]')).toHaveCount(2);
    await expect(editor.getByLabel("Motivo")).toHaveValue("Vacaciones Maria Jose Vela");
    // Franjas sin operador = advertencia, no error: guardar sigue habilitado
    await expect(editor.getByText("INSUMOS · Lunes 08:00–11:00: franja sin operador asignado")).toBeVisible();
    const guardar = editor.getByRole("button", { name: "Guardar grilla" });
    await expect(guardar).toBeEnabled();

    // Re-cortar INSUMOS 8–11 → 8:30–11 con Mariano: aparece el hueco 8:00–8:30 como advertencia
    await editor.getByLabel("Inicio INSUMOS 08:00–11:00").fill("08:30");
    await editor.getByRole("combobox", { name: "Operadores INSUMOS 08:30–11:00" }).click();
    await page.getByRole("option", { name: /Mariano Gomez/ }).click();
    await page.keyboard.press("Escape");
    await expect(editor.getByText("INSUMOS · Lunes sin cobertura 08:00–08:30")).toBeVisible();
    await expect(guardar).toBeEnabled();

    // Solape duro: ST 13–15 (hueco de Majo) re-cortado a 12–15 pisa ST 9–13 → error y guardar deshabilitado
    await editor.getByLabel("Inicio ST 13:00–15:00").fill("12:00");
    await expect(editor.getByText(/ST · Lunes: 09:00–13:00 y 12:00–15:00 se superponen/)).toBeVisible();
    await expect(guardar).toBeDisabled();
    // Corrección del caso real: eliminar ST 12–15, Victor 9–14, Luna 14–18, nueva ST 8–9 Mariana
    await editor.getByRole("button", { name: "Eliminar franja ST 12:00–15:00" }).click();
    await editor.getByLabel("Fin ST 09:00–13:00").fill("14:00");
    await editor.getByLabel("Inicio ST 15:00–18:00").fill("14:00");
    await editor.getByRole("button", { name: "Agregar franja en ST" }).click();
    await editor.getByLabel("Inicio ST --:--–--:--").fill("08:00");
    await editor.getByLabel("Fin ST 08:00–--:--").fill("09:00");
    await editor.getByRole("combobox", { name: "Operadores ST 08:00–09:00" }).click();
    await page.getByRole("option", { name: /Mariana Rodriguez/ }).click();
    await page.keyboard.press("Escape");

    await expect(guardar).toBeEnabled();
    await guardar.click();

    await expect(async () => {
      expect(postBody).not.toBeNull();
    }).toPass();
    const body = postBody as unknown as {
      motivo: string;
      desde: string;
      hasta: string;
      slots: { casillaId: string; diaSemana: number; horaInicio: string; horaFin: string; userIds: string[] }[];
    };
    expect(body.motivo).toBe("Vacaciones Maria Jose Vela");
    expect([body.desde, body.hasta]).toEqual(["2026-08-24", "2026-08-28"]);
    const resumen = body.slots
      .map((s) => `${s.casillaId === INSUMOS ? "INSUMOS" : "ST"} ${s.horaInicio}-${s.horaFin} ${s.userIds.join(",")}`)
      .sort();
    expect(resumen).toEqual(
      [
        `INSUMOS 08:30-11:00 ${MARIANO}`,
        `INSUMOS 11:00-13:00 ${LUNA}`,
        `INSUMOS 13:00-17:00 ${MARIANO}`,
        `INSUMOS 17:00-18:00 ${VICTOR}`,
        `ST 08:00-09:00 ${MARIANA}`,
        `ST 09:00-14:00 ${VICTOR}`,
        `ST 14:00-18:00 ${LUNA}`,
      ].sort(),
    );
    await expect(page.getByRole("status")).toContainText("1 advertencia(s) de cobertura registradas");
  });

  test("listado: estados derivados por fecha y cancelar hace POST /cancelar", async ({ page }) => {
    const vigente = { ...VARIANTE_GUARDADA, desde: "2020-01-01", hasta: "2099-12-31" };
    const cancelada = { ...VARIANTE_GUARDADA, id: "eeeeeeee-0000-0000-0000-000000000002", estado: "CANCELADA", motivo: "Licencia" };
    await mockTurnos(page, [vigente, cancelada]);
    let cancelCalled = false;
    await page.route(`**/api/turnos/grilla-variantes/${vigente.id}/cancelar`, async (r) => {
      cancelCalled = true;
      await r.fulfill({ status: 204 });
    });

    await page.goto("/admin/turnos?tab=vacaciones");
    await expect(page.getByLabel("Estado: Vigente")).toBeVisible();
    await expect(page.getByLabel("Estado: Cancelada")).toBeVisible();

    await page.getByRole("button", { name: "Cancelar Vacaciones M. J. Vela" }).click();
    const confirm = page.getByRole("dialog", { name: "Cancelar grilla de vacaciones" });
    await confirm.getByRole("button", { name: "Cancelar grilla" }).click();
    await expect(async () => {
      expect(cancelCalled).toBe(true);
    }).toPass();
  });

  test("home: badge 'Grilla de vacaciones hasta el DD/MM' cuando /current trae varianteActiva", async ({
    page,
  }) => {
    await page.route("**/api/turnos/current**", (r) =>
      r.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              slotId: "ffffffff-0000-0000-0000-000000000001",
              casillaId: INSUMOS,
              casillaNombre: "INSUMOS",
              casillaColor: "#F7941D",
              horaInicio: "08:30:00",
              horaFin: "11:00:00",
              diaSemana: 0,
              operadores: [op(MARIANO)],
              isCurrent: true,
              isNext: false,
            },
          ],
          total: 1,
          page: 1,
          size: 200,
          varianteActiva: { id: VARIANTE_GUARDADA.id, motivo: "Vacaciones M. J. Vela", desde: "2026-08-24", hasta: "2026-08-28" },
        }),
      }),
    );
    await page.goto("/");
    await expect(page.getByText("Grilla de vacaciones hasta el 28/08")).toBeVisible();
    await expect(page.getByText("Mariano Gomez").first()).toBeVisible();
  });

  test("aprobaciones: la decisión con afectaTurnos muestra el banner con CTA al editor precargado", async ({
    page,
  }) => {
    const solicitud = {
      id: "dddddddd-0000-0000-0000-000000000009",
      empleadoId: "cccccccc-0000-0000-0000-000000000009",
      empleadoNombre: "Maria Jose Vela",
      empleadoColor: "#F7941D",
      sectorNombre: "Soporte",
      sectorColor: "#58595B",
      startDate: "2026-08-24",
      endDate: "2026-08-28",
      daysRequested: 5,
      chargedToYear: 2026,
      reason: null,
      status: "PENDING",
      createdAt: "2026-08-20T12:00:00Z",
      aprobaciones: [],
    };
    await page.route("**/api/vacaciones/solicitudes**", async (r) => {
      const url = new URL(r.request().url());
      if (r.request().method() === "POST" && url.pathname.endsWith("/decision")) {
        await r.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            ...solicitud,
            status: "APPROVED",
            afectaTurnos: { userId: MAJO, desde: "2026-08-24", hasta: "2026-08-28" },
          }),
        });
      } else if (r.request().method() === "GET") {
        await r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(page_([solicitud])) });
      } else {
        await r.fallback();
      }
    });

    await page.goto("/vacaciones/aprobaciones");
    await page.getByRole("button", { name: /Maria Jose Vela/ }).click();
    await page.getByRole("button", { name: "Aprobar" }).click();

    const banner = page.getByRole("status");
    await expect(banner).toContainText("Maria Jose Vela tiene turnos de casilla entre el 24/08/2026 y el 28/08/2026");
    const cta = banner.getByRole("link", { name: "Armar grilla de cobertura →" });
    await expect(cta).toHaveAttribute(
      "href",
      `/admin/turnos?tab=vacaciones&ausente=${MAJO}&desde=2026-08-24&hasta=2026-08-28&motivo=Vacaciones+Maria+Jose+Vela`,
    );
  });
});
