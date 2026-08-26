import { httpClient } from "@/services/http-client";
import type { IncidenteMesaAyuda } from "../types/mesa-ayuda";

import type { Page } from "@/shared/types/pagination";

export const mesaAyudaApi = {
  listIncidentes: (params?: { operador?: string }) => {
    const p = new URLSearchParams({ size: "500" });
    if (params?.operador) p.set("operador", params.operador);
    return httpClient
      .get<Page<IncidenteMesaAyuda>>(`/api/sla/mesa-de-ayuda?${p.toString()}`)
      .then((page) => page.items);
  },
};
