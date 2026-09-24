import type { Page, Route } from "@playwright/test";
import { expect, test } from "./fixtures";

// ── Insumos › Despachados: wire camelCase (despachados_schemas.py / despachados_detalle_schemas.py) ──

const FILA_ROJA = {
  guia: "2610800000000210011",
  color: "rojo",
  alertaAbierta: true,
  observacion: "",
  fechaLimite: "2026-09-25",
  diasHabilesParaLimite: 1,
  estado: "En Espera de Retiro por Sucursal",
  motivo: "Sin Motivo",
  sucursalOca: "CORDOBA (COA)",
  fechaEstado: "2026-09-21",
  operativa: "294051",
  cliente: "Papelera del Centro S.A.",
  fechaRemito: "2026-09-15",
  numeroRemito: 45210,
  cantidadRemitos: 1,
  incidente: "184532",
  cantidadIncidentes: 1,
  ultimaAccion: {
    tipo: "mail_cliente",
    resultado: "sin_respuesta",
    usuarioNombre: "Lucía Fernández",
    creadaEn: "2026-09-22T12:35:00Z",
  },
  conError: false,
};

const FILA_NARANJA = {
  ...FILA_ROJA,
  guia: "2610800000000210019",
  color: "naranja",
  fechaLimite: null,
  diasHabilesParaLimite: null,
  estado: "Reprogramado para nueva visita",
  motivo: "Persona Inhabilitada",
  sucursalOca: "TUCUMAN",
  cliente: "Bebidas del Sur S.A.",
  incidente: "184655",
  ultimaAccion: null,
};

const FILA_AMARILLA = {
  ...FILA_NARANJA,
  guia: "2118600000000100027",
  color: "amarillo",
  alertaAbierta: false,
  observacion: "Sin movimiento hace 4 días hábiles",
  estado: "En viaje a Centro de Distribución de Destino",
  motivo: "Sin Motivo",
  cliente: "Metalúrgica Andina S.R.L.",
};

const RESUMEN = {
  porColor: { verde: 104, amarillo: 3, naranja: 1, rojo: 1, gris: 3, cerrado: 581 },
  alertasRojas: 1,
  alertasNaranjas: 1,
  naranjasSinAccion: 1,
  limiteMasProximo: "2026-09-25",
  diasHabilesLimiteMasProximo: 1,
  operativas: ["294051", "294052"],
};

const DETALLE_NARANJA = {
  envio: {
    guia: FILA_NARANJA.guia,
    idDistribucion: 12,
    fechaRemito: "2026-09-15",
    cliente: FILA_NARANJA.cliente,
    sucursalCliente: "Casa central",
    color: "naranja",
    alerta: true,
    alertaAbierta: true,
    abierto: true,
    fechaLimite: null,
    observacion: "",
    estadoOca: {
      operativa: "294051",
      ordenRetiro: "1",
      sucursalActual: "TUCUMAN",
      fechaEstado: "2026-09-23",
      estado: "Reprogramado para nueva visita",
      idEstado: 48,
      motivo: "Persona Inhabilitada",
      cantidadPaquetes: 1,
    },
    consultadoEn: "2026-09-24T13:40:00Z",
    ultimoError: null,
    cierreAlerta: null,
  },
  diasHabilesParaLimite: null,
  remitos: [
    {
      idRemito: 1,
      numeroRemito: 45211,
      fechaRemito: "2026-09-15",
      idDistribucion: 12,
      bultos: 2,
      cliente: FILA_NARANJA.cliente,
      sucursalCliente: "Casa central",
      entregaA: "Compras",
      incidentes: [{ numero: "184655", numeroCliente: "A-1" }],
    },
  ],
  cambios: [
    {
      idEstado: 48,
      estado: "Reprogramado para nueva visita",
      motivo: "Persona Inhabilitada",
      sucursal: "TUCUMAN",
      fechaEstado: "2026-09-23",
      color: "naranja",
      observadoEn: "2026-09-23T15:00:00Z",
    },
  ],
  acciones: [],
};

const CORRIDA = {
  id: 1, origen: "programada", usuarioNombre: null, iniciadaEn: "2026-09-24T13:38:00Z",
  terminadaEn: "2026-09-24T13:40:00Z", enviosNuevos: 0, consultasOk: 120, consultasError: 0, error: null,
};

