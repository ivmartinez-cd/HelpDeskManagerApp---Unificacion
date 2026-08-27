import { httpClient } from "@/services/http-client";
import type { IncidenteDerivado } from "../types/derivados";

import type { Page } from "@/shared/types/pagination";

export const derivadosApi = {
  listIncidentes: (periodo: string, params?: { operadorId?: string }) => {
    const p = new URLSearchParams({ periodo, size: "500" });
    if (params?.operadorId) p.set("operadorId", params.operadorId);
    return httpClient
      .get<Page<IncidenteDerivado>>(`/api/sla/incidentes-derivados?${p.toString()}`)
      .then((page) => page.items);
  },
};
