import { httpClient } from "@/services/http-client";
import type {
  ConfigUpdatePayload,
  ConfigVacaciones,
  Exclusion,
  Page,
  RegistroAuditoria,
} from "../types/vacaciones";

const BASE = "/api/vacaciones";

export const configApi = {
  getConfig: () => httpClient.get<ConfigVacaciones>(`${BASE}/config`),
  updateConfig: (payload: ConfigUpdatePayload) =>
    httpClient.put<ConfigVacaciones>(`${BASE}/config`, payload),

  listExclusiones: () =>
    httpClient.get<Page<Exclusion>>(`${BASE}/exclusiones`).then((p) => p.items),
  createExclusion: (empleadoAId: string, empleadoBId: string) =>
    httpClient.post<{ id: string }>(`${BASE}/exclusiones`, { empleadoAId, empleadoBId }),
  deleteExclusion: (id: string) =>
    httpClient.delete<void>(`${BASE}/exclusiones/${id}`),

  listAuditoria: (params: { search?: string; page?: number; size?: number }) => {
    const q = new URLSearchParams();
    if (params.search) q.set("search", params.search);
    if (params.page) q.set("page", String(params.page));
    if (params.size) q.set("size", String(params.size));
    const query = q.size > 0 ? `?${q.toString()}` : "";
    return httpClient.get<Page<RegistroAuditoria>>(`${BASE}/auditoria${query}`);
  },
};
