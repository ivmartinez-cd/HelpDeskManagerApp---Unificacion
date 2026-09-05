import { httpClient } from "@/services/http-client";
import type {
  ImportExcelMaestroResult,
  PrestadorLiquidacion,
  ReglaAlerta,
  ResultadoVinculoTablaKmSpst,
  Spst,
  TablaKm,
  Tarifario,
} from "../types/liquidaciones";
import { fetchCatalogoCompleto, type Page } from "./_shared";

/** Import de Tarifarios/Tabla KM hace upsert (por su clave natural) en vez de
 * crear siempre — reimportar el mismo CSV ya no duplica filas. */
interface ResultadoImportCsv {
  creados: number;
  actualizados: number;
  sinCambios: number;
  descartadas: number;
}

interface TarifarioBody {
  prestadorId: string;
  tipoServicio: string;
  spstId?: string;
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

/** CRUD de catálogos de configuración: prestadores, SPSTs, tarifarios, tabla KM
 * y reglas de alerta. */
export const configApi = {
  // ── Reglas de alerta ───────────────────────────────────────────────────────
  listReglasAlerta: () =>
    httpClient
      .get<Page<ReglaAlerta>>("/api/liquidaciones/reglas-alerta")
      .then((p) => p.items),

  updateReglaActiva: (codigo: string, activa: boolean) =>
    httpClient.patch<ReglaAlerta>(
      `/api/liquidaciones/reglas-alerta/${codigo}/activa`,
      { activa },
    ),

  updateReglaGeneraObservaciones: (codigo: string, generaObservaciones: boolean) =>
    httpClient.patch<ReglaAlerta>(
      `/api/liquidaciones/reglas-alerta/${codigo}/genera-observaciones`,
      { generaObservaciones },
    ),

  // ── Prestadores ────────────────────────────────────────────────────────────
  createPrestador: (body: { nombreCorto: string; nombre: string; cuit?: string; region?: string }) =>
    httpClient.post<PrestadorLiquidacion>("/api/liquidaciones/prestadores", body),

  updatePrestador: (id: string, body: { nombreCorto: string; nombre: string; cuit?: string; region?: string }) =>
    httpClient.patch<PrestadorLiquidacion>(`/api/liquidaciones/prestadores/${id}`, body),

  togglePrestadorActivo: (id: string, activo: boolean) =>
    httpClient.patch<PrestadorLiquidacion>(`/api/liquidaciones/prestadores/${id}/activo`, { activo }),

  vincularCdPrestador: (id: string, cdPrestadorId: number | null) =>
    httpClient.patch<PrestadorLiquidacion>(`/api/liquidaciones/prestadores/${id}/vincular-cd`, {
      cdPrestadorId,
    }),

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

  // ── SPSTs ──────────────────────────────────────────────────────────────────
  listSpsts: (params?: { prestadorId?: string; soloActivos?: boolean }) => {
    const qs = new URLSearchParams();
    if (params?.prestadorId) qs.set("prestadorId", params.prestadorId);
    if (params?.soloActivos) qs.set("soloActivos", "true");
    return httpClient
      .get<Page<Spst>>(`/api/liquidaciones/spsts?${qs}`)
      .then((p) => p.items);
  },

  createSpst: (body: { prestadorId: string; nombre: string; domicilio?: string; localidad?: string; provincia?: string; zonaCobertura?: string }) =>
    httpClient.post<Spst>("/api/liquidaciones/spsts", body),

  updateSpst: (id: string, body: { prestadorId: string; nombre: string; domicilio?: string; localidad?: string; provincia?: string; zonaCobertura?: string }) =>
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

  // ── Tarifarios ─────────────────────────────────────────────────────────────
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

  exportTarifariosCsv: (prestadorId?: string) =>
    httpClient.downloadFile(
      `/api/liquidaciones/tarifarios/export${prestadorId ? `?prestadorId=${prestadorId}` : ""}`,
      "tarifarios.csv",
    ),

  importTarifariosCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return httpClient.postForm<ResultadoImportCsv>("/api/liquidaciones/tarifarios/import", fd);
  },

  // ── Tabla KM ───────────────────────────────────────────────────────────────
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

  exportTablaKmCsv: (prestadorId?: string) =>
    httpClient.downloadFile(
      `/api/liquidaciones/tabla-km/export${prestadorId ? `?prestadorId=${prestadorId}` : ""}`,
      "tabla_km.csv",
    ),

  importTablaKmCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return httpClient.postForm<ResultadoImportCsv>("/api/liquidaciones/tabla-km/import", fd);
  },

  vincularSpstTablaKm: (prestadorId: string, dryRun: boolean) =>
    httpClient.post<ResultadoVinculoTablaKmSpst>(
      `/api/liquidaciones/tabla-km/vincular-spst?prestadorId=${prestadorId}&dryRun=${dryRun}`,
    ),
};
