import { httpClient } from "@/services/http-client";
import type { Page } from "@/shared/types/pagination";

/** Una notificación de la bandeja, vista por el usuario logueado (`leida` es
 * suya, no global). `url`: ruta interna de la app a la que lleva el click. */
export interface Notificacion {
  id: string;
  titulo: string;
  cuerpo: string;
  url: string | null;
  creada_en: string;
  leida: boolean;
}

const BASE = "/api/notificaciones";

export const notificacionesApi = {
  listar: (opts: { soloNoLeidas: boolean; page?: number; size?: number }) =>
    httpClient.get<Page<Notificacion>>(
      `${BASE}?solo_no_leidas=${opts.soloNoLeidas}&page=${opts.page ?? 1}&size=${opts.size ?? 20}`,
    ),

  /** Sin `ids`: marca todas las que el usuario puede ver. */
  marcarLeidas: (ids?: string[]) =>
    httpClient.post<{ actualizadas: number }>(`${BASE}/marcar-leidas`, { ids: ids ?? null }),
};
