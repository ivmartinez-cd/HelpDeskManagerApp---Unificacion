import { httpClient } from "@/services/http-client";
import type {
  CustomerRow,
  ImportFromSupplyResponse,
  SdsContactRow,
  SyncCustomersResponse,
  ZoneContactApplyResponse,
  ZoneContactApplyRow,
  ZoneContactPreviewResponse,
  ZoneContactRow,
} from "../types";
import { BASE, toQuery, type Page } from "./insumos-api-base";

/** Métodos de `/api/insumos/customers/*` y `/api/insumos/sync-customers` —
 * separados de `insumosApi` solo para no pasar el límite de líneas del
 * archivo orquestador (`ARCHITECTURE_GUIDE.md` §4). Se componen de vuelta en
 * `insumosApi` con spread, así que el call site sigue siendo
 * `insumosApi.getContacts(...)` como siempre. */
export const insumosCustomersApi = {
  // ------------------------------------------------------------------ Clientes
  /** Todos los clientes de Insight con su flag de monitoreo. Catálogo chico:
   * el backend pagina (`Page[T]`, default 500) y acá se desenvuelve `.items`. */
  listCustomers: () =>
    httpClient.get<Page<CustomerRow>>(`${BASE}/customers`).then((p) => p.items),

  /** Habilita o deshabilita el monitoreo de un cliente. */
  toggleCustomer: (customerId: number, enabled: boolean) =>
    httpClient.patch<{ ok: boolean }>(`${BASE}/customers/${customerId}`, { enabled }),

  /** Habilita o deshabilita TODOS los clientes de una vez. */
  bulkToggleCustomers: (enabled: boolean) =>
    httpClient.post<{ ok: boolean }>(`${BASE}/customers/bulk-toggle`, { enabled }),

  /** Sincroniza la lista de clientes desde Insight (lo mismo que hace el poller). */
  syncCustomers: () => httpClient.post<SyncCustomersResponse>(`${BASE}/sync-customers`),

  /** Contactos por zona de un cliente. */
  getContacts: (customerId: number) =>
    httpClient
      .get<Page<ZoneContactRow>>(`${BASE}/customers/${customerId}/contacts`)
      .then((p) => p.items),

  /** Crea o actualiza los contactos de una zona (upsert por `zone`). */
  putContact: (customerId: number, body: ZoneContactRow) =>
    httpClient.put<{ ok: boolean }>(`${BASE}/customers/${customerId}/contacts`, body),

  /** Elimina todos los contactos de una zona. La zona va en el querystring. */
  deleteContact: (customerId: number, zone: string) =>
    httpClient.delete<{ ok: boolean }>(
      `${BASE}/customers/${customerId}/contacts${toQuery({ zone })}`,
    ),

  /** Contactos detectados en el PortalWeb SDS (solo lectura, piloto). */
  getSdsContacts: (customerId: number) =>
    httpClient
      .get<Page<SdsContactRow>>(`${BASE}/customers/${customerId}/sds-contacts`)
      .then((p) => p.items),

  /** Resuelve el contacto de una zona a partir de un N° de pedido de supply
   * (SOAP HP SDS) y hace upsert directo — sin preview, pisa la zona. */
  importContactsFromSupply: (customerId: number, supplyId: string) =>
    httpClient.post<ImportFromSupplyResponse>(
      `${BASE}/customers/${customerId}/contacts/import-from-supply`,
      { supply_id: supplyId },
    ),

  /** Preview de la importación masiva de contactos desde el PortalWeb de SDS
   * (scrapea SDS + Insight, es lento y puede fallar entero). GET, sin body. */
  previewZoneContactsImport: (customerId: number) =>
    httpClient.get<ZoneContactPreviewResponse>(
      `${BASE}/customers/${customerId}/zone-contacts-import/preview`,
    ),

  /** Aplica las filas seleccionadas del preview — re-ejecuta la resolución
   * del lado del servidor, puede no coincidir con lo que mostró el preview. */
  applyZoneContactsImport: (customerId: number, rows: ZoneContactApplyRow[]) =>
    httpClient.post<ZoneContactApplyResponse>(
      `${BASE}/customers/${customerId}/zone-contacts-import/apply`,
      { rows },
    ),
};
