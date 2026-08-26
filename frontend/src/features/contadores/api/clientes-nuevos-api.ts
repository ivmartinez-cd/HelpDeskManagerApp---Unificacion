import { httpClient } from "@/services/http-client";
import type {
  CandidatosClientesNuevos,
  ClienteNuevo,
  ClienteNuevoPayload,
} from "../types/clientes-nuevos";

/** Envelope `Page[T]` del backend (ver contadores-api.ts): las fichas son
 * decenas por año, se piden en una sola página y se filtran en la UI. */
import type { Page } from "@/shared/types/pagination";

const BASE = "/api/contadores/clientes-nuevos";

export const clientesNuevosApi = {
  list: (refresh = false) =>
    httpClient
      .get<Page<ClienteNuevo>>(`${BASE}?size=500${refresh ? "&refresh=true" : ""}`)
      .then((page) => page.items),
  create: (payload: ClienteNuevoPayload) => httpClient.post<ClienteNuevo>(BASE, payload),
  update: (id: string, payload: ClienteNuevoPayload) =>
    httpClient.put<ClienteNuevo>(`${BASE}/${id}`, payload),
  remove: (id: string) => httpClient.delete<void>(`${BASE}/${id}`),
  /** Empresas de Siges con primer contrato firmado en la ventana y sin ficha. */
  candidatos: (dias = 120, refresh = false) =>
    httpClient.get<CandidatosClientesNuevos>(
      `${BASE}/candidatos?dias=${dias}${refresh ? "&refresh=true" : ""}`,
    ),
};
