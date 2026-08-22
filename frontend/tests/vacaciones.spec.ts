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
  // El listado trae los saldos del ciclo en curso y el siguiente (contrato
  // real de GET /empleados); sin esto la tabla rompe al leer saldo.available.
  saldo: { annual: 21, carryOver: 0, used: 7, pending: 0, available: 14, cycleOpen: true },
  saldoSiguiente: null,
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

const AUSENCIA_ID = "ffffffff-0000-0000-0000-000000000001";

const AUSENCIA = {
  id: AUSENCIA_ID,
  empleadoId: EMPLEADO_ID,
  empleadoNombre: "Laura Pérez",
  empleadoColor: "#2563eb",
  sectorNombre: "Soporte Técnico",
  sectorColor: "#2563eb",
  startDate: "2026-08-21",
  endDate: "2026-08-21",
  daysCount: 3, // viernes: corridos + extensión LCT (paridad backend)
  halfDay: false,
  tipo: "BAJA_ENFERMEDAD",
  reason: "Gripe",
  status: "APPROVED",
  createdAt: "2026-08-13T12:00:00Z",
};

const CONFIG = {
  seniorityTiers: [
    { minYears: 0, maxYears: 0.5, days: 7 },
    { minYears: 0.5, maxYears: 5, days: 14 },
    { minYears: 5, maxYears: 10, days: 21 },
    { minYears: 10, maxYears: 20, days: 28 },
    { minYears: 20, maxYears: 99, days: 35 },
  ],
  nextYearOpenMonth: 10,
  nextYearOpenDay: 1,
  allowAdvanceRequest: true,
  maxAdvanceDays: 0,
  allowCarryOver: true,
  maxCarryOverDays: 0,
  minAdvanceNoticeDays: 7,
  maxOverlapPercent: 50,
  maxOverlapCount: 0,
};

const EXCLUSION = {
  id: "99999999-0000-0000-0000-000000000001",
  empleadoAId: EMPLEADO_ID,
  empleadoBId: "cccccccc-0000-0000-0000-000000000002",
  empleadoANombre: "Laura Pérez",
  empleadoBNombre: "Martín García",
};

const REGISTRO_CONFIG = {
  id: "11111111-aaaa-0000-0000-000000000001",
  accion: "UPDATE",
  entidad: "SystemConfig",
  entidadId: "singleton",
  usuarioEmail: "admin@example.com",
  metadata: { changes: ["min_advance_notice_days"] },
  createdAt: "2026-08-13T20:40:52Z",
};

