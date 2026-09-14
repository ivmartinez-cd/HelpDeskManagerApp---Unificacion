import { httpClient } from "@/services/http-client";
import type {
  GrillaVariante,
  GrillaVariantePayload,
  PrecargaGrilla,
} from "../types/grilla-variantes";

import type { Page } from "@/shared/types/pagination";

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

  /** Solo lectura: la grilla titular con las franjas del ausente marcadas (o completa si ausenteUserId es null). */
  precargar: (ausenteUserId: string | null, desde: string, hasta: string) => {
    const params: Record<string, string> = { desde, hasta };
    if (ausenteUserId) params.ausenteUserId = ausenteUserId;
    const q = new URLSearchParams(params);
    return httpClient.post<PrecargaGrilla>(`${BASE}/precarga?${q.toString()}`);
  },
};
