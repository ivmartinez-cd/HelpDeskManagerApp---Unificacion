import { httpClient } from "@/services/http-client";
import type {
  EstadoLiquidacion,
  EstadoObservacion,
  ImportarLiquidacionResult,
  ImportExcelMaestroResult,
  Liquidacion,
  LiquidacionDetalle,
  LiquidacionPage,
  Observacion,
  PrestadorLiquidacion,
  PropuestasVinculo,
  Spst,
  SucursalSiges,
  SyncSigesResult,
  SyncTarifariosResult,
  TablaKm,
  Tarifario,
  ZonasSiges,
} from "../types/liquidaciones";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

// Tope de `size` que acepta el backend (Query le=1000 en config_routers).
const CATALOGO_SIZE_MAX = 1000;

// Los catálogos por prestador pueden superar incluso el tope de una página
// (INFOMAC: 960 tarifas y creciendo) — se piden páginas hasta cubrir `total`
// en vez de truncar en silencio al default de 500.
async function fetchCatalogoCompleto<T>(path: string, params: URLSearchParams): Promise<T[]> {
  params.set("size", String(CATALOGO_SIZE_MAX));
  params.set("page", "1");
  const primera = await httpClient.get<Page<T>>(`${path}?${params}`);
  const items = [...primera.items];
  for (let page = 2; items.length < primera.total; page++) {
    params.set("page", String(page));
    const siguiente = await httpClient.get<Page<T>>(`${path}?${params}`);
    if (siguiente.items.length === 0) break;
    items.push(...siguiente.items);
  }
  return items;
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

  list: (params?: {
    prestadorId?: string;
    estado?: string;
    periodo?: string;
    page?: number;
    size?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.prestadorId) qs.set("prestadorId", params.prestadorId);
    if (params?.estado) qs.set("estado", params.estado);
    if (params?.periodo) qs.set("periodo", params.periodo);
    qs.set("page", String(params?.page ?? 1));
    qs.set("size", String(params?.size ?? 50));
    return httpClient.get<LiquidacionPage>(`/api/liquidaciones?${qs}`);
  },

  listAll: () =>
    fetchCatalogoCompleto<Liquidacion>("/api/liquidaciones", new URLSearchParams()),

  listPeriodos: () =>
    httpClient.get<string[]>("/api/liquidaciones/periodos"),

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

  deletePrestador: (id: string) =>
    httpClient.delete<void>(`/api/liquidaciones/prestadores/${id}`),

  exportPrestadoresCsv: () =>
    httpClient.downloadFile("/api/liquidaciones/prestadores/export", "prestadores.csv"),

  importPrestadoresCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return httpClient.postForm<{ creados: number }>("/api/liquidaciones/prestadores/import", fd);
  },

  importExcelMaestro: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return httpClient.postForm<ImportExcelMaestroResult>(
      "/api/liquidaciones/prestadores/importar-excel",
      fd,
    );
  },

  // ── Vínculo y sync contra Siges (ADR-014) ─────────────────────────────────
  getSigesPropuestas: () =>
    httpClient.get<PropuestasVinculo>("/api/liquidaciones/siges/propuestas"),

  syncSiges: (dryRun: boolean) =>
    httpClient.post<SyncSigesResult>(`/api/liquidaciones/siges/sync?dryRun=${dryRun}`),

  vincularPrestadorSiges: (id: string, sigesEmpresaId: number | null) =>
    httpClient.put<PrestadorLiquidacion>(`/api/liquidaciones/prestadores/${id}/siges-vinculo`, {
      sigesEmpresaId,
    }),

  vincularSpstSiges: (id: string, sigesEmpresaId: number | null) =>
    httpClient.put<Spst>(`/api/liquidaciones/spsts/${id}/siges-vinculo`, { sigesEmpresaId }),

  getSigesZonas: () => httpClient.get<ZonasSiges>("/api/liquidaciones/siges/zonas"),

  mapearZonaSiges: (body: {
    prestadorId: string;
    descripcionSiges: string;
    zonaLocal: string | null;
  }) => httpClient.put<{ id: string }>("/api/liquidaciones/siges/zonas", body),

  syncTarifariosSiges: (dryRun: boolean) =>
    httpClient.post<SyncTarifariosResult>(
      `/api/liquidaciones/siges/sync-tarifarios?dryRun=${dryRun}`,
    ),

  buscarSucursalesSiges: (prestadorId: string, q: string) => {
    const qs = new URLSearchParams({ prestadorId, q, size: "200" });
    return httpClient.get<Page<SucursalSiges>>(`/api/liquidaciones/siges/sucursales?${qs}`);
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

  deleteSpst: (id: string) =>
    httpClient.delete<void>(`/api/liquidaciones/spsts/${id}`),

  exportSpstsCsv: () =>
    httpClient.downloadFile("/api/liquidaciones/spsts/export", "spsts.csv"),

  importSpstsCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return httpClient.postForm<{ creados: number }>("/api/liquidaciones/spsts/import", fd);
  },

  // ── Config: Tarifarios ────────────────────────────────────────────────────
  listTarifarios: (prestadorId?: string) => {
    const qs = new URLSearchParams();
    if (prestadorId) qs.set("prestadorId", prestadorId);
    return fetchCatalogoCompleto<Tarifario>("/api/liquidaciones/tarifarios", qs);
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
    return fetchCatalogoCompleto<TablaKm>("/api/liquidaciones/tabla-km", qs);
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
