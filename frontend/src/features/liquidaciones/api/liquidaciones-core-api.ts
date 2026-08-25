import { httpClient } from "@/services/http-client";
import type {
  Alerta,
  EstadoAlerta,
  EstadoLiquidacion,
  EstadoObservacion,
  ImportarLiquidacionResult,
  Liquidacion,
  LiquidacionDetalle,
  LiquidacionPage,
  Observacion,
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
      .then((p) => p.items),

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

  delete: (id: string) => httpClient.delete<void>(`/api/liquidaciones/${id}`),

  updateEstado: (id: string, estado: EstadoLiquidacion) =>
    httpClient.patch<Liquidacion>(`/api/liquidaciones/${id}/estado`, { estado }),

  updateExtra: (id: string, body: { conceptoExtra: string | null; montoExtra: number | null }) =>
    httpClient.patch<Liquidacion>(`/api/liquidaciones/${id}/extra`, body),

  updateEstadoObservacion: (liquidacionId: string, observacionId: string, estado: EstadoObservacion) =>
    httpClient.patch<Observacion>(
      `/api/liquidaciones/${liquidacionId}/observaciones/${observacionId}/estado`,
      { estado },
    ),

  updateEstadoAlerta: (
    liquidacionId: string,
    alertaId: string,
    body: { estado: EstadoAlerta; justificacion?: string },
  ) =>
    httpClient.patch<Alerta>(
      `/api/liquidaciones/${liquidacionId}/alertas/${alertaId}/estado`,
      body,
    ),

  aprobar: (id: string) =>
    httpClient.post<Liquidacion>(`/api/liquidaciones/${id}/aprobar`),

  observar: (id: string) =>
    httpClient.post<Liquidacion>(`/api/liquidaciones/${id}/observar`),

  anular: (id: string) =>
    httpClient.post<void>(`/api/liquidaciones/${id}/anular`),

  reconciliar: (id: string) =>
    httpClient.post<void>(`/api/liquidaciones/${id}/reconciliar`),

  reanalyze: (id: string) =>
    httpClient.post<{ totalIncidentes: number; totalAlertas: number; totalObservaciones: number }>(
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
