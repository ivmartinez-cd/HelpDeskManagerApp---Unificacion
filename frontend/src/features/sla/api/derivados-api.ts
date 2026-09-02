import { httpClient } from "@/services/http-client";
import type { IncidenteDerivado } from "../types/derivados";

import type { Page } from "@/shared/types/pagination";

export const derivadosApi = {
  listIncidentes: (
    periodo: string,
    params?: { operadorId?: string; page?: number; size?: number },
  ) => {
    const p = new URLSearchParams({
      periodo,
      page: String(params?.page ?? 1),
      size: String(params?.size ?? 100),
    });
    if (params?.operadorId) p.set("operadorId", params.operadorId);
    return httpClient.get<Page<IncidenteDerivado>>(`/api/sla/incidentes-derivados?${p.toString()}`);
  },
};
