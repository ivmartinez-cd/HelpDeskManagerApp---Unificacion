import { expect, test } from "@playwright/test";

// ---------------------------------------------------------------------------
// Fixtures de mock — deben ser coherentes entre sí (el TSV que devuelve
// extract-logs es el que se pasa al analysis/preview, y los incidentes del
// panel derivan de esa respuesta de preview).
// ---------------------------------------------------------------------------

const MOCK_TSV = [
  "EventType\tCode\tTimestamp\tCounter\tFirmware\tHelpRef",
  "ERROR\t13.DA.EE\t2026-08-15T14:30:00\t221678\t5.09.0\t",
  "ERROR\t13.DA.EE\t2026-08-14T09:12:00\t221450\t5.09.0\t",
  "WARNING\tW-041\t2026-08-13T17:45:00\t221200\t5.09.0\t",
  "INFO\t40.00.00\t2026-08-12T08:00:00\t220900\t5.09.0\t",
].join("\n");

const MOCK_SDS_EXTRACT = {
  device_id: "abc123",
  model_name: "HP LaserJet Managed E82650z",
  tsv: MOCK_TSV,
  help_urls_updated: 3,
};

const MOCK_INCIDENT = {
  id: "inc-001",
  code: "13.DA.EE",
  classification: "FUSOR",
  severity: "ERROR",
  severity_weight: 3,
  occurrences: 2,
  start_time: "2026-08-14T09:12:00",
  end_time: "2026-08-15T14:30:00",
  counter_range: [221450, 221678],
  sds_link: null,
  code_description: "Fuser error",
};

const MOCK_ANALYSIS = {
  events: [
    {
      type: "ERROR",
      code: "13.DA.EE",
      timestamp: "2026-08-15T14:30:00",
      counter: 221678,
      firmware: "5.09.0",
      help_reference: null,
      code_severity: "ERROR",
      code_description: "Fuser error",
      code_solution_url: null,
    },
    {
      type: "ERROR",
      code: "13.DA.EE",
      timestamp: "2026-08-14T09:12:00",
      counter: 221450,
      firmware: "5.09.0",
      help_reference: null,
      code_severity: "ERROR",
      code_description: "Fuser error",
      code_solution_url: null,
    },
    {
      type: "WARNING",
      code: "W-041",
      timestamp: "2026-08-13T17:45:00",
      counter: 221200,
      firmware: "5.09.0",
      help_reference: null,
      code_severity: "WARNING",
      code_description: "Paper jam warning",
      code_solution_url: null,
    },
    {
      type: "INFO",
      code: "40.00.00",
      timestamp: "2026-08-12T08:00:00",
      counter: 220900,
      firmware: "5.09.0",
      help_reference: null,
      code_severity: "INFO",
      code_description: "Ready",
      code_solution_url: null,
    },
  ],
  incidents: [MOCK_INCIDENT],
  global_severity: "ERROR",
  events_count: 4,
  codes_new: [],
  errors: [],
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function mockExtractAndAnalysis(page: import("@playwright/test").Page) {
  page.route("**/api/analisis-log-hp/sds/extract-logs", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_SDS_EXTRACT),
    });
  });
  page.route("**/api/analisis-log-hp/analysis/preview", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_ANALYSIS),
    });
  });
}

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

