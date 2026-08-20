import { httpClient } from "@/services/http-client";
import type {
  GrillaVariante,
  GrillaVariantePayload,
  PrecargaGrilla,
} from "../types/grilla-variantes";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

const BASE = "/api/turnos/grilla-variantes";

export const grillaVariantesApi = {
  list: (soloVigentes = false) =>
    httpClient
      .get<Page<GrillaVariante>>(`${BASE}${soloVigentes ? "?vigentes=true" : ""}`)
      .then((p) => p.items),

  create: (payload: GrillaVariantePayload) => httpClient.post<GrillaVariante>(BASE, payload),

  update: (id: string, payload: GrillaVariantePayload) =>
    httpClient.put<GrillaVariante>(`${BASE}/${id}`, payload),

  cancel: (id: string) => httpClient.post<void>(`${BASE}/${id}/cancelar`),

  /** Solo lectura: la grilla titular con las franjas del ausente marcadas. */
  precargar: (ausenteUserId: string, desde: string, hasta: string) => {
    const q = new URLSearchParams({ ausenteUserId, desde, hasta });
    return httpClient.post<PrecargaGrilla>(`${BASE}/precarga?${q.toString()}`);
  },
};
