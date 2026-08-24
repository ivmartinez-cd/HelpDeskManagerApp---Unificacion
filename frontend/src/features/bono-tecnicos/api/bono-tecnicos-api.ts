import { httpClient } from "@/services/http-client";
import type { GuardarBonoInputBody, IncidenteBono, PuntajeTecnico } from "../types/bono-tecnicos";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const bonoTecnicosApi = {
  getResumen: (periodo: string) =>
    httpClient
      .get<Page<PuntajeTecnico>>(`/api/bono-tecnicos/resumen?periodo=${periodo}&size=100`)
      .then((p) => p.items),

  guardarInput: (periodo: string, idTecnico: number, body: GuardarBonoInputBody) =>
    httpClient.put<void>(`/api/bono-tecnicos/${periodo}/${idTecnico}`, body),

  getIncidentes: (periodo: string, idTecnico: number) =>
    httpClient
      .get<Page<IncidenteBono>>(
        `/api/bono-tecnicos/${periodo}/${idTecnico}/incidentes?size=200`,
      )
      .then((p) => p.items),
};
