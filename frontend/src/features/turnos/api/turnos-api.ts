import { httpClient } from "@/services/http-client";
import type {
  Casilla,
  CreateCasillaPayload,
  CreateSlotPayload,
  ResolvedShift,
  Slot,
  UpdateCasillaPayload,
  UpdateSlotPayload,
  UserOption,
} from "../types/turnos";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const turnosApi = {
  getCurrentShifts: () =>
    httpClient.get<Page<ResolvedShift>>("/api/turnos/current").then((p) => p.items),

  listCasillas: () =>
    httpClient.get<Page<Casilla>>("/api/turnos/casillas").then((p) => p.items),

  createCasilla: (payload: CreateCasillaPayload) =>
    httpClient.post<Casilla>("/api/turnos/casillas", payload),

  updateCasilla: (id: string, payload: UpdateCasillaPayload) =>
    httpClient.put<Casilla>(`/api/turnos/casillas/${id}`, payload),

  deleteCasilla: (id: string) => httpClient.delete<void>(`/api/turnos/casillas/${id}`),

  listSlots: (casillaId?: string) => {
    const query = casillaId ? `?casillaId=${casillaId}` : "";
    return httpClient.get<Page<Slot>>(`/api/turnos/slots${query}`).then((p) => p.items);
  },

  createSlot: (payload: CreateSlotPayload) => httpClient.post<Slot>("/api/turnos/slots", payload),

  updateSlot: (id: string, payload: UpdateSlotPayload) =>
    httpClient.put<Slot>(`/api/turnos/slots/${id}`, payload),

  deleteSlot: (id: string) => httpClient.delete<void>(`/api/turnos/slots/${id}`),

  replaceAssignments: (slotId: string, userIds: string[], vigenteDesde: string) =>
    httpClient.post<void>(`/api/turnos/slots/${slotId}/asignaciones`, { userIds, vigenteDesde }),

  listAssignableUsers: () =>
    httpClient.get<Page<UserOption>>("/api/turnos/users").then((p) => p.items),
};
