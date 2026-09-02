import { httpClient } from "@/services/http-client";
import type {
  ConversacionPendiente,
  WatiPendientesResumen,
  WatiSyncResultado,
} from "../types/wati";

import type { Page } from "@/shared/types/pagination";

const PENDIENTES_PAGE_SIZE = 200;
/** Tope de páginas a recorrer: cubre hasta 2000 chats pendientes, muy por
 * encima de cualquier cola real, sin arriesgar un loop sin fin. */
const PENDIENTES_MAX_PAGES = 10;

export const watiApi = {
  getResumen: () => httpClient.get<WatiPendientesResumen>("/api/wati/pendientes/resumen"),

  /** El endpoint pagina en memoria con un tope de 200 por página (no hay más
   * volumen para paginar server-side). Acá se recorren todas las páginas para
   * devolver la cola completa: el badge del header, el banner "mis chats" y
   * la card de Inicio filtran/cuentan sobre este array y necesitan verlo
   * entero, no solo la primera página. */
  listPendientes: async (): Promise<ConversacionPendiente[]> => {
    const items: ConversacionPendiente[] = [];
    for (let page = 1; page <= PENDIENTES_MAX_PAGES; page++) {
      const result = await httpClient.get<Page<ConversacionPendiente>>(
        `/api/wati/pendientes?page=${page}&size=${PENDIENTES_PAGE_SIZE}`,
      );
      items.push(...result.items);
      if (items.length >= result.total) break;
    }
    return items;
  },

  /** Fuerza un ciclo de sincronización contra WATI (permiso wati.update). */
  actualizar: () => httpClient.post<WatiSyncResultado>("/api/wati/pendientes/actualizar"),
};
