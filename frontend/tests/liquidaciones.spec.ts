import { expect, test } from "./fixtures";

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
  nroSerie: "SN-ABC-123",
  tipo: "correctivo",
  empresaNombre: "EMPRESA TEST",
  sucursalNombre: "SUCURSAL CENTRO",
  fechaCierre: "2026-08-05",
  costoServicioCobrado: 15000,
  cantKmCobrado: 50.7,
  costoTotalCobrado: 16500,
  costoServicioEsperado: 14000,
  cantKmEsperado: 45,
  estadoValidacion: "con_alertas",
  localidadCliente: "Villa Mercedes",
  spstId: null,
  urlMaps: "https://maps.google.com/?q=test",
};

const INCIDENTE_SIN_TABLA = {
  id: "99999999-9999-9999-9999-999999999999",
  numeroIncidente: "INC-2026-0002",
  nroSerie: "SN-ABC-123",
  tipo: "correctivo",
  empresaNombre: "EMPRESA SIN TABLA",
  sucursalNombre: "SUCURSAL NORTE",
  fechaCierre: "2026-08-05",
  costoServicioCobrado: 8000,
  cantKmCobrado: 30,
  costoTotalCobrado: 8000,
  costoServicioEsperado: null,
  cantKmEsperado: null,
  estadoValidacion: "ok",
  localidadCliente: null,
  spstId: null,
  urlMaps: null,
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

// Dos vigencias del mismo grupo (correctivo, sin zona): la más nueva vigente
// hoy, la vieja cerrada — alcanza para el timeline con variación +10%.
const TARIFA_VIGENTE = {
  id: "66666666-6666-6666-6666-666666666666",
  prestadorId: PST_ID,
  tipoServicio: "correctivo",
  zona: null,
  costoServicio: 11000,
  costoKm: 550,
  vigenciaDesde: "2026-01-01",
  vigenciaHasta: null,
  createdAt: "2026-01-01T00:00:00Z",
};

const TARIFA_ANTERIOR = {
  ...TARIFA_VIGENTE,
  id: "77777777-7777-7777-7777-777777777777",
  costoServicio: 10000,
  costoKm: 500,
  vigenciaDesde: "2025-01-01",
  vigenciaHasta: "2025-12-31",
};

const TABLA_KM = {
  id: "88888888-8888-8888-8888-888888888888",
  prestadorId: PST_ID,
  spstId: null,
  empresaNombre: "EMPRESA TEST",
  sucursalNombre: "SUCURSAL CENTRO",
  observaciones: null,
  domicilioCliente: null,
  localidadCliente: null,
  provinciaCliente: null,
  kmsRecorrido: 30,
  umbralViatico: 30,
  aplicaViatico: false,
  kmsAFacturar: 30,
  urlMaps: null,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
};

const DETALLE_RESPONSE = {
  liquidacion: LIQUIDACION,
  incidentes: [INCIDENTE],
  alertas: [ALERTA],
  observaciones: [],
};

test.describe("Módulo de Liquidaciones", () => {
  test.beforeEach(async ({ page }) => {
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

  test("dashboard muestra los 4 KPI tiles y la tabla de últimas liquidaciones @smoke", async ({
    page,
  }) => {
    await page.goto("/liquidaciones");

    await expect(page.getByText("Liquidaciones pendientes")).toBeVisible();
    await expect(page.getByText("Total importadas")).toBeVisible();
    await expect(page.getByText("Total incidentes")).toBeVisible();
    await expect(page.getByText("Total facturado")).toBeVisible();

    await expect(page.getByText("Últimas liquidaciones")).toBeVisible();
    await expect(page.getByRole("cell", { name: "Córdoba — Pentacom S.A." })).toBeVisible();
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
    // KPI de alertas cuenta pendientes/en_revision en vivo sobre `alertas`
    // (fix 8272396), no el liquidacion.totalAlertas=3 fijado al importar —
    // el fixture ALERTA trae una sola alerta en estado "pendiente".
    await expect(page.getByText("1", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "↻ Reanalizar" })).toBeVisible();
    await expect(page.getByRole("link", { name: "← Lista de liquidaciones" })).toBeVisible();
  });

  // El select de estado manual solo existe para liquidaciones sin número de
  // AyC (las vinculadas a Canal Directo cambian de estado por la barra AyC:
  // aprobar/observar/anular — ver liquidacion-detalle.tsx). Estos dos tests
  // usan una liquidación local (numeroLiquidacion: null).
  const LIQUIDACION_LOCAL = { ...LIQUIDACION, numeroLiquidacion: null };
  const DETALLE_LOCAL = { ...DETALLE_RESPONSE, liquidacion: LIQUIDACION_LOCAL };

  test("detalle muestra el select de estado con el valor actual", async ({ page }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(DETALLE_LOCAL),
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
        body: JSON.stringify(DETALLE_LOCAL),
      });
    });

    let patchCalled = false;
    await page.route(`**/api/liquidaciones/${LIQ_ID}/estado`, async (route) => {
      patchCalled = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...LIQUIDACION_LOCAL, estado: "recibida" }),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    await page.getByRole("combobox").selectOption("recibida");

    await expect(async () => {
      expect(patchCalled).toBe(true);
    }).toPass();

    await expect(page.getByRole("combobox")).toHaveValue("recibida");
  });

  test("detalle: PATCH /estado con 409 muestra el error y no cambia el select", async ({ page }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(DETALLE_LOCAL),
      });
    });

    await page.route(`**/api/liquidaciones/${LIQ_ID}/estado`, async (route) => {
      await route.fulfill({
        status: 409,
        contentType: "application/json",
        body: JSON.stringify({
          message: "La liquidación fue modificada por otro usuario. Recargá e intentá de nuevo.",
          code: "CONFLICT",
        }),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    await page.getByRole("combobox").selectOption("recibida");

    await expect(
      page.getByText("La liquidación fue modificada por otro usuario. Recargá e intentá de nuevo."),
    ).toBeVisible();
    await expect(page.getByRole("combobox")).toHaveValue("abierta");
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

    await expect(page.getByRole("link", { name: "INC-2026-0001" }).first()).toBeVisible();
    await expect(page.getByText("EMPRESA TEST / SUCURSAL CENTRO")).toBeVisible();
    await expect(page.getByText("● CON ALERTAS")).toBeVisible();

    // Expandir la fila para ver la alerta inline
    await page.getByRole("link", { name: "INC-2026-0001" }).first().click();
    await expect(page.getByText("ALT001")).toBeVisible();
    await expect(page.getByText("Monto cobrado supera el esperado")).toBeVisible();
  });

  test("detalle: tabla de incidentes muestra columnas KMs y Nro Serie", async ({ page }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(DETALLE_RESPONSE),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    // Cabeceras nuevas
    await expect(page.getByRole("columnheader", { name: /Nro Serie/i })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: /KMs cob/i })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: /KMs esp/i })).toBeVisible();

    // Nro de serie del incidente
    await expect(page.getByText("SN-ABC-123")).toBeVisible();

    // KMs cobrado redondeado (50.7 → 51) — cell en la tabla
    await expect(page.getByRole("cell", { name: "51", exact: true })).toBeVisible();

    // KMs esperado en verde (45)
    await expect(page.getByRole("cell", { name: "45", exact: true })).toBeVisible();
  });

  test("detalle: incidente sin entrada en tabla KM muestra 'Sin tabla' en KMs esp.", async ({
    page,
  }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...DETALLE_RESPONSE,
          incidentes: [INCIDENTE_SIN_TABLA],
          alertas: [],
        }),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    await expect(page.getByText("EMPRESA SIN TABLA / SUCURSAL NORTE")).toBeVisible();
    await expect(page.getByText("Sin tabla", { exact: true })).toBeVisible();
  });

  test("detalle: nro de serie duplicado muestra advertencia ⚠", async ({ page }) => {
    // Dos incidentes con el mismo nroSerie "SN-ABC-123". La detección ya no es
    // del cliente: la hace el motor de reglas del backend y llega como alerta
    // ALT010 por incidente (incidentes-tabla.tsx, CODIGO_ALT010); el ⚠ usa la
    // descripción de la alerta como title.
    const DESCRIPCION = "Nro de serie duplicado en esta liquidación";
    const alt010 = (incidenteId: string, id: string) => ({
      ...ALERTA,
      id,
      incidenteId,
      tipoAlerta: "ALT010",
      descripcion: DESCRIPCION,
    });
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...DETALLE_RESPONSE,
          incidentes: [INCIDENTE, INCIDENTE_SIN_TABLA],
          alertas: [
            alt010(INCIDENTE.id, "a1a1a1a1-0000-0000-0000-000000000001"),
            alt010(INCIDENTE_SIN_TABLA.id, "a1a1a1a1-0000-0000-0000-000000000002"),
          ],
        }),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    // Ambos tienen nroSerie "SN-ABC-123" → deben mostrar ⚠
    const warnings = page.getByTitle(DESCRIPCION);
    await expect(warnings).toHaveCount(2);
  });

  test("detalle: observación pendiente muestra acciones y PATCH cambia el estado", async ({
    page,
  }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...DETALLE_RESPONSE, alertas: [], observaciones: [OBSERVACION] }),
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
    await expect(page.getByRole("button", { name: "Nuevo prestador" })).toBeVisible();
  });

  test("tarifarios: agrupa por servicio y el timeline muestra la variación entre vigencias", async ({
    page,
  }) => {
    await page.route("**/api/liquidaciones/tarifarios**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [TARIFA_VIGENTE, TARIFA_ANTERIOR],
          total: 2,
          page: 1,
          size: 1000,
        }),
      });
    });

    await page.goto("/liquidaciones/configuracion/tarifarios");
    await page.getByLabel("Filtrar por prestador").selectOption(PST_ID);

    // Grupo con resumen de la tarifa vigente
    await expect(page.getByText("2 tarifas en 1 servicios de PENTACOM")).toBeVisible();
    await expect(page.getByRole("heading", { name: "correctivo" })).toBeVisible();
    await expect(page.getByText("Costo servicio", { exact: true })).toBeVisible();

    // Timeline expandible con badges de vigencia y variación
    await page.getByRole("button", { name: /Historial \(2\)/ }).click();
    await expect(page.getByText("Línea de tiempo de tarifas")).toBeVisible();
    await expect(page.getByText("Vigente hoy")).toBeVisible();
    await expect(page.getByText("+10.0%")).toBeVisible();
    await expect(page.getByText("Inicial")).toBeVisible();
  });

  test("tarifarios: Actualizar abre el modal prefijado con el grupo", async ({ page }) => {
    await page.route("**/api/liquidaciones/tarifarios**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [TARIFA_VIGENTE, TARIFA_ANTERIOR],
          total: 2,
          page: 1,
          size: 1000,
        }),
      });
    });

    await page.goto("/liquidaciones/configuracion/tarifarios");
    await page.getByLabel("Filtrar por prestador").selectOption(PST_ID);
    await page.getByRole("button", { name: "Actualizar" }).click();

    const dialog = page.getByRole("dialog", { name: "Nueva tarifa" });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByLabel("Tipo de servicio *")).toHaveValue("correctivo");
    await expect(dialog.getByLabel("Costo servicio (ARS) *")).toHaveValue("11000");
  });

  test("tabla KM: muestra las entradas del prestador seleccionado", async ({ page }) => {
    await page.route("**/api/liquidaciones/spsts**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, size: 500 }),
      });
    });
    await page.route("**/api/liquidaciones/tabla-km**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [TABLA_KM], total: 1, page: 1, size: 1000 }),
      });
    });

    await page.goto("/liquidaciones/configuracion/tabla-km");
    await page.getByLabel("Filtrar por PST").selectOption(PST_ID);

    await expect(page.getByText("1 entradas de PENTACOM")).toBeVisible();
    await expect(page.getByRole("cell", { name: "EMPRESA TEST" })).toBeVisible();
    await expect(page.getByRole("cell", { name: "SUCURSAL CENTRO" })).toBeVisible();
  });
});
