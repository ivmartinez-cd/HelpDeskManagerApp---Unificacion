import { httpClient } from "@/services/http-client";
import type {
  Cargo,
  CargoPayload,
  Empleado,
  EmpleadoListItem,
  EmpleadoPayload,
  Feriado,
  FeriadoPayload,
  ImportFeriadosResult,
  Page,
  Sector,
  SectorPayload,
  UsuarioOption,
} from "../types/vacaciones";

const BASE = "/api/vacaciones";

export const gestionApi = {
  listEmpleados: (params?: { search?: string; departmentId?: string }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.departmentId) q.set("departmentId", params.departmentId);
    const query = q.size > 0 ? `?${q.toString()}` : "";
    return httpClient
      .get<Page<EmpleadoListItem>>(`${BASE}/empleados${query}`)
      .then((p) => p.items);
  },
  createEmpleado: (payload: EmpleadoPayload) =>
    httpClient.post<Empleado>(`${BASE}/empleados`, payload),
  updateEmpleado: (id: string, payload: EmpleadoPayload) =>
    httpClient.put<Empleado>(`${BASE}/empleados/${id}`, payload),
  deleteEmpleado: (id: string) => httpClient.delete<void>(`${BASE}/empleados/${id}`),

  listSectores: () =>
    httpClient.get<Page<Sector>>(`${BASE}/sectores`).then((p) => p.items),
  createSector: (payload: SectorPayload) =>
    httpClient.post<{ id: string }>(`${BASE}/sectores`, payload),
  updateSector: (id: string, payload: SectorPayload) =>
    httpClient.put<{ id: string }>(`${BASE}/sectores/${id}`, payload),
  deleteSector: (id: string) => httpClient.delete<void>(`${BASE}/sectores/${id}`),

  listCargos: () => httpClient.get<Page<Cargo>>(`${BASE}/cargos`).then((p) => p.items),
  createCargo: (payload: CargoPayload) =>
    httpClient.post<{ id: string }>(`${BASE}/cargos`, payload),
  updateCargo: (id: string, payload: CargoPayload) =>
    httpClient.put<{ id: string }>(`${BASE}/cargos/${id}`, payload),
  deleteCargo: (id: string) => httpClient.delete<void>(`${BASE}/cargos/${id}`),

  listFeriados: () =>
    httpClient.get<Page<Feriado>>(`${BASE}/feriados`).then((p) => p.items),
  createFeriado: (payload: FeriadoPayload) =>
    httpClient.post<Feriado>(`${BASE}/feriados`, payload),
  updateFeriado: (id: string, payload: FeriadoPayload) =>
    httpClient.put<Feriado>(`${BASE}/feriados/${id}`, payload),
  deleteFeriado: (id: string) => httpClient.delete<void>(`${BASE}/feriados/${id}`),
  importarFeriados: (year: number) =>
    httpClient.post<ImportFeriadosResult>(`${BASE}/feriados/importar/${year}`),
  exportFeriados: () =>
    httpClient.downloadFile(`${BASE}/feriados/export`, "feriados-backup.json"),

  listUsuarios: () =>
    httpClient.get<Page<UsuarioOption>>(`${BASE}/usuarios`).then((p) => p.items),
};
