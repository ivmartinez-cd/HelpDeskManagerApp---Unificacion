import { httpClient } from "@/services/http-client";
import type {
  Alerta,
  EstadoAlerta,
  EstadoLiquidacion,
  ImportarLiquidacionResult,
  Liquidacion,
  LiquidacionDetalle,
  LiquidacionPage,
  PrestadorLiquidacion,
} from "../types/liquidaciones";
import { fetchCatalogoCompleto, type Page } from "./_shared";

export const liquidacionesCoreApi = {
  getResumen: () =>
    httpClient.get<{
      pendientes: number;
      porPrestador: { nombreCorto: string; count: number }[];
    }>("/api/liquidaciones/resumen"),

  listPrestadores: (soloActivos = true) =>
    httpClient
      .get<Page<PrestadorLiquidacion>>(
        `/api/liquidaciones/prestadores?soloActivos=${soloActivos}`,
      )
      // Los combos muestran nombreCorto, que no correlaciona alfabéticamente
      // con el `nombre` por el que ordena el backend (ej. "Rosario" -> SUPERNOVA).
      .then((p) => [...p.items].sort((a, b) => a.nombreCorto.localeCompare(b.nombreCorto, "es"))),

  list: (params?: {
    prestadorId?: string;
    estado?: string;
    periodo?: string;
    anio?: number;
    page?: number;
    size?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.prestadorId) qs.set("prestadorId", params.prestadorId);
    if (params?.estado) qs.set("estado", params.estado);
    if (params?.periodo) qs.set("periodo", params.periodo);
    if (params?.anio) qs.set("anio", String(params.anio));
    qs.set("page", String(params?.page ?? 1));
    qs.set("size", String(params?.size ?? 50));
    return httpClient.get<LiquidacionPage>(`/api/liquidaciones?${qs}`);
  },

  listAll: () =>
    fetchCatalogoCompleto<Liquidacion>("/api/liquidaciones", new URLSearchParams()),

  listPeriodos: () =>
    httpClient.get<Page<string>>("/api/liquidaciones/periodos").then((p) => p.items),

  get: (id: string) => httpClient.get<LiquidacionDetalle>(`/api/liquidaciones/${id}`),

  importar: (prestadorId: string, file: File) => {
    const fd = new FormData();
    fd.append("prestadorId", prestadorId);
    fd.append("file", file);
    return httpClient.postForm<ImportarLiquidacionResult>("/api/liquidaciones/importar", fd);
  },

  // `forzar` es la única forma de borrar localmente una liquidación vinculada
  // a Canal Directo (el backend rechaza con 409 si no) — solo debería pasarlo
  // el link "Eliminar solo localmente" tras un `/anular` que ya falló.
  delete: (id: string, forzar = false) =>
    httpClient.delete<void>(`/api/liquidaciones/${id}${forzar ? "?forzar=true" : ""}`),

  updateEstado: (id: string, estado: EstadoLiquidacion) =>
    httpClient.patch<Liquidacion>(`/api/liquidaciones/${id}/estado`, { estado }),

  updateExtra: (id: string, body: { conceptoExtra: string | null; montoExtra: number | null }) =>
    httpClient.patch<Liquidacion>(`/api/liquidaciones/${id}/extra`, body),

  updateEstadoAlerta: (
    liquidacionId: string,
    alertaId: string,
    body: { estado: EstadoAlerta; justificacion?: string; incidenteRelacionadoId?: string | null },
  ) =>
    httpClient.patch<Alerta>(
      `/api/liquidaciones/${liquidacionId}/alertas/${alertaId}/estado`,
      body,
    ),

  /** Mismo estado y motivo para varias alertas (tilde múltiple en el detalle). */
  updateEstadoAlertasLote: (
    liquidacionId: string,
    body: { alertaIds: string[]; estado: EstadoAlerta; justificacion?: string },
  ) =>
    httpClient.patch<{ actualizadas: number }>(
      `/api/liquidaciones/${liquidacionId}/alertas/estado`,
      body,
    ),

  aprobar: (id: string) =>
    httpClient.post<Liquidacion>(`/api/liquidaciones/${id}/aprobar`),

  observar: (id: string) =>
    httpClient.post<Liquidacion>(`/api/liquidaciones/${id}/observar`),

  recibir: (id: string) =>
    httpClient.post<Liquidacion>(`/api/liquidaciones/${id}/recibir`),

  anular: (id: string) =>
    httpClient.post<void>(`/api/liquidaciones/${id}/anular`),

  reconciliar: (id: string) =>
    httpClient.post<void>(`/api/liquidaciones/${id}/reconciliar`),

  reanalyze: (id: string) =>
    httpClient.post<{ totalIncidentes: number; totalAlertas: number }>(
      `/api/liquidaciones/${id}/reanalyze`,
    ),

  sincronizar: () =>
    httpClient.post<{
      creadas: number;
      yaExistentes: number;
      sinPrestador: number;
      fallidas: number;
      anuladas: number;
      reconciliadas: number;
      estadosActualizados: number;
      periodosActualizados: number;
      extrasActualizados: number;
      facturasActualizadas: number;
    }>("/api/liquidaciones/sincronizar"),
};
