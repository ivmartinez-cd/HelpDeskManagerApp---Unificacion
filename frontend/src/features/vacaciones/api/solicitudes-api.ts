import { httpClient } from "@/services/http-client";
import type {
  DashboardResumen,
  EstadoSolicitud,
  EventoCalendario,
  Page,
  Saldo,
  Solapamientos,
  Solicitud,
  SolicitudPayload,
} from "../types/vacaciones";

const BASE = "/api/vacaciones";

export const solicitudesApi = {
  list: (params?: {
    status?: EstadoSolicitud;
    empleadoId?: string;
    desde?: string;
    hasta?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.empleadoId) q.set("employeeId", params.empleadoId);
    if (params?.desde) q.set("from", params.desde);
    if (params?.hasta) q.set("to", params.hasta);
    const query = q.size > 0 ? `?${q.toString()}` : "";
    return httpClient
      .get<Page<Solicitud>>(`${BASE}/solicitudes${query}`)
      .then((p) => p.items);
  },
  create: (payload: SolicitudPayload) =>
    httpClient.post<Solicitud>(`${BASE}/solicitudes`, payload),
  update: (id: string, payload: Omit<SolicitudPayload, "empleadoId">) =>
    httpClient.put<Solicitud>(`${BASE}/solicitudes/${id}`, payload),
  remove: (id: string) => httpClient.delete<void>(`${BASE}/solicitudes/${id}`),
  decide: (id: string, decision: "APPROVED" | "REJECTED", comment: string | null) =>
    httpClient.post<Solicitud>(`${BASE}/solicitudes/${id}/decision`, {
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
