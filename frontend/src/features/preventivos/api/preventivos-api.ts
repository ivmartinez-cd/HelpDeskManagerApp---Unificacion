import { httpClient } from "@/services/http-client";
import type {
  EquiposPreventivosPage,
  HabilitacionPreventivo,
  ListEquiposParams,
  Page,
  ZonaParque,
} from "../types/preventivos";

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

  habilitar: (sigesMaquinaId: number, nota?: string) =>
    httpClient.post<HabilitacionPreventivo>(
      `/api/preventivos/equipos/${sigesMaquinaId}/habilitar`,
      { nota: nota || null },
    ),

  deshabilitar: (sigesMaquinaId: number) =>
    httpClient.delete<void>(`/api/preventivos/equipos/${sigesMaquinaId}/habilitar`),
};