interface Mock {
  listados: URL[];
  accionBody: Record<string, unknown> | null;
  actualizarLlamado: boolean;
  actualizacion: () => unknown;
}

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

async function mockDespachados(page: Page): Promise<Mock> {
  const mock: Mock = {
    listados: [],
    accionBody: null,
    actualizarLlamado: false,
    actualizacion: () => ({ enCurso: false, iniciadaEn: null, ultimaTerminada: CORRIDA }),
  };
  await page.route(/\/api\/insumos\/despachados(\/|\?|$)/, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace(/^.*\/api\/insumos\/despachados/, "");
    if (path === "/resumen") return json(route, RESUMEN);
    if (path === "/actualizacion") return json(route, mock.actualizacion());
    if (path === "/actualizar" && request.method() === "POST") {
      mock.actualizarLlamado = true;
      return json(route, { enCurso: true }, 202);
    }
    if (path.endsWith("/acciones") && request.method() === "POST") {
      mock.accionBody = request.postDataJSON() as Record<string, unknown>;
      return json(route, { id: 9, guia: FILA_NARANJA.guia, cerroAlerta: true }, 201);
    }
    if (path === `/${FILA_NARANJA.guia}`) return json(route, DETALLE_NARANJA);
    if (path === "" || path === "/") {
      mock.listados.push(url);
      const colores = url.searchParams.get("colores");
      const filas = colores === "naranja" ? [FILA_NARANJA] : [FILA_ROJA, FILA_NARANJA, FILA_AMARILLA];
      return json(route, { items: filas, total: filas.length, page: 1, size: 25 });
    }
    return route.fallback();
  });
  return mock;
}