test.describe("Módulo Análisis de Log HP", () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: "hdm_session", value: "playwright-test", domain: "localhost", path: "/" },
    ]);
  });

  // -------------------------------------------------------------------------
  // Pantalla 1 — Bienvenida
  // -------------------------------------------------------------------------

  test("debe mostrar la pantalla de bienvenida con título, toggle y estado vacío @smoke", async ({ page }) => {
    await page.goto("/analisis-log-hp");

    // Título en dos partes: "HP Logs" y "ANALYZER"
    await expect(page.getByText("HP Logs")).toBeVisible();
    await expect(page.getByText("ANALYZER")).toBeVisible();

    // Toggle de modo (Buscar por Serie activo por defecto)
    await expect(page.getByRole("radio", { name: "Buscar por Serie" })).toBeChecked();
    await expect(page.getByRole("radio", { name: "Análisis Manual" })).not.toBeChecked();

    // Input y botón de acción
    await expect(page.getByPlaceholder(/Ingrese Serie/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Analizar" })).toBeDisabled();

    // Empty state
    await expect(page.getByText("Sin diagnóstico todavía")).toBeVisible();
  });

  test("debe habilitar el botón Analizar solo cuando hay texto en el input de serie", async ({ page }) => {
    await page.goto("/analisis-log-hp");

    const btn = page.getByRole("button", { name: "Analizar" });
    await expect(btn).toBeDisabled();

    await page.getByPlaceholder(/Ingrese Serie/).fill("MXBCN12345");
    await expect(btn).toBeEnabled();

    await page.getByPlaceholder(/Ingrese Serie/).clear();
    await expect(btn).toBeDisabled();
  });

  test("debe cambiar a modo Análisis Manual al hacer clic en el toggle", async ({ page }) => {
    await page.goto("/analisis-log-hp");

    await page.getByRole("radio", { name: "Análisis Manual" }).click();

    await expect(page.getByRole("radio", { name: "Análisis Manual" })).toBeChecked();
    await expect(page.getByPlaceholder(/Pegá los logs HP/)).toBeVisible();
    await expect(page.getByRole("button", { name: /Iniciar Análisis/ })).toBeVisible();
    // El input de serie desaparece en modo manual
    await expect(page.getByPlaceholder(/Ingrese Serie/)).not.toBeVisible();
  });

  // -------------------------------------------------------------------------
  // Flujo principal — extracción SDS → panel
  // -------------------------------------------------------------------------

  test("debe mostrar el panel de errores al analizar un número de serie válido", async ({ page }) => {
    mockExtractAndAnalysis(page);

    await page.goto("/analisis-log-hp");
    await page.getByPlaceholder(/Ingrese Serie/).fill("MXBCN12345");
    await page.getByRole("button", { name: "Analizar" }).click();

    // Panel de errores
    await expect(page.getByRole("heading", { name: "Panel de errores" })).toBeVisible();
    await expect(page.getByText("HP LaserJet Managed E82650z · S/N MXBCN12345")).toBeVisible();
  });

  test("el panel debe mostrar los 4 KPIs con datos del análisis", async ({ page }) => {
    mockExtractAndAnalysis(page);

    await page.goto("/analisis-log-hp");
    await page.getByPlaceholder(/Ingrese Serie/).fill("MXBCN12345");
    await page.getByRole("button", { name: "Analizar" }).click();

    await expect(page.getByRole("heading", { name: "Panel de errores" })).toBeVisible();

    // KPI labels (uppercase en CSS — buscar por texto exacto del DOM). Cada
    // label aparece dos veces (span del KPI + div de leyenda/tooltip): alcanza
    // con que el primero sea visible.
    await expect(page.getByText("Último error crítico", { exact: false }).first()).toBeVisible();
    await expect(page.getByText("Errores críticos", { exact: false }).first()).toBeVisible();
    await expect(page.getByText("Incidencias activas", { exact: false }).first()).toBeVisible();
    await expect(page.getByText("Tasa de errores", { exact: false }).first()).toBeVisible();

    // El código del último error crítico
    await expect(page.getByText("13.DA.EE").first()).toBeVisible();
  });

  test("el panel debe mostrar el filtro de severidad con las 3 pills", async ({ page }) => {
    mockExtractAndAnalysis(page);

    await page.goto("/analisis-log-hp");
    await page.getByPlaceholder(/Ingrese Serie/).fill("MXBCN12345");
    await page.getByRole("button", { name: "Analizar" }).click();

    await expect(page.getByRole("heading", { name: "Panel de errores" })).toBeVisible();

    await expect(page.getByRole("button", { name: "ERROR" })).toBeVisible();
    await expect(page.getByRole("button", { name: "WARNING" })).toBeVisible();
    await expect(page.getByRole("button", { name: "INFO" })).toBeVisible();
  });

  test("el panel debe mostrar la sección de timeline con los eventos", async ({ page }) => {
    mockExtractAndAnalysis(page);

    await page.goto("/analisis-log-hp");
    await page.getByPlaceholder(/Ingrese Serie/).fill("MXBCN12345");
    await page.getByRole("button", { name: "Analizar" }).click();

    await expect(page.getByRole("heading", { name: "Panel de errores" })).toBeVisible();
    await expect(page.getByText("Timeline de errores", { exact: false })).toBeVisible();
    // Los filtros de rango temporal. `exact`: hay otro botón cuyo nombre contiene
    // "Todo" (filtro desplegable); la pill de rango es la que dice exactamente "Todo".
    await expect(page.getByRole("button", { name: "Todo", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "7 días" })).toBeVisible();
  });

  // -------------------------------------------------------------------------
  // Interacciones del panel
  // -------------------------------------------------------------------------

  test("el botón Volver del panel debe regresar a la pantalla de bienvenida", async ({ page }) => {
    mockExtractAndAnalysis(page);

    await page.goto("/analisis-log-hp");
    await page.getByPlaceholder(/Ingrese Serie/).fill("MXBCN12345");
    await page.getByRole("button", { name: "Analizar" }).click();

    await expect(page.getByRole("heading", { name: "Panel de errores" })).toBeVisible();

    // Botón ← (aria-label o title "Volver")
    await page.getByTitle("Volver").click();

    await expect(page.getByText("Sin diagnóstico todavía")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Panel de errores" })).not.toBeVisible();
  });

  test("el filtro de severidad activo debe mostrar el botón Limpiar", async ({ page }) => {
    mockExtractAndAnalysis(page);

    await page.goto("/analisis-log-hp");
    await page.getByPlaceholder(/Ingrese Serie/).fill("MXBCN12345");
    await page.getByRole("button", { name: "Analizar" }).click();

    await expect(page.getByRole("heading", { name: "Panel de errores" })).toBeVisible();

    // Sin filtro activo: Limpiar no debe estar visible
    await expect(page.getByRole("button", { name: "Limpiar" })).not.toBeVisible();

    // Activar filtro ERROR
    await page.getByRole("button", { name: "ERROR" }).click();
    await expect(page.getByRole("button", { name: "Limpiar" })).toBeVisible();

    // Limpiar resetea el filtro
    await page.getByRole("button", { name: "Limpiar" }).click();
    await expect(page.getByRole("button", { name: "Limpiar" })).not.toBeVisible();
  });

  // -------------------------------------------------------------------------
  // Modo manual
  // -------------------------------------------------------------------------

  test("debe mostrar el panel al analizar logs pegados en modo manual", async ({ page }) => {
    page.route("**/api/analisis-log-hp/analysis/preview", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_ANALYSIS),
      });
    });

    await page.goto("/analisis-log-hp");
    await page.getByRole("radio", { name: "Análisis Manual" }).click();

    await page.getByPlaceholder(/Pegá los logs HP/).fill(MOCK_TSV);
    await page.getByRole("button", { name: /Iniciar Análisis/ }).click();

    await expect(page.getByRole("heading", { name: "Panel de errores" })).toBeVisible();
    // En modo manual el modelo es "Análisis Manual"
    await expect(page.getByText("Análisis Manual · S/N MANUAL")).toBeVisible();
  });

  // -------------------------------------------------------------------------
  // Estado de error
  // -------------------------------------------------------------------------

  test("debe mostrar mensaje de error cuando SDS falla", async ({ page }) => {
    page.route("**/api/analisis-log-hp/sds/extract-logs", async (route) => {
      await route.fulfill({
        status: 502,
        contentType: "application/json",
        body: JSON.stringify({ message: "HP SDS Portal no disponible", code: "EXTERNAL_SERVICE_ERROR" }),
      });
    });

    await page.goto("/analisis-log-hp");
    await page.getByPlaceholder(/Ingrese Serie/).fill("MXBCN99999");
    await page.getByRole("button", { name: "Analizar" }).click();

    await expect(page.getByText("HP SDS Portal no disponible")).toBeVisible();
    // El panel NO debe aparecer
    await expect(page.getByRole("heading", { name: "Panel de errores" })).not.toBeVisible();
  });
});
