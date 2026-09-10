import { httpClient } from "@/services/http-client";
import type { Page } from "@/shared/types/pagination";
import type { ModificacionPrestador } from "../types/modificacion";

const BASE = "/api/liquidaciones";

export const modificacionesApi = {
  listNoVistas: (page = 1, size = 50) =>
    httpClient.get<Page<ModificacionPrestador>>(
      `${BASE}/modificaciones?page=${page}&size=${size}`,
    ),

  listByLiquidacion: (liquidacionId: string, page = 1, size = 50) =>
    httpClient.get<Page<ModificacionPrestador>>(
      `${BASE}/${liquidacionId}/modificaciones?page=${page}&size=${size}`,
    ),

  marcarVistas: (liquidacionId: string) =>
    httpClient.post<{ actualizadas: number }>(
      `${BASE}/${liquidacionId}/modificaciones/marcar-vistas`,
    ),
};