test.describe("Insumos › Despachados", () => {
  test("carga tarjetas y tabla con datos mockeados @smoke", async ({ page }) => {
    await mockDespachados(page);
    await page.goto("/insumos/despachados");

    await expect(page.getByRole("heading", { name: "Despachados", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: /^Visita fallida/ })).toContainText("1 sin acción registrada");
    await expect(page.getByRole("button", { name: /^En sucursal/ })).toContainText("La más próxima vence mañana (25/09)");
    await expect(page.getByRole("button", { name: /^En tránsito/ })).toContainText("107");

    await expect(page.getByRole("region", { name: /Requieren acción/ })).toHaveCount(0);
    await expect(page.getByLabel("Color")).toHaveCount(0);

    const todos = page.getByRole("region", { name: "Todos los despachos" });
    await expect(todos.getByText("vence mañana (25/09)")).toBeVisible();
    await expect(todos.getByText("Sin movimiento hace 4 días hábiles")).toBeVisible();
    await expect(todos.getByText("Mostrando")).toContainText("de 3 despachos");
  });

  test("tocar una tarjeta filtra la tabla por su color", async ({ page }) => {
    const mock = await mockDespachados(page);
    await page.goto("/insumos/despachados");

    const tarjeta = page.getByRole("button", { name: /^Visita fallida/ });
    await tarjeta.click();
    await expect(tarjeta).toHaveAttribute("aria-pressed", "true");
    await expect.poll(() => mock.listados.at(-1)?.searchParams.get("colores")).toBe("naranja");
    const todos = page.getByRole("region", { name: "Todos los despachos" });
    await expect(todos.getByText(/Filtrado por la tarjeta "Visita fallida"/)).toBeVisible();
    await expect(todos.getByText(FILA_AMARILLA.cliente)).toBeHidden();

    await tarjeta.click();
    await expect(tarjeta).toHaveAttribute("aria-pressed", "false");
  });

  test("los encabezados ordenan en el servidor (orden/direccion) y vuelven a la página 1", async ({ page }) => {
    const mock = await mockDespachados(page);
    await page.goto("/insumos/despachados");
    const ultimo = () => mock.listados.at(-1)?.searchParams;
    await expect.poll(() => ultimo()?.has("orden")).toBe(false);

    const cliente = page.getByRole("columnheader", { name: "Cliente" });
    await cliente.getByRole("button").click();
    await expect.poll(() => [ultimo()?.get("orden"), ultimo()?.get("direccion"), ultimo()?.get("page")]).toEqual(["cliente", "asc", "1"]);
    await expect(cliente).toHaveAttribute("aria-sort", "ascending");
    await cliente.getByRole("button").click();
    await expect.poll(() => ultimo()?.get("direccion")).toBe("desc");
    await expect(cliente).toHaveAttribute("aria-sort", "descending");

    await page.getByRole("columnheader", { name: "Fecha estado" }).getByRole("button").click();
    await expect.poll(() => [ultimo()?.get("orden"), ultimo()?.get("direccion")]).toEqual(["fecha_estado", "desc"]);
    await expect(cliente).toHaveAttribute("aria-sort", "none");
  });

  test("abrir el panel lateral de una guía", async ({ page }) => {
    await mockDespachados(page);
    await page.goto("/insumos/despachados");

    const todos = page.getByRole("region", { name: "Todos los despachos" });
    await todos.getByRole("cell", { name: FILA_NARANJA.guia }).click();
    const panel = page.getByRole("dialog", { name: `Guía ${FILA_NARANJA.guia}` });
    await expect(panel).toBeVisible();
    await expect(panel.getByText("Cambios de estado observados")).toBeVisible();
    await expect(panel.getByRole("button", { name: "Cerrar alerta" })).toBeDisabled();
    await expect(panel.getByText("Para cerrar la alerta registrá al menos una acción.")).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(panel).toBeHidden();
  });

  test("registrar acción hace POST camelCase con cerrarAlerta", async ({ page }) => {
    const mock = await mockDespachados(page);
    await page.goto("/insumos/despachados");

    const todos = page.getByRole("region", { name: "Todos los despachos" });
    await todos.getByRole("cell", { name: FILA_NARANJA.guia }).click();
    await page
      .getByRole("dialog", { name: `Guía ${FILA_NARANJA.guia}` })
      .getByRole("button", { name: "Registrar acción" })
      .click();
    const dialog = page.getByRole("dialog", { name: "Registrar acción" });
    await expect(dialog).toBeVisible();

    await dialog.getByRole("button", { name: "Guardar acción" }).click();
    await expect(dialog.getByText("Elegí el tipo de acción.")).toBeVisible();

    await dialog.getByLabel("Llamado al cliente").check();
    await dialog.getByLabel("Detalle").fill("No atendieron; se dejó mensaje en recepción.");
    await dialog.getByRole("radio", { name: "Resuelto" }).click();
    await dialog.getByLabel("Cerrar la alerta al guardar esta acción").check();
    await dialog.getByRole("button", { name: "Guardar acción" }).click();

    await expect(dialog).toBeHidden();
    expect(mock.accionBody).toEqual({
      tipo: "llamado_cliente",
      detalle: "No atendieron; se dejó mensaje en recepción.",
      resultado: "resuelto",
      cerrarAlerta: true,
    });
    await expect(page.getByText("Acción registrada y alerta cerrada")).toBeVisible();
  });

  test("Actualizar ahora lanza la corrida (202) y la sigue por polling", async ({ page }) => {
    const mock = await mockDespachados(page);
    let polls = 0;
    mock.actualizacion = () => {
      if (!mock.actualizarLlamado) return { enCurso: false, iniciadaEn: null, ultimaTerminada: CORRIDA };
      polls += 1;
      if (polls < 2) return { enCurso: true, iniciadaEn: "2026-09-24T14:00:00Z", ultimaTerminada: CORRIDA };
      return {
        enCurso: false,
        iniciadaEn: null,
        ultimaTerminada: { ...CORRIDA, id: 2, origen: "manual", terminadaEn: "2026-09-24T14:05:00Z", consultasOk: 118 },
      };
    };
    await page.goto("/insumos/despachados");

    await expect(page.getByText("Última consulta a OCA:")).toContainText("10:40");
    await page.getByRole("button", { name: "Actualizar ahora" }).click();
    await expect(page.getByRole("button", { name: "Actualizando…" })).toBeDisabled();
    await expect.poll(() => mock.actualizarLlamado).toBe(true);

    await expect(page.getByText("Estados actualizados desde OCA (118 consultadas)")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Última consulta a OCA:")).toContainText("11:05");
    await expect(page.getByRole("button", { name: "Actualizar ahora" })).toBeEnabled();
  });
});
