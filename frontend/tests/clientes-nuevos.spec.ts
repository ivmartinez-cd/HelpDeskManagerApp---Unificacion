import { expect, test, type Page } from "@playwright/test";

// ── Contadores › Clientes nuevos: wire snake_case (clientes_nuevos_schemas.py) ──

const SIGES_BILETTA = {
  empresa_id: 1416,
  equipos_instalados: 11,
  instalas: 4,
  primera_instalacion: "2026-08-06",
  ultima_instalacion: "2026-08-21",
  equipos_con_toma: 11,
  contrato_nro: "SOD36CDSI00837",
  fecha_firma: "2026-07-28",
  vendedor: "Adrián Vanrell",
  rubro: "IMPRESION",
};

const FICHA_BILETTA = {
  id: "11111111-1111-1111-1111-111111111111",
  cliente: "EXPRESO BILETTA",
  siges_empresa_id: 1416,
  contrato_nro: "SOD36CDSI00837",
  fecha_firma: "2026-07-28",
  vendedor: "AV",
  operador_id: "marodriguez",
  implementacion_servicio: "MPS",
  fecha_estimada_implementacion: "2026-08-20",
  fecha_estimada_primera_facturacion: "2026-10-01",
  dia_corte: null,
  equipos_previstos: 10,
  estado: "ESPERANDO_INSTALACION",
  stc_enviado_el: null,
  notas: "FE 1º FC 1/10/2026 - Instalaciones 20/08",
  created_at: "2026-08-05T16:09:00Z",
  updated_at: "2026-08-05T16:09:00Z",
  siges: SIGES_BILETTA,
  listo_para_stc: true,
};

const FICHA_ROSMI = {
  ...FICHA_BILETTA,
  id: "22222222-2222-2222-2222-222222222222",
  cliente: "NEUMATICOS ROSMI SRL",
  siges_empresa_id: 1412,
  contrato_nro: "NEUMATICOS ROSMI SRL",
  vendedor: "GL",
  dia_corte: 25,
  fecha_estimada_primera_facturacion: "2026-08-25",
  equipos_previstos: 14,
  estado: "STC_ENVIADO",
  stc_enviado_el: "2026-08-10",
  siges: { ...SIGES_BILETTA, empresa_id: 1412, equipos_instalados: 14, equipos_con_toma: 14 },
  listo_para_stc: false,
};

const FICHA_CERRADA = {
  ...FICHA_BILETTA,
  id: "33333333-3333-3333-3333-333333333333",
  cliente: "CARTOCOR",
  siges_empresa_id: null,
  siges: null,
  estado: "CERRADO",
  listo_para_stc: false,
};

const OPERADORES = [
  { id: "marodriguez", nombre: "Marcela Rodríguez", color: "#888200" },
  { id: "vipaez", nombre: "Victor Paez", color: null },
];

const CANDIDATOS = {
  candidatos: [
    {
      empresa_id: 1411,
      cliente: "FURLONG",
      contrato_nro: "FURLONG DEMO",
      fecha_firma: "2026-07-01",
      vendedor: "Adrián Vanrell",
      rubro: "IMPRESION",
      equipos_instalados: 0,
    },
  ],
  firmado_desde: "2026-04-23",
};

async function mockClientesNuevos(page: Page, fichas: unknown[] = [FICHA_BILETTA, FICHA_ROSMI, FICHA_CERRADA]) {
  await page.route("**/api/contadores/calendario/operadores**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: OPERADORES, total: 2, page: 1, size: 2000 }),
    });
  });
  await page.route("**/api/contadores/clientes-nuevos/candidatos**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(CANDIDATOS) });
  });
  await page.route("**/api/contadores/clientes-nuevos?**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: fichas, total: fichas.length, page: 1, size: 500 }),
      });
    } else {
      await route.fallback();
    }
  });
}

