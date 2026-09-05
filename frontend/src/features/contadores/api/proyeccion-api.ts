import { httpClient } from "@/services/http-client";
import type { Page } from "@/shared/types/pagination";
import type {
  AnexoOption,
  CandidatosEquipo,
  CrearRecesoBody,
  ForzarMetodoBody,
  GrupoEconomicoOption,
  ProcesoOption,
  RecalcularCandidatoBody,
  RecalcularCandidatoResponse,
  Receso,
  SolicitudTableroReal,
  TableroProyeccion,
} from "../types/proyeccion";

const BASE = "/api/contadores/proyeccion";

export const proyeccionApi = {
  listGruposEconomicos: () =>
    httpClient
      .get<Page<GrupoEconomicoOption>>(`${BASE}/grupos-economicos`)
      .then((page) => page.items),

  listProcesos: (idGrupoEconomico: number) =>
    httpClient
      .get<Page<ProcesoOption>>(`${BASE}/procesos?id_grupo_economico=${idGrupoEconomico}`)
      .then((page) => page.items),

  listAnexos: (idGrupoEconomico: number) =>
    httpClient
      .get<Page<AnexoOption>>(`${BASE}/anexos?id_grupo_economico=${idGrupoEconomico}`)
      .then((page) => page.items),

  // Sin `solicitud`: tablero de ejemplo (fallback del backend). Con ella,
  // consulta real contra Siges — puede tardar (grilla completa, ver
  // GetTableroProyeccionSigesUseCase en el backend).
  getTablero: (solicitud?: SolicitudTableroReal) => {
    if (!solicitud) return httpClient.get<TableroProyeccion>(`${BASE}/tablero`);
    const qs = new URLSearchParams({
      nro_proceso: String(solicitud.nroProceso),
      id_grupo_economico: String(solicitud.idGrupoEconomico),
      id_anexo: String(solicitud.idAnexo),
      fecha_objetivo: solicitud.fechaObjetivo,
    });
    return httpClient.get<TableroProyeccion>(`${BASE}/tablero?${qs.toString()}`);
  },

  getCandidatos: (idMaquina: number, clase: string) =>
    httpClient.get<CandidatosEquipo>(`${BASE}/candidatos/${idMaquina}/${clase}`),

  recalcularCandidato: (body: RecalcularCandidatoBody) =>
    httpClient.post<RecalcularCandidatoResponse>(`${BASE}/candidatos/recalcular`, body),

  forzarMetodo: (body: ForzarMetodoBody) =>
    httpClient.post<RecalcularCandidatoResponse>(`${BASE}/candidatos/forzar`, body),

  marcarPendiente: (idMaquina: number, clase: string) =>
    httpClient.post<void>(`${BASE}/candidatos/${idMaquina}/${clase}/marcar-pendiente`),

  agregarNota: (idMaquina: number, clase: string, nota: string) =>
    httpClient.post<void>(`${BASE}/candidatos/${idMaquina}/${clase}/nota`, { nota }),

  aceptarPropuesta: (idMaquina: number, clase: string) =>
    httpClient.post<void>(`${BASE}/candidatos/${idMaquina}/${clase}/aceptar`),

  listRecesos: () =>
    httpClient.get<Page<Receso>>(`${BASE}/recesos`).then((page) => page.items),

  crearReceso: (body: CrearRecesoBody) => httpClient.post<Receso>(`${BASE}/recesos`, body),

  eliminarReceso: (id: number) => httpClient.delete<void>(`${BASE}/recesos/${id}`),
};
