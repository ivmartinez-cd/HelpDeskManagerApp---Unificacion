import { httpClient } from "@/services/http-client";
import type { IncidenteMesaAyuda } from "../types/mesa-ayuda";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const mesaAyudaApi = {
  listIncidentes: (params?: { operador?: string }) => {
    const p = new URLSearchParams({ size: "500" });
    if (params?.operador) p.set("operador", params.operador);
    return httpClient
      .get<Page<IncidenteMesaAyuda>>(`/api/sla/mesa-de-ayuda?${p.toString()}`)
      .then((page) => page.items);
  },
};
