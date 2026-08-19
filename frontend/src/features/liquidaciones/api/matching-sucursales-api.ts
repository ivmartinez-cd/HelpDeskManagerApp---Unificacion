import { httpClient } from "@/services/http-client";
import type {
  PropuestaN2Match,
  ResultadoAutoVinculoN1,
  TablaKm,
} from "../types/liquidaciones";

/** Matching de sucursales Tabla KM ↔ Siges (Fase 1). */
export const matchingSucursalesApi = {
  autoVincularN1: (prestadorId: string) =>
    httpClient.post<ResultadoAutoVinculoN1>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/matching/auto-vincular-n1`,
    ),

  listPropuestasN2: (prestadorId: string) =>
    httpClient.get<PropuestaN2Match[]>(
      `/api/liquidaciones/siges/prestador/${prestadorId}/matching/propuestas`,
    ),

  confirmarVinculo: (tablaKmId: string, sigesSucursalId: number) =>
    httpClient.post<TablaKm>(
      `/api/liquidaciones/tabla-km/${tablaKmId}/matching/confirmar`,
      { sigesSucursalId },
    ),

  rechazarPropuesta: (tablaKmId: string, sigesSucursalId: number) =>
    httpClient.post<void>(
      `/api/liquidaciones/tabla-km/${tablaKmId}/matching/rechazar`,
      { sigesSucursalId },
    ),
};
