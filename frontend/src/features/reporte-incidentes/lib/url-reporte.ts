/** El estado del dashboard vive en la URL (como el legacy): cliente, mes
 * final, cantidad de meses y los tres filtros transversales. */

import type { DimensionFiltro, Filtros, PedidoReporte } from "../types/reporte";
import { acotarMeses } from "./periodos";

export const RUTA_SELECCION = "/reporte-incidentes";
export const RUTA_REPORTE = "/reporte-incidentes/reporte";

export const FILTROS_VACIOS: Filtros = { sucursal: "", categoria: "", subcategoria: "" };
const DIMENSIONES: DimensionFiltro[] = ["sucursal", "categoria", "subcategoria"];

export interface EstadoReporte {
  pedido: PedidoReporte;
  filtros: Filtros;
}

export function leerEstado(params: URLSearchParams): EstadoReporte | null {
  const empresaId = params.get("empresa");
  if (!empresaId) return null;
  const filtros = { ...FILTROS_VACIOS };
  for (const d of DIMENSIONES) filtros[d] = params.get(d) ?? "";
  return {
    pedido: {
      empresaId,
      periodo: params.get("periodo") ?? "",
      meses: acotarMeses(Number(params.get("meses") ?? "1")),
    },
    filtros,
  };
}

export function urlReporte(pedido: PedidoReporte, filtros: Filtros = FILTROS_VACIOS): string {
  const params = new URLSearchParams({
    empresa: pedido.empresaId,
    periodo: pedido.periodo,
    meses: String(pedido.meses),
  });
  for (const d of DIMENSIONES) if (filtros[d]) params.set(d, filtros[d]);
  return `${RUTA_REPORTE}?${params}`;
}

/** Clickear un valor ya activo lo apaga; si no, lo activa. */
export function alternarFiltro(filtros: Filtros, dimension: DimensionFiltro, valor: string): Filtros {
  return { ...filtros, [dimension]: filtros[dimension] === valor ? "" : valor };
}
