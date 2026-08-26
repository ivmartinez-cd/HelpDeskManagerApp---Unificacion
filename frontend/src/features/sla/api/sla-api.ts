import { httpClient } from "@/services/http-client";
import type { IncidenteVencido, SlaResumen } from "../types/sla";

import type { Page } from "@/shared/types/pagination";

export interface FiltroOperador {
  /** Ignora el filtro por operador y trae todos los vencidos del período. */
  todos?: boolean;
  /** Ver los PST de otro operador puntual en vez de los propios. */
  operadorId?: string;
}

function filtroQuery(filtro?: FiltroOperador): string {
  if (!filtro) return "";
  const params = new URLSearchParams();
  if (filtro.todos) params.set("todos", "true");
  if (filtro.operadorId) params.set("operadorId", filtro.operadorId);
  const qs = params.toString();
  return qs ? `&${qs}` : "";
}

export const slaApi = {
  getResumen: (periodo: string) =>
    httpClient.get<SlaResumen>(`/api/sla/resumen?periodo=${periodo}`),

  listIncidentesVencidos: (periodo: string, filtro?: FiltroOperador) =>
    httpClient
      .get<Page<IncidenteVencido>>(
        `/api/sla/incidentes-vencidos?periodo=${periodo}&size=500${filtroQuery(filtro)}`,
      )
      .then((p) => p.items),

  refreshResumen: (periodo: string) =>
    httpClient.post<SlaResumen>(`/api/sla/actualizar?periodo=${periodo}`),
};
