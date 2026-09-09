import { httpClient } from "@/services/http-client";
import type {
  EvolucionEquipo,
  EvolucionTecnico,
  GuardarBonoInputBody,
  IncidenteBono,
  MiResumenBono,
  PuntajeTecnico,
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

  /** Puntaje/conteos/TV del técnico autenticado — sin `periodo`, el mes en
   * curso (backend). Las solicitudes de TV en sí (cargar/aprobar) son del
   * módulo `tareas-varias`, ver `tareas-varias-api.ts`. */
  getMiResumen: (periodo?: string) =>
    httpClient.get<MiResumenBono>(
      periodo ? `/api/bono-tecnicos/mi-resumen?periodo=${periodo}` : "/api/bono-tecnicos/mi-resumen",
    ),

  /** Si el usuario autenticado tiene vínculo Empleado↔Siges — chequear antes
   * de pedir `getMiResumen`/`tareasVariasApi.getMisSolicitudes`, que tiran
   * 404 sin vínculo (un superadmin ve todos los módulos aunque no sea
   * técnico, ver `ListVisibleModules`). */
  getVinculoSiges: () =>
    httpClient.get<{ vinculado: boolean }>("/api/bono-tecnicos/vinculo-siges"),

  getEvolucionAnual: (anio: number) =>
    httpClient
      .get<Page<EvolucionTecnico>>(`/api/bono-tecnicos/evolucion-anual?anio=${anio}&size=100`)
      .then((p) => p.items),

  getEvolucionEquipo: (anio: number) =>
    httpClient.get<EvolucionEquipo>(`/api/bono-tecnicos/evolucion-anual/equipo?anio=${anio}`),
};
