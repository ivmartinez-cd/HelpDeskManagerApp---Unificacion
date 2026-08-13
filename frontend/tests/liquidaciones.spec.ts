import { expect, test } from "@playwright/test";

const PST_ID = "11111111-1111-1111-1111-111111111111";
const LIQ_ID = "22222222-2222-2222-2222-222222222222";
const INC_ID = "33333333-3333-3333-3333-333333333333";

const PRESTADOR = {
  id: PST_ID,
  nombre: "Pentacom S.A.",
  nombreCorto: "PENTACOM",
  cuit: "30-12345678-9",
  region: "Córdoba",
  activo: true,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
};

const LIQUIDACION = {
  id: LIQ_ID,
  prestadorId: PST_ID,
  numeroLiquidacion: "LIQ-0001",
  periodo: "2026-08",
  tipoLiquidacion: "regular",
  nombreArchivo: "liquidacion_0001_20260812.xls",
  fechaImportacion: "2026-08-12T10:00:00Z",
  estado: "abierta",
  totalIncidentes: 42,
  totalAlertas: 3,
  totalImporte: 88117657.65,
};

const INCIDENTE = {
  id: INC_ID,
  numeroIncidente: "INC-2026-0001",
  tipo: "correctivo",
  empresaNombre: "EMPRESA TEST",
  sucursalNombre: "SUCURSAL CENTRO",
  fechaCierre: "2026-08-05",
  costoServicioCobrado: 15000,
  cantKmCobrado: 50,
  costoTotalCobrado: 16500,
  costoServicioEsperado: 14000,
  cantKmEsperado: 45,
  estadoValidacion: "con_alertas",
  localidadCliente: "Villa Mercedes",
  spstId: null,
  urlMaps: "https://maps.google.com/?q=test",
};

const OBSERVACION = {
  id: "55555555-5555-5555-5555-555555555555",
  tipoObservacion: "RUTA_COMPARTIDA",
  severidad: "ADVERTENCIA",
  titulo: "Ruta compartida entre incidentes",
  descripcion: "Dos incidentes comparten viaje",
  montoCobrado: 20000,
  montoEsperado: 10000,
  diferencia: 10000,
  estado: "pendiente",
  fechaGeneracion: "2026-08-12T10:02:00Z",
};

const ALERTA = {
  id: "44444444-4444-4444-4444-444444444444",
  incidenteId: INC_ID,
  tipoAlerta: "ALT001",
  descripcion: "Monto cobrado supera el esperado",
  datosContexto: null,
  riesgo: 0.8,
  estado: "pendiente",
  fechaGeneracion: "2026-08-12T10:01:00Z",
};

const PAGE_RESPONSE = {
  items: [LIQUIDACION],
  total: 1,
  page: 1,
  size: 50,
};

const DETALLE_RESPONSE = {
  liquidacion: LIQUIDACION,
  incidentes: [INCIDENTE],
  alertas: [ALERTA],
  observaciones: [],
};

