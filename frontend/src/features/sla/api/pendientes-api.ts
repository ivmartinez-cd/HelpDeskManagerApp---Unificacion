import { httpClient } from "@/services/http-client";
import type { IncidenteSinCerrar, PendientesResumen } from "../types/pendientes";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const pendientesApi = {
  getResumen: (operadorId?: string) => {
    const qs = operadorId ? `?operadorId=${operadorId}` : "";
    return httpClient.get<PendientesResumen>(`/api/sla/pendientes-a-cerrar/resumen${qs}`);
  },

  listPendientes: (params?: { operadorId?: string; prestadorId?: number }) => {
    const p = new URLSearchParams({ size: "500" });
    if (params?.operadorId) p.set("operadorId", params.operadorId);
    if (params?.prestadorId != null) p.set("prestadorId", String(params.prestadorId));
    return httpClient
      .get<Page<IncidenteSinCerrar>>(`/api/sla/pendientes-a-cerrar?${p.toString()}`)
      .then((page) => page.items);
  },

  refresh: () =>
    httpClient.post<PendientesResumen>("/api/sla/pendientes-a-cerrar/actualizar"),
};
