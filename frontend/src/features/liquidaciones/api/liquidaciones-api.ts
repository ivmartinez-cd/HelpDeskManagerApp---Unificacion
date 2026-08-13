import { httpClient } from "@/services/http-client";
import type {
  EstadoLiquidacion,
  EstadoObservacion,
  ImportarLiquidacionResult,
  Liquidacion,
  LiquidacionDetalle,
  LiquidacionPage,
  Observacion,
  PrestadorLiquidacion,
  Spst,
  TablaKm,
  Tarifario,
} from "../types/liquidaciones";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

interface TarifarioBody {
  prestadorId: string;
  tipoServicio: string;
  zona?: string;
  costoServicio: number;
  costoKm: number;
  vigenciaDesde: string;
  vigenciaHasta?: string;
}

interface TablaKmBody {
  prestadorId: string;
  spstId?: string;
  empresaNombre: string;
  sucursalNombre: string;
  observaciones?: string;
  domicilioCliente?: string;
  localidadCliente?: string;
  provinciaCliente?: string;
  kmsRecorrido: number;
  umbralViatico?: number;
  aplicaViatico?: boolean;
  kmsAFacturar?: number;
  urlMaps?: string;
}

export const liquidacionesApi = {
  // ── Liquidaciones ──────────────────────────────────────────────────────────
  listPrestadores: (soloActivos = true) =>
    httpClient
      .get<Page<PrestadorLiquidacion>>(
        `/api/liquidaciones/prestadores?soloActivos=${soloActivos}`,
      )
      .then((p) => p.items),

  list: (params?: { prestadorId?: string; page?: number; size?: number }) => {
    const qs = new URLSearchParams();
    if (params?.prestadorId) qs.set("prestadorId", params.prestadorId);
    qs.set("page", String(params?.page ?? 1));
    qs.set("size", String(params?.size ?? 50));
    return httpClient.get<LiquidacionPage>(`/api/liquidaciones?${qs}`);
  },

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

  updateEstadoObservacion: (liquidacionId: string, observacionId: string, estado: EstadoObservacion) =>
    httpClient.patch<Observacion>(
      `/api/liquidaciones/${liquidacionId}/observaciones/${observacionId}/estado`,
      { estado },
    ),

  reanalyze: (id: string) =>
    httpClient.post<{ totalIncidentes: number; totalAlertas: number; totalObservaciones: number }>(
      `/api/liquidaciones/${id}/reanalyze`,
    ),

  // ── Config: Prestadores ───────────────────────────────────────────────────
  createPrestador: (body: { nombreCorto: string; nombre: string; cuit?: string; region?: string }) =>
    httpClient.post<PrestadorLiquidacion>("/api/liquidaciones/prestadores", body),

  updatePrestador: (id: string, body: { nombreCorto: string; nombre: string; cuit?: string; region?: string }) =>
    httpClient.patch<PrestadorLiquidacion>(`/api/liquidaciones/prestadores/${id}`, body),

  togglePrestadorActivo: (id: string, activo: boolean) =>
    httpClient.patch<PrestadorLiquidacion>(`/api/liquidaciones/prestadores/${id}/activo`, { activo }),

  exportPrestadoresCsv: () =>
    httpClient.downloadFile("/api/liquidaciones/prestadores/export", "prestadores.csv"),

  importPrestadoresCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return httpClient.postForm<{ creados: number }>("/api/liquidaciones/prestadores/import", fd);
  },

  // ── Config: SPSTs ─────────────────────────────────────────────────────────
  listSpsts: (params?: { prestadorId?: string; soloActivos?: boolean }) => {
    const qs = new URLSearchParams();
    if (params?.prestadorId) qs.set("prestadorId", params.prestadorId);
    if (params?.soloActivos) qs.set("soloActivos", "true");
    return httpClient
      .get<Page<Spst>>(`/api/liquidaciones/spsts?${qs}`)
      .then((p) => p.items);
  },

  createSpst: (body: { prestadorId: string; nombre: string; domicilio?: string; localidad?: string; provincia?: string; zona?: string }) =>
    httpClient.post<Spst>("/api/liquidaciones/spsts", body),

  updateSpst: (id: string, body: { prestadorId: string; nombre: string; domicilio?: string; localidad?: string; provincia?: string; zona?: string }) =>
    httpClient.patch<Spst>(`/api/liquidaciones/spsts/${id}`, body),

  toggleSpstActivo: (id: string, activo: boolean) =>
    httpClient.patch<Spst>(`/api/liquidaciones/spsts/${id}/activo`, { activo }),

  exportSpstsCsv: () =>
    httpClient.downloadFile("/api/liquidaciones/spsts/export", "spsts.csv"),

  importSpstsCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return httpClient.postForm<{ creados: number }>("/api/liquidaciones/spsts/import", fd);
  },

  // ── Config: Tarifarios ────────────────────────────────────────────────────
  listTarifarios: (prestadorId?: string) => {
    const qs = prestadorId ? `?prestadorId=${prestadorId}` : "";
    return httpClient
      .get<Page<Tarifario>>(`/api/liquidaciones/tarifarios${qs}`)
      .then((p) => p.items);
  },

  createTarifario: (body: TarifarioBody) =>
    httpClient.post<Tarifario>("/api/liquidaciones/tarifarios", body),

  updateTarifario: (id: string, body: TarifarioBody) =>
    httpClient.patch<Tarifario>(`/api/liquidaciones/tarifarios/${id}`, body),

  deleteTarifario: (id: string) =>
    httpClient.delete<void>(`/api/liquidaciones/tarifarios/${id}`),

  exportTarifariosCsv: () =>
    httpClient.downloadFile("/api/liquidaciones/tarifarios/export", "tarifarios.csv"),

  importTarifariosCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return httpClient.postForm<{ creados: number }>("/api/liquidaciones/tarifarios/import", fd);
  },

  // ── Config: Tabla KM ──────────────────────────────────────────────────────
  listTablaKm: (params?: { prestadorId?: string; q?: string }) => {
    const qs = new URLSearchParams();
    if (params?.prestadorId) qs.set("prestadorId", params.prestadorId);
    if (params?.q) qs.set("q", params.q);
    return httpClient
      .get<Page<TablaKm>>(`/api/liquidaciones/tabla-km?${qs}`)
      .then((p) => p.items);
  },

  createTablaKm: (body: TablaKmBody) =>
    httpClient.post<TablaKm>("/api/liquidaciones/tabla-km", body),

  updateTablaKm: (id: string, body: TablaKmBody) =>
    httpClient.patch<TablaKm>(`/api/liquidaciones/tabla-km/${id}`, body),

  deleteTablaKm: (id: string) =>
    httpClient.delete<void>(`/api/liquidaciones/tabla-km/${id}`),

  exportTablaKmCsv: () =>
    httpClient.downloadFile("/api/liquidaciones/tabla-km/export", "tabla_km.csv"),

  importTablaKmCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return httpClient.postForm<{ creados: number }>("/api/liquidaciones/tabla-km/import", fd);
  },
};
