import { httpClient } from "@/services/http-client";
import type {
  EquiposPreventivosPage,
  HabilitacionPreventivo,
  ListEquiposParams,
  ListPuntosMapaParams,
  Page,
  PuntosMapaPage,
  ZonaParque,
} from "../types/preventivos";

// El mapa es por zona (~decenas de sucursales, hasta un par de cientos):
// una sola página al tamaño máximo alcanza, sin necesidad de paginar la UI.
const _MAX_PUNTOS_MAPA = 500;

export const preventivosApi = {
  /** Catálogo de zonas locales (DISTINCT real de Siges menos exclusiones);
   * son ~14, se piden en una sola página y se desenvuelve `.items`. */
  listZonas: () =>
    httpClient
      .get<Page<ZonaParque>>("/api/preventivos/zonas?size=100")
      .then((page) => page.items),

  listEquipos: (params: ListEquiposParams) => {
    const searchParams = new URLSearchParams({
      zona: params.zona,
      page: String(params.page ?? 1),
      size: String(params.size ?? 50),
    });
    if (params.estado) searchParams.set("estado", params.estado);
    if (params.habilitado !== undefined) {
      searchParams.set("habilitado", String(params.habilitado));
    }
    if (params.q) searchParams.set("q", params.q);
    if (params.refresh) searchParams.set("refresh", "true");
    return httpClient.get<EquiposPreventivosPage>(
      `/api/preventivos/equipos?${searchParams.toString()}`,
    );
  },

  listPuntosMapa: (params: ListPuntosMapaParams) => {
    const searchParams = new URLSearchParams({
      zona: params.zona,
      size: String(_MAX_PUNTOS_MAPA),
    });
    if (params.estado) searchParams.set("estado", params.estado);
    if (params.habilitado !== undefined) {
      searchParams.set("habilitado", String(params.habilitado));
    }
    if (params.q) searchParams.set("q", params.q);
    if (params.refresh) searchParams.set("refresh", "true");
    return httpClient.get<PuntosMapaPage>(`/api/preventivos/mapa?${searchParams.toString()}`);
  },

  habilitar: (sigesMaquinaId: number, nota?: string) =>
    httpClient.post<HabilitacionPreventivo>(
      `/api/preventivos/equipos/${sigesMaquinaId}/habilitar`,
      { nota: nota || null },
    ),

  deshabilitar: (sigesMaquinaId: number) =>
    httpClient.delete<void>(`/api/preventivos/equipos/${sigesMaquinaId}/habilitar`),
};
