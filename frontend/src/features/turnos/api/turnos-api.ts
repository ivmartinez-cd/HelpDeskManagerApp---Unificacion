import { httpClient } from "@/services/http-client";
import type {
  Casilla,
  CreateCasillaPayload,
  CreateSlotPayload,
  CurrentShifts,
  ResolvedShift,
  Slot,
  UpdateCasillaPayload,
  UpdateSlotPayload,
  UserOption,
  VarianteActiva,
} from "../types/turnos";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

/** `/current` es un `Page` + `varianteActiva` (aditivo, ADR-025). */
type CurrentShiftsWire = Page<ResolvedShift> & { varianteActiva?: VarianteActiva | null };

export const turnosApi = {
  getCurrentShifts: (): Promise<CurrentShifts> =>
    httpClient.get<CurrentShiftsWire>("/api/turnos/current").then((p) => ({
      shifts: p.items,
      varianteActiva: p.varianteActiva ?? null,
    })),

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
