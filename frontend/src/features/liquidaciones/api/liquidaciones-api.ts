import { httpClient } from "@/services/http-client";
import type {
  AplicarDistanciasResult,
  AuditarPinesResult,
  CalculoKmPreview,
  EstadoLiquidacion,
  GeocodeCandidato,
  GeocodificarResultado,
  PinSospechoso,
  SucursalCoordenadas,
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
  SucursalPropia,
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
  getResumen: () =>
    httpClient.get<{ pendientes: number }>("/api/liquidaciones/resumen"),

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

  aprobar: (id: string) =>
    httpClient.post<Liquidacion>(`/api/liquidaciones/${id}/aprobar`),

  observar: (id: string) =>
    httpClient.post<Liquidacion>(`/api/liquidaciones/${id}/observar`),

  anular: (id: string) =>
    httpClient.post<void>(`/api/liquidaciones/${id}/anular`),

  reanalyze: (id: string) =>
    httpClient.post<{ totalIncidentes: number; totalAlertas: number; totalObservaciones: number }>(
      `/api/liquidaciones/${id}/reanalyze`,
    ),

  sincronizar: () =>
    httpClient.post<{ creadas: number; yaExistentes: number; sinPrestador: number; fallidas: number; anuladas: number }>(
      "/api/liquidaciones/sincronizar",
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

  listSucursalesPropiasPrestatdor: (prestadorId: string) =>
    httpClient.get<SucursalPropia[]>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/sucursales-propia`,
    ),

  vincularBaseSucursal: (prestadorId: string, sigesBaseSucursalId: number | null) =>
    httpClient.patch<PrestadorLiquidacion>(
      `/api/liquidaciones/prestadores/${prestadorId}/base-sucursal`,
      { sigesBaseSucursalId },
    ),

  vincularBaseSucursalSpst: (spstId: string, sigesBaseSucursalId: number | null) =>
    httpClient.put<Spst>(
      `/api/liquidaciones/spsts/${spstId}/siges-base-sucursal`,
      { sigesBaseSucursalId },
    ),

  // ── Geolocalización / distancias (two-step) ───────────────────────────────
  previewCalcularDistancias: (prestadorId: string) =>
    httpClient.post<CalculoKmPreview>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/calcular-distancias/preview`,
    ),

  aplicarCalcularDistancias: (prestadorId: string, previewId: string) =>
    httpClient.post<AplicarDistanciasResult>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/calcular-distancias/aplicar`,
      { previewId },
    ),

  geocodificarFaltantes: (prestadorId: string) =>
    httpClient.post<GeocodificarResultado>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/geocodificar-faltantes`,
    ),

  listCoordenadas: (prestadorId: string) =>
    fetchCatalogoCompleto<SucursalCoordenadas>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/coordenadas`,
      new URLSearchParams(),
    ),

  resolverCoordenadas: (
    prestadorId: string,
    sigesSucursalId: number,
    body: { candidatoIdx?: number; latitud?: number; longitud?: number },
  ) =>
    httpClient.put<SucursalCoordenadas>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/coordenadas/${sigesSucursalId}`,
      body,
    ),

  listPinesSospechosos: (prestadorId: string) =>
    fetchCatalogoCompleto<PinSospechoso>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/pines-sospechosos`,
      new URLSearchParams(),
    ),

  auditarPines: (prestadorId: string) =>
    httpClient.post<AuditarPinesResult>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/auditar-pines`,
    ),

  corregirPin: (prestadorId: string, sigesSucursalId: number) =>
    httpClient.post<void>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/sucursal/${sigesSucursalId}/corregir-pin`,
    ),

  listCuadriculas: (prestadorId: string) =>
    httpClient.get<{ cuadricula: string; sigesBaseSucursalId: number | null }[]>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/cuadriculas`,
    ),

  mapearCuadricula: (prestadorId: string, cuadricula: string, sigesBaseSucursalId: number) =>
    httpClient.put<{ id: string; prestadorId: string; cuadricula: string; sigesBaseSucursalId: number }>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/cuadriculas/${encodeURIComponent(cuadricula)}`,
      { sigesBaseSucursalId },
    ),

  eliminarMapeoCuadricula: (prestadorId: string, cuadricula: string) =>
    httpClient.delete<void>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/cuadriculas/${encodeURIComponent(cuadricula)}`,
    ),

  refrescarDatosSucursales: (prestadorId: string) =>
    httpClient.post<{
      actualizadas: number;
      sinCambios: number;
      noEncontradas: number;
      cambios: { sucursalNombre: string; empresaNombre: string; domicilioAntes: string | null; domicilioDespues: string | null }[];
      noEncontradasDetalle: { empresaNombre: string; sucursalNombre: string }[];
    }>(`/api/liquidaciones/siges/prestador/${prestadorId}/refrescar-datos-sucursales`),

  buscarLugarFila: (tablaKmId: string) =>
    httpClient.post<{ candidatos: GeocodeCandidato[] }>(
      `/api/liquidaciones/tabla-km/${tablaKmId}/buscar-lugar`,
    ),

  resolverCoordenadasFila: (
    tablaKmId: string,
    body: { candidatoIdx?: number; latitud?: number; longitud?: number },
  ) =>
    httpClient.put<TablaKm>(`/api/liquidaciones/tabla-km/${tablaKmId}/coordenadas`, body),

  recalcularKmFila: (tablaKmId: string) =>
    httpClient.post<TablaKm>(`/api/liquidaciones/tabla-km/${tablaKmId}/recalcular-km`),

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
