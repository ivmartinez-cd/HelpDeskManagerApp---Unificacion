import { httpClient } from "@/services/http-client";
import type {
  CrearSolicitudTvAdminBody,
  CrearSolicitudTvBody,
  DecisionSolicitudTvBody,
  SolicitudTv,
} from "../types/tareas-varias";

import type { Page } from "@/shared/types/pagination";

export const tareasVariasApi = {
  crearSolicitud: (body: CrearSolicitudTvBody) =>
    httpClient.post<SolicitudTv>("/api/tareas-varias", body),

  crearSolicitudAdmin: (idTecnico: number, body: CrearSolicitudTvAdminBody) =>
    httpClient.post<SolicitudTv>(`/api/tareas-varias/a-nombre-de/${idTecnico}`, body),

  getMisSolicitudes: (periodo: string) =>
    httpClient
      .get<Page<SolicitudTv>>(`/api/tareas-varias/mias?periodo=${periodo}&size=100`)
      .then((p) => p.items),

  getSolicitudesPendientes: (periodo: string) =>
    httpClient
      .get<Page<SolicitudTv>>(`/api/tareas-varias?periodo=${periodo}&estado=PENDIENTE&size=100`)
      .then((p) => p.items),

  decidirSolicitud: (id: string, body: DecisionSolicitudTvBody) =>
    httpClient.patch<SolicitudTv>(`/api/tareas-varias/${id}/decision`, body),
};
