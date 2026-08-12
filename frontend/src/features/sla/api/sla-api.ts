import { httpClient } from "@/services/http-client";
import type { IncidenteVencido, SlaResumen } from "../types/sla";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const slaApi = {
  getResumen: (periodo: string) =>
    httpClient.get<SlaResumen>(`/api/sla/resumen?periodo=${periodo}`),

  listIncidentesVencidos: (periodo: string) =>
    httpClient
      .get<Page<IncidenteVencido>>(`/api/sla/incidentes-vencidos?periodo=${periodo}&size=500`)
      .then((p) => p.items),

  refreshResumen: (periodo: string) =>
    httpClient.post<SlaResumen>(`/api/sla/actualizar?periodo=${periodo}`),
};
