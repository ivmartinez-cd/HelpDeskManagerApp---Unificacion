import { expect, test, type Page } from "@playwright/test";

// ── Datos mock (wire camelCase, serialization_alias en los schemas) ─────────

const SECTOR_ID = "aaaaaaaa-0000-0000-0000-000000000001";
const CARGO_ID = "bbbbbbbb-0000-0000-0000-000000000001";
const EMPLEADO_ID = "cccccccc-0000-0000-0000-000000000001";
const SOLICITUD_ID = "dddddddd-0000-0000-0000-000000000001";

const EMPLEADO = {
  id: EMPLEADO_ID,
  firstName: "Laura",
  lastName: "Pérez",
  email: "lperez@canal.com",
  hireDate: "2019-03-15",
  status: "ACTIVE",
  color: "#2563eb",
  departmentId: SECTOR_ID,
  cargoId: CARGO_ID,
  userId: null,
  sectorNombre: "Soporte Técnico",
  sectorColor: "#2563eb",
  cargoNombre: "Analista Senior",
  diasAnuales: 21,
  antiguedadAnios: 7.41,
};

const SECTOR = {
  id: SECTOR_ID,
  name: "Soporte Técnico",
  color: "#2563eb",
  empleadosCount: 1,
  jefes: [],
};

const CARGO = {
  id: CARGO_ID,
  name: "Analista Senior",
  maxSimultaneos: 2,
  empleadosCount: 1,
};

const FERIADO = {
  id: "eeeeeeee-0000-0000-0000-000000000001",
  name: "Año nuevo",
  date: "2026-01-01",
  deductsVacation: false,
};

const SOLICITUD = {
  id: SOLICITUD_ID,
  empleadoId: EMPLEADO_ID,
  empleadoNombre: "Laura Pérez",
  empleadoColor: "#2563eb",
  sectorNombre: "Soporte Técnico",
  sectorColor: "#2563eb",
  startDate: "2026-09-07",
  endDate: "2026-09-11",
  daysRequested: 7,
  chargedToYear: 2026,
  reason: "Vacaciones de prueba",
  status: "PENDING",
  createdAt: "2026-08-13T12:00:00Z",
  aprobaciones: [],
};

const DASHBOARD = {
  totalEmpleados: 1,
  empleadosActivos: 1,
  solicitudesPendientes: 1,
  enVacaciones: [],
  dias: null,
  diasProximo: null,
  diasTotalesEquipo: 21,
  diasDisponiblesEquipo: 14,
};

function page_(items: unknown[]) {
  return JSON.stringify({ items, total: items.length, page: 1, size: 200 });
}

async function mockVacaciones(page: Page) {
  await page.route("**/api/vacaciones/empleados**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: page_([EMPLEADO]) }),
  );
  await page.route("**/api/vacaciones/sectores**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: page_([SECTOR]) }),
  );
  await page.route("**/api/vacaciones/cargos**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: page_([CARGO]) }),
  );
  await page.route("**/api/vacaciones/usuarios**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: page_([]) }),
  );
  await page.route("**/api/vacaciones/dashboard/resumen", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(DASHBOARD),
    }),
  );
  await page.route("**/api/vacaciones/calendario**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: page_([]) }),
  );
}