test.describe("Módulo de Liquidaciones", () => {
  test.beforeEach(async ({ page, context }) => {
    // El proxy (proxy.ts/middleware) redirige a /login si no hay cookie hdm_session.
    // Solo necesita existir — la validez real la chequea el layout contra el mock backend.
    await context.addCookies([
      { name: "hdm_session", value: "playwright-test", domain: "localhost", path: "/" },
    ]);

    // auth/me y auth/modules los maneja el mock backend global (global-setup.ts)
    // Acá solo mockeamos los datos de negocio (llamadas client-side)

    await page.route("**/api/liquidaciones/prestadores**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [PRESTADOR], total: 1, page: 1, size: 500 }),
      });
    });

    // Usa función predicate para evitar ambigüedad con /api/liquidaciones/prestadores
    await page.route(
      (url) => url.pathname === "/api/liquidaciones",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(PAGE_RESPONSE),
        });
      },
    );
  });

  // ── Dashboard ─────────────────────────────────────────────────────────────

  test("dashboard muestra los 4 KPI tiles y la tabla de últimas liquidaciones", async ({
    page,
  }) => {
    await page.goto("/liquidaciones");

    await expect(page.getByText("Liquidaciones pendientes")).toBeVisible();
    await expect(page.getByText("Total importadas")).toBeVisible();
    await expect(page.getByText("Total incidentes")).toBeVisible();
    await expect(page.getByText("Total facturado")).toBeVisible();

    await expect(page.getByText("Últimas liquidaciones")).toBeVisible();
    await expect(page.getByText("PENTACOM")).toBeVisible();
  });

  test("dashboard muestra el link 'Ver todas' que navega a la lista", async ({ page }) => {
    await page.goto("/liquidaciones");

    const verTodasLink = page.getByRole("link", { name: "Ver todas" });
    await expect(verTodasLink).toBeVisible();
    await verTodasLink.click();
    await expect(page).toHaveURL("/liquidaciones/lista");
  });

  // ── Lista ─────────────────────────────────────────────────────────────────

  test("lista muestra la tabla con el archivo como link naranja", async ({ page }) => {
    await page.goto("/liquidaciones/lista");

    const archivoLink = page.getByRole("link", {
      name: "liquidacion_0001_20260812.xls",
    });
    await expect(archivoLink).toBeVisible();
    await expect(archivoLink).toHaveAttribute("href", `/liquidaciones/${LIQ_ID}`);
  });

  test("lista muestra el total de liquidaciones y los filtros", async ({ page }) => {
    await page.goto("/liquidaciones/lista");

    await expect(page.getByText("1 liquidaciones")).toBeVisible();
    await expect(page.getByLabel("Filtrar por estado")).toBeVisible();
    await expect(page.getByLabel("Filtrar por prestador")).toBeVisible();
    await expect(page.getByRole("button", { name: "+ Importar" })).toBeVisible();
  });

  test("lista muestra el botón Eliminar por fila", async ({ page }) => {
    await page.goto("/liquidaciones/lista");

    await expect(page.getByRole("button", { name: "Eliminar" })).toBeVisible();
  });

  test("lista: click en Eliminar abre modal de confirmación destructivo", async ({ page }) => {
    await page.goto("/liquidaciones/lista");

    await page.getByRole("button", { name: "Eliminar" }).click();

    const dialog = page.getByRole("dialog", { name: "Eliminar liquidación" });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText("liquidacion_0001_20260812.xls")).toBeVisible();
    await expect(page.getByRole("button", { name: "Cancelar" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Eliminar" }).nth(1)).toBeVisible();
  });

  // ── Detalle ───────────────────────────────────────────────────────────────

  test("detalle muestra el header con metadatos y KPIs", async ({ page }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(DETALLE_RESPONSE),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    await expect(page.getByText("liquidacion_0001_20260812.xls")).toBeVisible();
    await expect(page.getByText("2026-08")).toBeVisible();
    await expect(page.getByText("42")).toBeVisible();
    await expect(page.getByText("3")).toBeVisible();
    await expect(page.getByRole("button", { name: "↻ Reanalizar" })).toBeVisible();
    await expect(page.getByRole("link", { name: "← Lista de liquidaciones" })).toBeVisible();
  });

  test("detalle muestra el select de estado con el valor actual", async ({ page }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(DETALLE_RESPONSE),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    const estadoSelect = page.getByRole("combobox");
    await expect(estadoSelect).toBeVisible();
    await expect(estadoSelect).toHaveValue("abierta");
  });

  test("detalle: cambiar estado llama PATCH /estado y actualiza el select", async ({ page }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(DETALLE_RESPONSE),
      });
    });

    let patchCalled = false;
    await page.route(`**/api/liquidaciones/${LIQ_ID}/estado`, async (route) => {
      patchCalled = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...LIQUIDACION, estado: "recibida" }),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    await page.getByRole("combobox").selectOption("recibida");

    await expect(async () => {
      expect(patchCalled).toBe(true);
    }).toPass();

    await expect(page.getByRole("combobox")).toHaveValue("recibida");
  });

  test("detalle muestra la tabla de incidentes con fila expandible", async ({ page }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(DETALLE_RESPONSE),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    await expect(page.getByText("INC-2026-0001")).toBeVisible();
    await expect(page.getByText("EMPRESA TEST / SUCURSAL CENTRO")).toBeVisible();
    await expect(page.getByText("Con alertas")).toBeVisible();

    // Expandir la fila para ver la alerta inline
    await page.getByText("INC-2026-0001").click();
    await expect(page.getByText("ALT001")).toBeVisible();
    await expect(page.getByText("Monto cobrado supera el esperado")).toBeVisible();
  });

  test("detalle: observación pendiente muestra acciones y PATCH cambia el estado", async ({
    page,
  }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...DETALLE_RESPONSE, observaciones: [OBSERVACION] }),
      });
    });

    let patchBody: unknown = null;
    await page.route(
      `**/api/liquidaciones/${LIQ_ID}/observaciones/${OBSERVACION.id}/estado`,
      async (route) => {
        patchBody = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ ...OBSERVACION, estado: "en_revision" }),
        });
      },
    );

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    await expect(page.getByText("Ruta compartida entre incidentes")).toBeVisible();
    await expect(page.getByRole("button", { name: "Aprobar excepción" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Resolver" })).toBeVisible();

    await page.getByRole("button", { name: "Revisar" }).click();

    await expect(async () => {
      expect(patchBody).toEqual({ estado: "en_revision" });
    }).toPass();
  });

  // ── Configuración ─────────────────────────────────────────────────────────

  test("página de configuración de prestadores carga sin error", async ({ page }) => {
    await page.goto("/liquidaciones/configuracion/prestadores");

    await expect(page.getByRole("cell", { name: "PENTACOM", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Crear prestador" })).toBeVisible();
  });
});
