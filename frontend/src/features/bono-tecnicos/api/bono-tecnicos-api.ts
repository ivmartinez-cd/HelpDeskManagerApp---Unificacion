import { httpClient } from "@/services/http-client";
import type {
  CrearSolicitudTvAdminBody,
  CrearSolicitudTvBody,
  DecisionSolicitudTvBody,
  GuardarBonoInputBody,
  IncidenteBono,
  PuntajeTecnico,
  SolicitudTv,
} from "../types/bono-tecnicos";

import type { Page } from "@/shared/types/pagination";

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

  crearSolicitud: (body: CrearSolicitudTvBody) =>
    httpClient.post<SolicitudTv>("/api/bono-tecnicos/solicitudes-tv", body),

  crearSolicitudAdmin: (periodo: string, idTecnico: number, body: CrearSolicitudTvAdminBody) =>
    httpClient.post<SolicitudTv>(
      `/api/bono-tecnicos/${periodo}/${idTecnico}/solicitudes-tv`,
      body,
    ),

  getMisSolicitudes: (periodo: string) =>
    httpClient
      .get<Page<SolicitudTv>>(`/api/bono-tecnicos/solicitudes-tv/mias?periodo=${periodo}&size=100`)
      .then((p) => p.items),

  getSolicitudesPendientes: (periodo: string) =>
    httpClient
      .get<Page<SolicitudTv>>(
        `/api/bono-tecnicos/solicitudes-tv?periodo=${periodo}&estado=PENDIENTE&size=100`,
      )
      .then((p) => p.items),

  decidirSolicitud: (id: string, body: DecisionSolicitudTvBody) =>
    httpClient.patch<SolicitudTv>(`/api/bono-tecnicos/solicitudes-tv/${id}/decision`, body),
};