test.describe("Vacaciones", () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: "hdm_session", value: "playwright-test", domain: "localhost", path: "/" },
    ]);
  });

  test("el dashboard muestra KPIs y calendario", async ({ page }) => {
    await mockVacaciones(page);
    await page.goto("/vacaciones");

    await expect(page.getByText("Total empleados")).toBeVisible();
    await expect(page.getByText("Solicitudes pendientes")).toBeVisible();
    await expect(page.getByText("de 21 totales del equipo")).toBeVisible();
    await expect(page.getByText("Nadie está de vacaciones hoy")).toBeVisible();
    // Grilla mensual con los 7 días de la semana
    await expect(page.getByText("lun", { exact: true })).toBeVisible();
    await expect(page.getByText("dom", { exact: true })).toBeVisible();
  });

  test("solicitudes lista, filtra y muestra el error de negocio al crear", async ({
    page,
  }) => {
    await mockVacaciones(page);
    await page.route("**/api/vacaciones/solicitudes**", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: page_([SOLICITUD]),
        });
      }
      // POST → conflicto de solapamiento (mensaje real del backend)
      return route.fulfill({
        status: 409,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Ya existe una solicitud que se solapa con esas fechas",
          code: "SOLAPAMIENTO_PROPIO",
        }),
      });
    });

    await page.goto("/vacaciones/solicitudes");
    await expect(page.getByText("Laura Pérez")).toBeVisible();
    await expect(page.getByRole("table").getByText("Pendiente")).toBeVisible();

    // Filtro por estado: Rechazada no matchea → empty state
    await page.getByRole("radio", { name: "Rechazada" }).click();
    await expect(page.getByText("No hay solicitudes todavía")).toBeVisible();
    await page.getByRole("radio", { name: "Todas" }).click();

    // Crear → el 409 del backend aparece como banner en el modal
    await page.getByRole("button", { name: "Nueva solicitud" }).click();
    await page.getByRole("button", { name: "Crear solicitud" }).click();
    await expect(
      page.getByText("Ya existe una solicitud que se solapa con esas fechas"),
    ).toBeVisible();
  });

  test("aprobaciones expande la card y decide con comentario", async ({ page }) => {
    await mockVacaciones(page);
    let decidida = false;
    await page.route("**/api/vacaciones/solicitudes", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: page_([
          decidida ? { ...SOLICITUD, status: "APPROVED" } : SOLICITUD,
        ]),
      }),
    );
    await page.route(`**/api/vacaciones/solicitudes/${SOLICITUD_ID}/decision`, (route) => {
      decidida = true;
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...SOLICITUD, status: "APPROVED" }),
      });
    });
    await page.route(`**/api/vacaciones/ciclos/empleado/${EMPLEADO_ID}**`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          annual: 21,
          carryOver: 0,
          used: 0,
          pending: 7,
          available: 14,
          cycleOpen: true,
        }),
      }),
    );

    await page.goto("/vacaciones/aprobaciones");
    await expect(page.getByText("Pendientes de aprobación")).toBeVisible();

    await page.getByText("Laura Pérez").first().click();
    await expect(page.getByPlaceholder("Comentario (opcional)…")).toBeVisible();
    await expect(page.getByText("Saldo: 14 disp.")).toBeVisible();

    await page.getByPlaceholder("Comentario (opcional)…").fill("OK");
    await page.getByRole("button", { name: "Aprobar" }).click();
    await expect(page.getByText("No hay solicitudes para mostrar")).toBeVisible();
  });

  test("gestión humana: tabs, tabla de empleados e import de feriados", async ({
    page,
  }) => {
    await mockVacaciones(page);
    await page.route("**/api/vacaciones/feriados", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: page_([FERIADO]) }),
    );
    let importado = false;
    await page.route("**/api/vacaciones/feriados/importar/**", (route) => {
      importado = true;
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          year: 2026,
          count: 19,
          message: "Se importaron 19 feriados del año 2026",
        }),
      });
    });

    await page.goto("/vacaciones/gestion");
    await expect(page.getByText("Laura Pérez")).toBeVisible();
    await expect(page.getByRole("button", { name: "Nuevo empleado" })).toBeVisible();

    await page.getByRole("button", { name: "Feriados" }).click();
    await expect(page.getByText("Año nuevo")).toBeVisible();
    await expect(page.getByText("Importar feriados de Argentina")).toBeVisible();

    await page.getByRole("button", { name: /Importar 20/ }).click();
    await expect(page.getByText("Se importaron 19 feriados del año 2026")).toBeVisible();
    expect(importado).toBe(true);
  });
});
