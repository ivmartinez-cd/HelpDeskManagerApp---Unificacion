import { httpClient } from "@/services/http-client";
import type {
  AsignacionHistorial,
  CreatePrestadorPayload,
  OperadorOption,
  Prestador,
  PrestadoresResumen,
  SyncResult,
  UpdatePrestadorPayload,
  UpsertContactoPayload,
} from "../types/prestadores";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const prestadoresApi = {
  getResumen: () => httpClient.get<PrestadoresResumen>("/api/prestadores"),

  getPrestador: (id: string) => httpClient.get<Prestador>(`/api/prestadores/${id}`),

  listOperadores: () =>
    httpClient
      .get<Page<OperadorOption>>("/api/prestadores/operadores")
      .then((p) => p.items),

  createPrestador: (payload: CreatePrestadorPayload) =>
    httpClient.post<Prestador>("/api/prestadores", payload),

  updatePrestador: (id: string, payload: UpdatePrestadorPayload) =>
    httpClient.put<Prestador>(`/api/prestadores/${id}`, payload),

  setActive: (id: string, isActive: boolean) =>
    httpClient.post<void>(`/api/prestadores/${id}/activo`, { isActive }),

  assignOperador: (id: string, operadorId: string | null, desde: string) =>
    httpClient.post<Prestador>(`/api/prestadores/${id}/operador`, { operadorId, desde }),

  listHistorial: (id: string) =>
    httpClient
      .get<Page<AsignacionHistorial>>(`/api/prestadores/${id}/historial?size=200`)
      .then((p) => p.items),

  syncDesdeSiges: () => httpClient.post<SyncResult>("/api/prestadores/sync"),

  createContacto: (prestadorId: string, payload: UpsertContactoPayload) =>
    httpClient.post(`/api/prestadores/${prestadorId}/contactos`, payload),

  updateContacto: (prestadorId: string, contactoId: string, payload: UpsertContactoPayload) =>
    httpClient.put(`/api/prestadores/${prestadorId}/contactos/${contactoId}`, payload),

  deleteContacto: (prestadorId: string, contactoId: string) =>
    httpClient.delete<void>(`/api/prestadores/${prestadorId}/contactos/${contactoId}`),
};
