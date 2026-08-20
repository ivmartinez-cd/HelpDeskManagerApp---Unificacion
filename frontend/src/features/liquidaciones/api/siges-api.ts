import { httpClient } from "@/services/http-client";
import type {
  PrestadorLiquidacion,
  PropuestasVinculo,
  Spst,
  SucursalPropia,
  SucursalSiges,
  SyncSigesResult,
  SyncTarifariosResult,
  ZonasSiges,
} from "../types/liquidaciones";
import type { Page } from "./_shared";

/** Vínculo y sync contra Siges (ADR-014). */
export const sigesApi = {
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

  /** Todas las sucursales del PST en Siges, paginando de a 200 (tope `le=200`
   * del endpoint). El Asistente de KM las necesita completas para contar qué
   * importar — con una sola página los conteos eran falsos (SAN JUAN: 948). */
  listarTodasSucursalesSiges: async (prestadorId: string): Promise<SucursalSiges[]> => {
    const items: SucursalSiges[] = [];
    for (let page = 1; ; page++) {
      const qs = new URLSearchParams({ prestadorId, q: "", size: "200", page: String(page) });
      const pagina = await httpClient.get<Page<SucursalSiges>>(`/api/liquidaciones/siges/sucursales?${qs}`);
      items.push(...pagina.items);
      if (items.length >= pagina.total || pagina.items.length === 0) return items;
    }
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
};
