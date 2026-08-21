import { httpClient } from "@/services/http-client";
import type {
  ConversacionPendiente,
  WatiPendientesResumen,
  WatiSyncResultado,
} from "../types/wati";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const watiApi = {
  getResumen: () => httpClient.get<WatiPendientesResumen>("/api/wati/pendientes/resumen"),

  listPendientes: () =>
    httpClient
      .get<Page<ConversacionPendiente>>("/api/wati/pendientes?size=200")
      .then((page) => page.items),

  /** Fuerza un ciclo de sincronización contra WATI (permiso wati.update). */
  actualizar: () => httpClient.post<WatiSyncResultado>("/api/wati/pendientes/actualizar"),
};
