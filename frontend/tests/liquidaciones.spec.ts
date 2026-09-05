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

const ALERTA = {
  id: "44444444-4444-4444-4444-444444444444",
  incidenteId: INC_ID,
  tipoAlerta: "ALT001",
  descripcion: "Monto cobrado supera el esperado",
  datosContexto: null,
  riesgo: 0.8,
  estado: "pendiente",
  fechaGeneracion: "2026-08-12T10:01:00Z",
  justificacion: null,
  incidenteRelacionadoId: null,
  esGrupo: false,
  grupoIncidenteIds: [],
  montoCobrado: null,
  montoEsperado: null,
  diferencia: null,
};

// Ex `Observacion` — ahora es una `Alerta` con esGrupo=true (unificación
// 2026-09-04). ALT005 agrupa dos incidentes que comparten viaje/ruta.
const ALERTA_GRUPO = {
  id: "55555555-5555-5555-5555-555555555555",
  incidenteId: INC_ID,
  tipoAlerta: "ALT005",
  descripcion: "Ruta compartida entre incidentes",
  datosContexto: null,
  riesgo: 60,
  estado: "pendiente",
  fechaGeneracion: "2026-08-12T10:02:00Z",
  justificacion: null,
  incidenteRelacionadoId: null,
  esGrupo: true,
  grupoIncidenteIds: [INC_ID, INCIDENTE_SIN_TABLA.id],
  montoCobrado: 20000,
  montoEsperado: 10000,
  diferencia: 10000,
};

const PAGE_RESPONSE = {
  items: [LIQUIDACION],
  total: 1,
  page: 1,
  size: 50,
};

// Dos vigencias del mismo grupo (correctivo, sin SPST): la más nueva vigente
// hoy, la vieja cerrada — alcanza para el timeline con variación +10%.
const TARIFA_VIGENTE = {
  id: "66666666-6666-6666-6666-666666666666",
  prestadorId: PST_ID,
  tipoServicio: "correctivo",
  spstId: null,
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
    // el fixture ALERTA trae una sola alerta en estado "pendiente". El valor
    // "1" solo, sin scopear al tile, matchea otros "1" de la página (celdas
    // de tabla, contador de issues de Next dev overlay).
    const alertasTileValor = page
      .getByText("Alertas", { exact: true })
      .locator("xpath=following-sibling::span");
    await expect(alertasTileValor).toHaveText("1");
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

    // Expandir la fila para ver la alerta inline — el link al incidente hace
    // stopPropagation (abre Gestión en otra pestaña), hay que clickear la fila.
    await page.locator(`#incidente-row-${INC_ID}`).click();
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

  test("detalle: alerta agrupada (ex observación) se gestiona y el PATCH cambia el estado", async ({
    page,
  }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...DETALLE_RESPONSE, alertas: [ALERTA_GRUPO] }),
      });
    });

    let patchBody: unknown = null;
    await page.route(
      `**/api/liquidaciones/${LIQ_ID}/alertas/${ALERTA_GRUPO.id}/estado`,
      async (route) => {
        patchBody = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ ...ALERTA_GRUPO, estado: "en_revision" }),
        });
      },
    );

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    // Las alertas de un incidente están colapsadas por default — hay que
    // expandir la fila (click) para que aparezca AlertaSubRow.
    await page.locator(`#incidente-row-${INC_ID}`).click();
    await expect(page.getByText("Ruta compartida entre incidentes")).toBeVisible();
    await page.getByRole("button", { name: "Gestionar" }).click();

    const dialog = page.getByRole("dialog", { name: "Gestionar ALT005" });
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: "Revisar", exact: true }).click();
    await dialog.getByRole("button", { name: "Revisar", exact: true }).click();

    await expect(async () => {
      expect(patchBody).toEqual({ estado: "en_revision", incidenteRelacionadoId: null });
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
    await page.route("**/api/liquidaciones/spsts**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, size: 500 }),
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

  test("tarifarios: Nueva vigencia desde hoy abre el modal prefijado con el grupo", async ({ page }) => {
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
    await page.route("**/api/liquidaciones/spsts**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, size: 500 }),
      });
    });

    await page.goto("/liquidaciones/configuracion/tarifarios");
    await page.getByLabel("Filtrar por prestador").selectOption(PST_ID);
    await page.getByRole("button", { name: "Nueva vigencia desde hoy" }).click();

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

  test("detalle: 'Recibir' marca la liquidación como Recibida en Canal Directo", async ({
    page,
  }) => {
    // El botón "Recibir" solo aparece si el estado lo permite (gating real de
    // Web Agentes, ver ayc-acciones-bar.tsx) — acá una preliquidada.
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...DETALLE_RESPONSE,
          liquidacion: { ...LIQUIDACION, estado: "preliquidada" },
        }),
      });
    });
    let recibido = false;
    await page.route(`**/api/liquidaciones/${LIQ_ID}/recibir`, async (route) => {
      recibido = route.request().method() === "POST";
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...LIQUIDACION, estado: "recibida" }),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);
    await page.getByRole("button", { name: "Recibir", exact: true }).click();

    const dialog = page.getByRole("dialog", { name: "Recibir en Canal Directo" });
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: "Recibir", exact: true }).click();

    await expect(page.getByText("Liquidación marcada como Recibida en Canal Directo")).toBeVisible();
    expect(recibido).toBe(true);
  });

  test("detalle: tildar incidentes y resolver sus alertas en lote con un solo motivo", async ({
    page,
  }) => {
    await page.route(`**/api/liquidaciones/${LIQ_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(DETALLE_RESPONSE),
      });
    });
    let bodyLote: unknown = null;
    await page.route(`**/api/liquidaciones/${LIQ_ID}/alertas/estado`, async (route) => {
      bodyLote = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ actualizadas: 1 }),
      });
    });

    await page.goto(`/liquidaciones/${LIQ_ID}`);

    // Sin selección no hay barra
    await expect(page.getByRole("toolbar", { name: "Alertas seleccionadas" })).toBeHidden();

    await page.getByRole("checkbox", { name: "Seleccionar incidente INC-2026-0001" }).check();
    const barra = page.getByRole("toolbar", { name: "Alertas seleccionadas" });
    await expect(barra).toBeVisible();
    await expect(barra.getByText("1 incidente · 1 alerta seleccionada")).toBeVisible();

    await barra.getByRole("button", { name: "Resolver", exact: true }).click();
    const dialog = page.getByRole("dialog", { name: "Resolver 1 alerta" });
    await expect(dialog).toBeVisible();
    await dialog.getByRole("textbox").fill("costo doble acordado para toda la zona");
    await dialog.getByRole("button", { name: "Resolver 1 alerta" }).click();

    await expect(page.getByText("1 alerta resuelta")).toBeVisible();
    expect(bodyLote).toEqual({
      alertaIds: [ALERTA.id],
      estado: "resuelta",
      justificacion: "costo doble acordado para toda la zona",
    });
  });
});
