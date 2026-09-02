import { httpClient } from "@/services/http-client";
import type { IncidenteSinCerrar, PendientesResumen } from "../types/pendientes";

import type { Page } from "@/shared/types/pagination";

export const pendientesApi = {
  getResumen: (operadorId?: string) => {
    const qs = operadorId ? `?operadorId=${operadorId}` : "";
    return httpClient.get<PendientesResumen>(`/api/sla/pendientes-a-cerrar/resumen${qs}`);
  },

  listPendientes: (params?: {
    operadorId?: string;
    prestadorId?: number;
    page?: number;
    size?: number;
  }) => {
    const p = new URLSearchParams({
      page: String(params?.page ?? 1),
      size: String(params?.size ?? 100),
    });
    if (params?.operadorId) p.set("operadorId", params.operadorId);
    if (params?.prestadorId != null) p.set("prestadorId", String(params.prestadorId));
    return httpClient.get<Page<IncidenteSinCerrar>>(`/api/sla/pendientes-a-cerrar?${p.toString()}`);
  },

  refresh: () =>
    httpClient.post<PendientesResumen>("/api/sla/pendientes-a-cerrar/actualizar"),
};
