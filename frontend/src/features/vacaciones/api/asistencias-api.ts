import { httpClient } from "@/services/http-client";
import type {
  Ausencia,
  AusenciaPayload,
  DecisionAusenciaResult,
  DescuentoRow,
  EstadoSolicitud,
  Page,
  TipoAusencia,
} from "../types/vacaciones";

const BASE = "/api/vacaciones/ausencias";
/** Tope del backend por página (ver `_DEFAULT_SIZE`/`le=500` en
 * `ausencias_router.py`). */
const LIST_PAGE_SIZE = 500;
/** Cubre hasta 5000 ausencias — muy por encima de lo que junta la empresa en
 * años de historial — sin arriesgar un loop sin fin. */
const LIST_MAX_PAGES = 10;

export const asistenciasApi = {
  /** El calendario y el listado (con su filtro "Todos los años") necesitan el
   * historial completo en memoria para funcionar bien, así que acá se
   * recorren todas las páginas en vez de devolver solo la primera — el
   * default del backend (200) se queda corto para varios años de ausencias
   * de toda la empresa. */
  list: async (params?: {
    empleadoId?: string;
    tipo?: TipoAusencia;
    status?: EstadoSolicitud;
    desde?: string;
    hasta?: string;
  }): Promise<Ausencia[]> => {
    const q = new URLSearchParams();
    if (params?.empleadoId) q.set("empleadoId", params.empleadoId);
    if (params?.tipo) q.set("tipo", params.tipo);
    if (params?.status) q.set("status", params.status);
    if (params?.desde) q.set("desde", params.desde);
    if (params?.hasta) q.set("hasta", params.hasta);
    q.set("size", String(LIST_PAGE_SIZE));

    const items: Ausencia[] = [];
    for (let page = 1; page <= LIST_MAX_PAGES; page++) {
      q.set("page", String(page));
      const result = await httpClient.get<Page<Ausencia>>(`${BASE}?${q.toString()}`);
      items.push(...result.items);
      if (items.length >= result.total) break;
    }
    return items;
  },
  create: (payload: AusenciaPayload) =>
    httpClient.post<{ ids: string[] }>(BASE, payload),
  update: (id: string, payload: Omit<AusenciaPayload, "empleadoIds">) =>
    httpClient.put<{ id: string }>(`${BASE}/${id}`, payload),
  remove: (id: string) => httpClient.delete<void>(`${BASE}/${id}`),
  /** Aprobar/rechazar una baja pedida por un empleado (home office, cambio
   * de horario): mismo circuito que las solicitudes de vacaciones. */
  decide: (id: string, decision: "APPROVED" | "REJECTED", comment: string | null) =>
    httpClient.post<DecisionAusenciaResult>(`${BASE}/${id}/decision`, { decision, comment }),
  reporteDescuentos: (year: number, month: number, departmentId?: string) => {
    const q = new URLSearchParams({ year: String(year), month: String(month) });
    if (departmentId) q.set("departmentId", departmentId);
    return httpClient
      .get<Page<DescuentoRow>>(`${BASE}/reportes/descuentos?${q.toString()}`)
      .then((p) => p.items);
  },
};
