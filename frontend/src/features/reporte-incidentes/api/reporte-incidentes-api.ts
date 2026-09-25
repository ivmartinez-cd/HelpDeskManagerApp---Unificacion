import { httpClient } from "@/services/http-client";
import type { Page } from "@/shared/types/pagination";
import type {
  CampoOrden,
  CategoriaDetalle,
  Empresa,
  Filtros,
  Incidente,
  PedidoReporte,
  Reporte,
  ResultadoIA,
} from "../types/reporte";

const BASE = "/api/reporte-incidentes";

function pedidoParams(pedido: PedidoReporte, filtros?: Partial<Filtros>): URLSearchParams {
  const params = new URLSearchParams({
    empresa_id: pedido.empresaId,
    periodo: pedido.periodo,
    meses: String(pedido.meses),
  });
  for (const [clave, valor] of Object.entries(filtros ?? {})) {
    if (valor) params.set(clave, valor);
  }
  return params;
}

export interface ConsultaIncidentes {
  q?: string;
  orden?: CampoOrden | null;
  direccion?: "asc" | "desc";
  page?: number;
  size?: number;
}

export const reporteIncidentesApi = {
  listEmpresas: (q: string, size = 50) =>
    httpClient.get<Page<Empresa>>(
      `${BASE}/empresas?${new URLSearchParams({ q, size: String(size) })}`,
    ),

  getReporte: (pedido: PedidoReporte, filtros: Filtros) =>
    httpClient.get<Reporte>(`${BASE}/reporte?${pedidoParams(pedido, filtros)}`),

  listIncidentes: (pedido: PedidoReporte, filtros: Filtros, consulta: ConsultaIncidentes) => {
    const params = pedidoParams(pedido, filtros);
    if (consulta.q) params.set("q", consulta.q);
    if (consulta.orden) params.set("orden", consulta.orden);
    if (consulta.direccion) params.set("direccion", consulta.direccion);
    params.set("page", String(consulta.page ?? 1));
    params.set("size", String(consulta.size ?? 50));
    return httpClient.get<Page<Incidente>>(`${BASE}/incidentes?${params}`);
  },

  listPendientes: (pedido: PedidoReporte, page = 1, size = 50) => {
    const params = pedidoParams(pedido);
    params.set("page", String(page));
    params.set("size", String(size));
    return httpClient.get<Page<Incidente>>(`${BASE}/pendientes?${params}`);
  },

  tipificar: (pedido: PedidoReporte) =>
    httpClient.post<ResultadoIA>(`${BASE}/tipificar?${pedidoParams(pedido)}`),

  corregirTipificacion: (
    incidente: Pick<Incidente, "descripcion" | "causa" | "solucion">,
    categoria: string,
    subcategoria: string,
  ) =>
    httpClient.put<void>(`${BASE}/tipificacion`, {
      descripcion: incidente.descripcion,
      causa: incidente.causa,
      solucion: incidente.solucion,
      categoria,
      subcategoria,
    }),

  listCategorias: () => httpClient.get<Page<CategoriaDetalle>>(`${BASE}/categorias?size=200`),

  crearCategoria: (categoria: CategoriaDetalle) =>
    httpClient.post<void>(`${BASE}/categorias`, categoria),

  editarCategoria: (nombreAnterior: string, categoria: CategoriaDetalle) =>
    httpClient.put<void>(`${BASE}/categorias/${encodeURIComponent(nombreAnterior)}`, categoria),

  eliminarCategoria: (nombre: string) =>
    httpClient.delete<void>(`${BASE}/categorias/${encodeURIComponent(nombre)}`),
};
