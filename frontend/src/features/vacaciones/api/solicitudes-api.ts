import { httpClient } from "@/services/http-client";
import type {
  DashboardResumen,
  DecisionResult,
  EstadoSolicitud,
  EventoCalendario,
  Page,
  Saldo,
  Solapamientos,
  Solicitud,
  SolicitudPayload,
} from "../types/vacaciones";

const BASE = "/api/vacaciones";
/** Tope del backend por página (`le=500` en `solicitudes_router.py`). */
const LIST_PAGE_SIZE = 500;
/** Cubre hasta 5000 solicitudes (admin ve las de toda la empresa, sin filtro
 * de fecha) sin arriesgar un loop sin fin. */
const LIST_MAX_PAGES = 10;

export const solicitudesApi = {
  /** Un admin ve acá las solicitudes de TODA la empresa sin límite de fecha:
   * el default del backend (200) se queda corto, así que se recorren todas
   * las páginas para no truncar en silencio. */
  list: async (params?: {
    status?: EstadoSolicitud;
    empleadoId?: string;
    desde?: string;
    hasta?: string;
  }): Promise<Solicitud[]> => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.empleadoId) q.set("employeeId", params.empleadoId);
    if (params?.desde) q.set("from", params.desde);
    if (params?.hasta) q.set("to", params.hasta);
    q.set("size", String(LIST_PAGE_SIZE));

    const items: Solicitud[] = [];
    for (let page = 1; page <= LIST_MAX_PAGES; page++) {
      q.set("page", String(page));
      const result = await httpClient.get<Page<Solicitud>>(`${BASE}/solicitudes?${q.toString()}`);
      items.push(...result.items);
      if (items.length >= result.total) break;
    }
    return items;
  },
  create: (payload: SolicitudPayload) =>
    httpClient.post<Solicitud>(`${BASE}/solicitudes`, payload),
  update: (id: string, payload: Omit<SolicitudPayload, "empleadoId">) =>
    httpClient.put<Solicitud>(`${BASE}/solicitudes/${id}`, payload),
  remove: (id: string) => httpClient.delete<void>(`${BASE}/solicitudes/${id}`),
  decide: (id: string, decision: "APPROVED" | "REJECTED", comment: string | null) =>
    httpClient.post<DecisionResult>(`${BASE}/solicitudes/${id}/decision`, {
      decision,
      comment,
    }),
  solapamientos: (id: string) =>
    httpClient.get<Solapamientos>(`${BASE}/solicitudes/${id}/solapamientos`),

  saldoEmpleado: (empleadoId: string, year?: number) => {
    const q = year ? `?year=${year}` : "";
    return httpClient.get<Saldo>(`${BASE}/ciclos/empleado/${empleadoId}${q}`);
  },

  dashboard: () => httpClient.get<DashboardResumen>(`${BASE}/dashboard/resumen`),

  calendario: (desde: string, hasta: string) =>
    httpClient
      .get<Page<EventoCalendario>>(`${BASE}/calendario?from=${desde}&to=${hasta}`)
      .then((p) => p.items),
};