const REGISTRO_AUSENCIA = {
  id: "11111111-aaaa-0000-0000-000000000002",
  accion: "CREATE",
  entidad: "Absence",
  entidadId: AUSENCIA_ID,
  usuarioEmail: "admin@example.com",
  metadata: {
    employee: "Laura Pérez",
    type: "BAJA_ENFERMEDAD",
    startDate: "2026-08-21",
    endDate: "2026-08-21",
    days: 3,
  },
  createdAt: "2026-08-13T20:40:43Z",
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

  test("el dashboard muestra KPIs y calendario @smoke", async ({ page }) => {
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

  test("asistencias: calendario anual, listado y error de solape al registrar", async ({
    page,
  }) => {
    await mockVacaciones(page);
    await page.route("**/api/vacaciones/feriados", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: page_([FERIADO]) }),
    );
    await page.route("**/api/vacaciones/solicitudes**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: page_([]) }),
    );
    await page.route("**/api/vacaciones/ausencias**", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: page_([AUSENCIA]),
        });
      }
      // POST → conflicto de solape del mismo tipo (mensaje real del backend)
      return route.fulfill({
        status: 409,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Ya existe una baja del mismo tipo que se solapa con esas fechas",
          code: "SOLAPAMIENTO_AUSENCIA",
        }),
      });
    });

    await page.goto("/vacaciones/asistencias");

    // KPIs del año (port de getStatsForYear): 1 día de enfermedad
    await expect(page.getByText("Días trabajados")).toBeVisible();
    await expect(page.getByText("Trámites y estudio")).toBeVisible();
    await expect(page.getByText("Calendario de bajas · 2026")).toBeVisible();
    await expect(page.getByText("Total días con baja")).toBeVisible();

    // Listado con la baja y sus acciones
    await page.getByRole("button", { name: "Listado y registros" }).click();
    await expect(page.getByRole("table").getByText("Laura Pérez")).toBeVisible();
    await expect(page.getByRole("table").getByText("Baja por enfermedad")).toBeVisible();
    await expect(page.getByRole("button", { name: "Editar" })).toBeVisible();

    // Registrar → el 409 del backend aparece como banner en el modal
    await page.getByRole("button", { name: "Registrar baja" }).click();
    await page.getByRole("checkbox", { name: /Laura Pérez/ }).check();
    await page.getByRole("button", { name: "Registrar", exact: true }).click();
    await expect(
      page.getByText("Ya existe una baja del mismo tipo que se solapa con esas fechas"),
    ).toBeVisible();
  });

  test("asistencias: reporte de descuentos por técnico", async ({ page }) => {
    await mockVacaciones(page);
    await page.route("**/api/vacaciones/feriados", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: page_([]) }),
    );
    await page.route("**/api/vacaciones/solicitudes**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: page_([]) }),
    );
    await page.route("**/api/vacaciones/ausencias**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: page_([]) }),
    );
    await page.route("**/api/vacaciones/ausencias/reportes/descuentos**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: page_([
          {
            empleadoId: EMPLEADO_ID,
            firstName: "Laura",
            lastName: "Pérez",
            cargoNombre: "Analista Senior",
            diasDescontados: 1,
            diasEnfermedad: 2,
            guardias: 0,
          },
        ]),
      }),
    );

    await page.goto("/vacaciones/asistencias");
    await page.getByRole("button", { name: "Reportes descuentos" }).click();

    await expect(page.getByText(/Días descontables por técnico/)).toBeVisible();
    await expect(page.getByText("Pérez, Laura")).toBeVisible();
    await expect(page.getByText("1 desc. + 2 enf.")).toBeVisible();
  });

  test("configuración: tabs, guardado y solapamientos", async ({ page }) => {
    await mockVacaciones(page);
    await page.route("**/api/vacaciones/exclusiones**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: page_([EXCLUSION]) }),
    );
    let guardado = false;
    await page.route("**/api/vacaciones/config", (route) => {
      if (route.request().method() === "PUT") {
        guardado = true;
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ ...CONFIG, minAdvanceNoticeDays: 8 }),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(CONFIG),
      });
    });

    await page.goto("/vacaciones/configuracion");

    // Tab Antigüedad: tabla editable de rangos
    await expect(
      page.getByText("Rangos de antigüedad y días de vacaciones"),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "+ Agregar rango" })).toBeVisible();

    // Tab Reglas: stepper de aviso + slider de solapamiento
    await page.getByRole("button", { name: "Reglas de Solicitud" }).click();
    await expect(page.getByText("Aviso Previo Mínimo")).toBeVisible();
    await expect(page.getByText("50%")).toBeVisible();
    await page.getByRole("button", { name: "Sumar" }).first().click();

    // Tab Ciclos: toggle de arrastre
    await page.getByRole("button", { name: "Ciclos Anuales" }).click();
    await expect(page.getByText("Arrastrar días no usados")).toBeVisible();
    await expect(page.getByRole("switch")).toBeVisible();

    // Guardar cambios (dirty por el stepper) → PUT /config
    await page.getByRole("button", { name: "Guardar cambios" }).click();
    await expect(page.getByText("Configuración guardada.")).toBeVisible();
    expect(guardado).toBe(true);

    // Tab Solapamientos: exclusiones + límites por cargo (max_simultaneos)
    await page.getByRole("button", { name: "Solapamientos" }).click();
    await expect(page.getByText("Exclusiones Mutuas")).toBeVisible();
    await expect(page.getByText("Martín García")).toBeVisible();
    await expect(page.getByText("Límites por Cargo")).toBeVisible();
    await expect(page.getByText("Máx. 2 simultáneos")).toBeVisible();
  });

  test("reportes: gráfico por sector, tablas con filtro y tabs a auditoría", async ({
    page,
  }) => {
    await mockVacaciones(page);
    await page.route("**/api/vacaciones/auditoria**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: page_([]) }),
    );
    await page.route("**/api/vacaciones/reportes", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          year: 2026,
          porEmpleado: [
            {
              nombre: "Laura Pérez",
              color: "#2563eb",
              sectorNombre: "Soporte Técnico",
              cargoNombre: "Analista Senior",
              annual: 21,
              used: 10,
              pending: 0,
              available: 11,
            },
            {
              nombre: "Martín García",
              color: "#059669",
              sectorNombre: "Logística",
              cargoNombre: "Analista",
              annual: 14,
              used: 0,
              pending: 5,
              available: 9,
            },
          ],
          porSector: [
            {
              nombre: "Logística",
              color: "#059669",
              empleados: 1,
              annual: 14,
              used: 0,
              available: 9,
            },
            {
              nombre: "Soporte Técnico",
              color: "#2563eb",
              empleados: 1,
              annual: 21,
              used: 10,
              available: 11,
            },
          ],
        }),
      }),
    );

    await page.goto("/vacaciones/reportes");

    await expect(
      page.getByText("Días consumidos vs. disponibles por sector"),
    ).toBeVisible();
    await expect(page.getByText("Vacaciones · Ciclo 2026")).toBeVisible();
    await expect(page.getByRole("button", { name: "Excel" })).toBeVisible();
    await expect(page.getByRole("button", { name: "PDF" })).toBeVisible();

    // Tablas por empleado y por sector con los saldos
    await expect(page.getByText("Por empleado", { exact: true })).toBeVisible();
    await expect(page.getByText("Laura Pérez")).toBeVisible();
    await expect(page.getByText("Por sector", { exact: true })).toBeVisible();

    // El filtro de la tabla por empleado descarta a Martín
    await page.getByPlaceholder("Filtrar…").fill("laura");
    await expect(page.getByRole("table").getByText("Martín García")).toBeHidden();
    await expect(page.getByText("Laura Pérez")).toBeVisible();

    // El tab pill navega a Auditoría
    await page
      .getByRole("navigation", { name: "Reportes y auditoría" })
      .getByRole("link", { name: "Auditoría" })
      .click();
    await expect(page).toHaveURL(/\/vacaciones\/auditoria/);
    await expect(page.getByText("Sin registros de auditoría")).toBeVisible();
  });

  test("auditoría: tabla con badges en castellano y detalle expandible", async ({
    page,
  }) => {
    await mockVacaciones(page);
    await page.route("**/api/vacaciones/auditoria**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: page_([REGISTRO_CONFIG, REGISTRO_AUSENCIA]),
      }),
    );

    await page.goto("/vacaciones/auditoria");

    const tabla = page.getByRole("table");
    await expect(tabla.getByText("Edición")).toBeVisible();
    await expect(tabla.getByText("Creación")).toBeVisible();
    await expect(tabla.getByText("Configuración", { exact: true })).toBeVisible();
    await expect(tabla.getByText("Baja", { exact: true })).toBeVisible();
    await expect(
      tabla.getByText("Actualizó la configuración: min_advance_notice_days"),
    ).toBeVisible();
    await expect(page.getByText("Mostrando 2 de 2 registros")).toBeVisible();

    // Expandir la fila de la baja → detalle clave/valor desde metadata
    await tabla.getByRole("button", { name: "Expandir" }).nth(1).click();
    await expect(tabla.getByText("BAJA_ENFERMEDAD")).toBeVisible();
    await expect(tabla.getByRole("definition").filter({ hasText: "Laura Pérez" })).toBeVisible();
  });
});
