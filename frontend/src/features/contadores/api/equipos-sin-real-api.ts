import { httpClient } from "@/services/http-client";
import type { Page } from "@/shared/types/pagination";
import type {
  EquipoSinReal,
  EquiposSinRealListParams,
  EquiposSinRealResumen,
} from "../types/equipos-sin-real";

/** Extraído de `contadores-api.ts` (ARCHITECTURE_GUIDE §4, límite de 300
 * líneas) — mismo patrón que la partición de `liquidaciones/api/*`. */
export const equiposSinRealApi = {
  // Consulta en vivo a Siges cacheada en el backend (TTL 10 min); filtro/
  // orden/paginación son server-side sobre ese snapshot, así que acá se
  // devuelve el envelope completo (hace falta `total` para paginar).
  listEquiposSinReal: (params: EquiposSinRealListParams) => {
    const searchParams = new URLSearchParams({
      page: String(params.page),
      size: String(params.size),
      sort_by: params.sortBy,
      sort_dir: params.sortDir,
      min_meses: String(params.minMeses),
    });
    if (params.search) searchParams.set("search", params.search);
    if (params.refresh) searchParams.set("refresh", "true");
    if (params.soloActivos) searchParams.set("solo_activos", "true");
    return httpClient.get<Page<EquipoSinReal>>(
      `/api/contadores/equipos-sin-real?${searchParams.toString()}`,
    );
  },
  // El desglose por operador del resumen sigue los mismos min_meses/
  // solo_activos que la tabla (decisión 2026-08-28); las tarjetas de
  // severidad no — el backend las mantiene sobre el universo completo.
  getEquiposSinRealResumen: (params: { minMeses: number; soloActivos?: boolean }) => {
    const searchParams = new URLSearchParams({ min_meses: String(params.minMeses) });
    if (params.soloActivos) searchParams.set("solo_activos", "true");
    return httpClient.get<EquiposSinRealResumen>(
      `/api/contadores/equipos-sin-real/resumen?${searchParams.toString()}`,
    );
  },
};
