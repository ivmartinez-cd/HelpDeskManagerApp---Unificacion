import { httpClient } from "@/services/http-client";
import type { IntercambioPayload, IntercambiosApi } from "../types/coberturas";

/** Intercambio de turnos (ADR-026): `/api/turnos/intercambios`, body
 * camelCase (`IntercambioRequest` de
 * `turnos/presentation/schemas/intercambio_schemas.py`). Solo turnos. */

function toWire(payload: IntercambioPayload) {
  return {
    operadorAId: payload.operadorAId,
    operadorBId: payload.operadorBId,
    desde: payload.desde,
    hasta: payload.hasta,
    slotIdsA: payload.alcanceItemsA,
    slotIdsB: payload.alcanceItemsB,
    motivo: payload.motivo,
  };
}

export const intercambiosTurnosApi: IntercambiosApi = {
  create: (payload) =>
    httpClient.post<unknown>("/api/turnos/intercambios", toWire(payload)).then(() => undefined),

  update: (id, payload) =>
    httpClient
      .put<unknown>(`/api/turnos/intercambios/${id}`, toWire(payload))
      .then(() => undefined),

  cancel: (id) => httpClient.post<void>(`/api/turnos/intercambios/${id}/cancelar`),
};
