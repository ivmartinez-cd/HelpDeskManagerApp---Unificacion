import type { Page, Route } from "@playwright/test";
import { expect, test } from "./fixtures";

// ── Insumos › Despachados › Reclamar en OCA ──
// El formulario real es un embed de Bitrix24 (formulario público de OCA): acá
// se bloquea su carga y se verifica el respaldo (link a OCA + comentario para
// copiar). Nunca se toca Bitrix ni OCA de verdad.

const GUIA = "2610800000000210019";
const CLIENTE = "Bebidas del Sur S.A.";
const COMENTARIO = [
  `Reclamo por el envío ${GUIA}.`,
  "Estado en OCA: Reprogramado para nueva visita (motivo: Persona Inhabilitada), desde el 23/09/2026, sucursal TUCUMAN.",
  "Cliente: Bebidas del Sur S.A. (Casa central).",
  "Incidente: 184655.",
  "Remito: 45211 (2 bultos).",
  "Pedimos revisar el envío y confirmar cómo sigue la entrega.",
].join("\n");

const FILA = {
  guia: GUIA, color: "naranja", alertaAbierta: true, observacion: "", fechaLimite: null,
  diasHabilesParaLimite: null, estado: "Reprogramado para nueva visita", motivo: "Persona Inhabilitada",
  sucursalOca: "TUCUMAN", fechaEstado: "2026-09-23", operativa: "434324", cliente: CLIENTE,
  fechaRemito: "2026-09-15", numeroRemito: 45211, cantidadRemitos: 1, incidente: "184655",
  cantidadIncidentes: 1, ultimaAccion: null, conError: false,
};

const DETALLE = {
  envio: {
    guia: GUIA, idDistribucion: 3, fechaRemito: "2026-09-15", cliente: CLIENTE, sucursalCliente: "Casa central",
    color: "naranja", alerta: true, alertaAbierta: true, abierto: true, fechaLimite: null, observacion: "",
    estadoOca: {
      operativa: "434324", ordenRetiro: "1", sucursalActual: "TUCUMAN", fechaEstado: "2026-09-23",
      estado: "Reprogramado para nueva visita", idEstado: 48, motivo: "Persona Inhabilitada", cantidadPaquetes: 1,
    },
    consultadoEn: "2026-09-24T13:40:00Z", ultimoError: null, cierreAlerta: null,
  },
  diasHabilesParaLimite: null,
  remitos: [],
  cambios: [],
  acciones: [],
};

const RECLAMO = {
  guia: GUIA,
  operativa: "434324",
  contacto: {
    nombre: "Canal Directo", apellido: "Soluciones de Impresión", empresa: "Canal Directo Soluciones de Impresión",
    email: "ocacdsisa@canaldirecto.com.ar", cuit: "30709381101", telefono: "",
  },
  comentario: COMENTARIO,
};

const RESUMEN = {
  porColor: { verde: 0, amarillo: 0, naranja: 1, rojo: 0, gris: 0, cerrado: 0 },
  alertasRojas: 0, alertasNaranjas: 1, naranjasSinAccion: 1, limiteMasProximo: null,
  diasHabilesLimiteMasProximo: null, operativas: ["434324"],
};

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

async function mockPantalla(page: Page): Promise<{ reclamosPedidos: number }> {
  const mock = { reclamosPedidos: 0 };
  // Bitrix24 bloqueado: el formulario de OCA nunca carga en los tests.
  await page.route(/bitrix24\./, (route) => route.abort());
  await page.route(/\/api\/insumos\/despachados(\/|\?|$)/, async (route) => {
    const path = new URL(route.request().url()).pathname.replace(/^.*\/api\/insumos\/despachados/, "");
    if (path === "/resumen") return json(route, RESUMEN);
    if (path === "/actualizacion") return json(route, { enCurso: false, iniciadaEn: null, ultimaTerminada: null });
    if (path === `/${GUIA}/reclamo-oca`) {
      mock.reclamosPedidos += 1;
      return json(route, RECLAMO);
    }
    if (path === `/${GUIA}`) return json(route, DETALLE);
    if (path === "" || path === "/") return json(route, { items: [FILA], total: 1, page: 1, size: 25 });
    return route.fallback();
  });
  return mock;
}

test.describe("Insumos › Despachados › Reclamar en OCA", () => {
  test("sin el formulario de OCA muestra el respaldo y al cerrar ofrece registrar la acción", async ({ page }) => {
    const mock = await mockPantalla(page);
    await page.goto("/insumos/despachados");

    await page.getByRole("region", { name: "Todos los despachos" }).getByRole("cell", { name: GUIA }).click();
    await page.getByRole("dialog", { name: `Guía ${GUIA}` }).getByRole("button", { name: "Reclamar en OCA" }).click();

    const modal = page.getByRole("dialog", { name: "Reclamar en OCA" });
    await expect(modal).toBeVisible();
    // ≥1 y no 1: la suite corre sobre `next dev`, donde StrictMode monta el modal dos
    // veces y la primera respuesta se descarta; en producción es un solo pedido.
    await expect.poll(() => mock.reclamosPedidos).toBeGreaterThanOrEqual(1);
    await expect(modal.getByText("No se pudo cargar el formulario de OCA acá.")).toBeVisible({ timeout: 20_000 });
    await expect(modal.getByRole("link", { name: "Abrir el formulario de OCA" })).toHaveAttribute(
      "href",
      "https://int.oca.com.ar/grandescuentas/",
    );
    await expect(modal.getByTestId("oca-comentario")).toHaveText(COMENTARIO);
    await expect(modal.getByRole("button", { name: "Copiar comentario" })).toBeVisible();

    await modal.getByRole("button", { name: "Cerrar modal" }).click();
    await expect(modal).toBeHidden();
    await page.locator("[data-sonner-toast]").getByRole("button", { name: "Registrar acción" }).click();

    const registrar = page.getByRole("dialog", { name: "Registrar acción" });
    await expect(registrar).toBeVisible();
    await expect(registrar.getByLabel("Reclamo a OCA")).toBeChecked();
    await expect(registrar.getByLabel("Detalle")).toHaveValue(COMENTARIO);
  });
});