test.describe("Contadores › Clientes nuevos", () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: "hdm_session", value: "playwright-test", domain: "localhost", path: "/" },
    ]);
  });

  test("listado: KPIs, fichas abiertas por defecto, aviso listo para STC", async ({ page }) => {
    await mockClientesNuevos(page);
    await page.goto("/contadores/clientes-nuevos");

    await expect(page.getByRole("heading", { name: "Clientes nuevos" })).toBeVisible();
    await expect(page.getByText("EXPRESO BILETTA")).toBeVisible();
    await expect(page.getByText("NEUMATICOS ROSMI SRL", { exact: true })).toBeVisible();
    // La cerrada no entra en el filtro "Abiertas" por defecto.
    await expect(page.getByText("CARTOCOR")).toBeHidden();
    await expect(page.getByText("Listo para STC", { exact: true })).toBeVisible();
    await expect(page.getByText("11 / 10 · últ. 21/08/2026")).toBeVisible();
    await expect(page.getByText("Marcela Rodríguez")).toHaveCount(2);
    await expect(page.getByText("STC enviado", { exact: true }).first()).toBeVisible();

    await page.getByRole("radio", { name: "Cerradas" }).click();
    await expect(page.getByText("CARTOCOR")).toBeVisible();
    await expect(page.getByText("EXPRESO BILETTA")).toBeHidden();
    await page.screenshot({ path: "test-results/clientes-nuevos.png", fullPage: true });
  });

  test("empty state sin fichas", async ({ page }) => {
    await mockClientesNuevos(page, []);
    await page.goto("/contadores/clientes-nuevos");
    await expect(page.getByText("Todavía no hay fichas")).toBeVisible();
  });

  test("alta manual hace POST snake_case y refresca", async ({ page }) => {
    await mockClientesNuevos(page);
    let postBody: Record<string, unknown> | null = null;
    await page.route("**/api/contadores/clientes-nuevos", async (route) => {
      if (route.request().method() === "POST") {
        postBody = route.request().postDataJSON() as Record<string, unknown>;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ ...FICHA_BILETTA, id: "99999999-9999-9999-9999-999999999999", cliente: "BP" }),
        });
      } else {
        await route.fallback();
      }
    });

    await page.goto("/contadores/clientes-nuevos");
    await page.getByRole("button", { name: "Nueva ficha" }).click();
    const dialog = page.getByRole("dialog", { name: "Nueva ficha de cliente" });
    await expect(dialog).toBeVisible();
    await dialog.getByLabel("Cliente", { exact: true }).fill("BP");
    await dialog.getByLabel("Vendedor / ejecutivo").fill("ER");
    await dialog.getByLabel("Día de corte (vacío = a definir)").fill("31");
    await dialog.getByLabel("Operador").selectOption("vipaez");
    await dialog.getByRole("button", { name: "Crear ficha" }).click();

    await expect(dialog).toBeHidden();
    expect(postBody).not.toBeNull();
    expect(postBody).toMatchObject({
      cliente: "BP",
      vendedor: "ER",
      dia_corte: 31,
      operador_id: "vipaez",
      estado: "ESPERANDO_INSTALACION",
      siges_empresa_id: null,
    });
  });

  test("sugerencias de Siges precargan la ficha", async ({ page }) => {
    await mockClientesNuevos(page);
    await page.goto("/contadores/clientes-nuevos");
    await page.getByRole("button", { name: "Sugerencias de Siges" }).click();
    const sugerencias = page.getByRole("dialog", { name: "Sugerencias de Siges" });
    await expect(sugerencias.getByText("FURLONG", { exact: true })).toBeVisible();
    await expect(sugerencias.getByText("Impresión", { exact: true })).toBeVisible();
    await sugerencias.getByRole("button", { name: "Crear ficha" }).click();

    const dialog = page.getByRole("dialog", { name: "Nueva ficha de cliente" });
    await expect(dialog.getByLabel("Cliente", { exact: true })).toHaveValue("FURLONG");
    await expect(dialog.getByLabel("Contrato N°")).toHaveValue("FURLONG DEMO");
    await expect(dialog.getByLabel("Fecha de firma")).toHaveValue("2026-07-01");
    await expect(dialog.getByText("Cruzada con ID_Empresa 1411", { exact: false })).toBeVisible();
  });
});
