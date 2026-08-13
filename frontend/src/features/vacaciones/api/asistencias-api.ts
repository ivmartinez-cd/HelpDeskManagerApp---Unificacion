import { httpClient } from "@/services/http-client";
import type {
  Ausencia,
  AusenciaPayload,
  DescuentoRow,
  EstadoSolicitud,
  Page,
  TipoAusencia,
} from "../types/vacaciones";

const BASE = "/api/vacaciones/ausencias";

export const asistenciasApi = {
  list: (params?: {
    empleadoId?: string;
    tipo?: TipoAusencia;
    status?: EstadoSolicitud;
    desde?: string;
    hasta?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.empleadoId) q.set("empleadoId", params.empleadoId);
    if (params?.tipo) q.set("tipo", params.tipo);
    if (params?.status) q.set("status", params.status);
    if (params?.desde) q.set("desde", params.desde);
    if (params?.hasta) q.set("hasta", params.hasta);
    const query = q.size > 0 ? `?${q.toString()}` : "";
    return httpClient.get<Page<Ausencia>>(`${BASE}${query}`).then((p) => p.items);
  },
  create: (payload: AusenciaPayload) =>
    httpClient.post<{ ids: string[] }>(BASE, payload),
  update: (id: string, payload: Omit<AusenciaPayload, "empleadoIds">) =>
    httpClient.put<{ id: string }>(`${BASE}/${id}`, payload),
  remove: (id: string) => httpClient.delete<void>(`${BASE}/${id}`),
  reporteDescuentos: (year: number, month: number, departmentId?: string) => {
    const q = new URLSearchParams({ year: String(year), month: String(month) });
    if (departmentId) q.set("departmentId", departmentId);
    return httpClient
      .get<Page<DescuentoRow>>(`${BASE}/reportes/descuentos?${q.toString()}`)
      .then((p) => p.items);
  },
};
