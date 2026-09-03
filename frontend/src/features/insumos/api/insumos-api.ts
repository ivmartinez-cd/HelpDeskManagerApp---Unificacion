import { httpClient } from "@/services/http-client";
import type {
  AcknowledgeResponse,
  AlertRow,
  AuditRow,
  AuditSummaryResponse,
  AvailabilityWindowsResponse,
  CancelResponse,
  ConsumableDetail,
  ConsumableHistoryResponse,
  ConsumableRequestHistoryResponse,
  CustomerDetailResponse,
  DashboardResponse,
  DeleteOfflinePayload,
  DeleteOfflineResponse,
  DeviceSuppliesResponse,
  DismissDeviceResponse,
  DismissRequestPayload,
  DismissResponse,
  EstadisticasFilters,
  EstadisticasResponse,
  IgnoreRequestPayload,
  IgnoreResponse,
  InsumosConfig,
  InsumosConfigPayload,
  LoadRequestPayload,
  LoadResponse,
  MailLogRow,
  MassOutageRow,
  NewDeviceRow,
  NewDevicesSummary,
  OfflineDismissResponse,
  OfflineDeviceRow,
  OfflineSummary,
  PendingOrderRow,
  ReconcileRequestPayload,
  ReconcileResponse,
  RequestRow,
  SaveConfigResponse,
  SyncNewDevicesResponse,
  VerifyOfflinePayload,
  VerifyOfflineResponse,
} from "../types";
import { BASE, toQuery } from "./insumos-api-base";
import type { Page, PageParams } from "./insumos-api-base";
import { insumosCustomersApi } from "./insumos-customers-api";

export type { Page, PageParams } from "./insumos-api-base";

/** Filtros que acepta `GET /api/insumos/audit` además de `page`/`size` — los
 * mismos que `GET /api/insumos/audit/summary` (que ignora `scope`: siempre
 * cuenta todo). `event` es un query param repetible (`?event=A&event=B`), así
 * que `toQuery` (que solo arma pares escalares) no alcanza para armarlo. */
interface AuditFilterParams {
  event?: string[];
  startDate?: string;
  endDate?: string;
  search?: string;
}

interface AuditListParams extends AuditFilterParams {
  page: number;
  size: number;
  scope?: "orders" | "system" | "all";
}

/** Arma el querystring de `/audit` y `/audit/summary`: los campos escalares
 * van por `toQuery` de siempre, y `event` (0 o más valores) se agrega a mano
 * repitiendo la clave — es la única forma de mandar una lista con
 * `URLSearchParams`. */
function auditQuery(params: AuditListParams | AuditFilterParams): string {
  const { event, ...scalarParams } = params;
  const base = toQuery({ ...scalarParams });
  if (!event || event.length === 0) return base;
  const search = new URLSearchParams(base.startsWith("?") ? base.slice(1) : base);
  for (const value of event) search.append("event", value);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

/**
 * Todos los endpoints reales de `/api/insumos/*`, agrupados en un objeto —
 * mismo patrón que `contadoresApi`. Los nombres de campo de request y response
 * salen del OpenAPI del backend, no de la documentación del legacy: ver
 * `../types/*` para el detalle de cada schema.
 *
 * OJO con las cuatro acciones sobre solicitudes (`load`/`cancel`/`dismiss`/
 * `reconcile`), con `saveConfig` y con los tres endpoints de importación de
 * contactos (`importContactsFromSupply`, `previewZoneContactsImport`,
 * `applyZoneContactsImport`): responden **200 aunque fallen**, con el error
 * de negocio en el body (`ok: false` + `error`). `httpClient` no tira
 * `ApiError` en esos casos — hay que chequear `response.ok` a mano.
 *
 * Los métodos de Clientes (`listCustomers`, `getContacts`, etc.) viven en
 * `./insumos-customers-api` y se componen acá con spread — es un solo
 * archivo el que se pasaba de las 300 líneas del `ARCHITECTURE_GUIDE.md`,
 * no un cambio de superficie: `insumosApi.getContacts(...)` sigue andando
 * igual que siempre.
 */
export const insumosApi = {
  // ---------------------------------------------------------------- Dashboard
  /** Resumen global de solicitudes pendientes de todos los clientes habilitados. */
  getDashboard: () => httpClient.get<DashboardResponse>(`${BASE}/dashboard`),

  // --------------------------------------------------------------- Solicitudes
  /** Solicitudes OUTSTANDING de un cliente (`customerId`) o de todos. */
  listRequests: (params: { customerId?: number } & PageParams = {}, init?: RequestInit) =>
    httpClient.get<Page<RequestRow>>(`${BASE}/requests${toQuery({ ...params })}`, init),

  /** Crea el pedido en Canal Directo para la solicitud dada. */
  loadRequest: (requestId: number, payload: LoadRequestPayload) =>
    httpClient.post<LoadResponse>(`${BASE}/requests/${requestId}/load`, payload),

  /** Anula en Canal Directo el pedido asociado y libera el registro local. */
  cancelRequest: (requestId: number) =>
    httpClient.post<CancelResponse>(`${BASE}/requests/${requestId}/cancel`),

  /** Descarta la solicitud en HP SDS — IGNORE (temporal, con auto-UNIGNORE) si
   * tenía un pedido activo sin confirmar entrega, DELETE si no. */
  dismissRequest: (requestId: number, payload: DismissRequestPayload = {}) =>
    httpClient.post<DismissResponse>(`${BASE}/requests/${requestId}/dismiss`, payload),

  /** Ignora la solicitud PERMANENTEMENTE en HP SDS (status_update=IGNORE, sin
   * UNIGNORE automático) — a diferencia de dismiss, no requiere pedido asociado. */
  ignoreRequest: (requestId: number, payload: IgnoreRequestPayload = {}) =>
    httpClient.post<IgnoreResponse>(`${BASE}/requests/${requestId}/ignore`, payload),

  /** Vincula un pedido que ya existe en CD pero que la app no registró como
   * propio (verificación post-creación fallida). Nunca crea uno nuevo. */
  reconcileRequest: (requestId: number, payload: ReconcileRequestPayload) =>
    httpClient.post<ReconcileResponse>(`${BASE}/requests/${requestId}/reconcile`, payload),

  // ------------------------------------------------------------------- Pedidos
  /** Pedidos propios que siguen circulando en CD, más viejos primero. */
  listPendingOrders: (
    params: { customerId?: number; includeDelivered?: boolean } & PageParams = {},
  ) => httpClient.get<Page<PendingOrderRow>>(`${BASE}/orders/pending${toQuery({ ...params })}`),

  // ----------------------------------------------------------------- Historial
  /** Historial permanente de eventos, más reciente primero — filtrado,
   * scopeado (`orders`/`system`/`all`) y paginado enteramente en SQL. */
  listAudit: (params: AuditListParams) =>
    httpClient.get<Page<AuditRow>>(`${BASE}/audit${auditQuery(params)}`),

  /** Conteo de eventos por pestaña (`orders`/`system`/`all`), con los mismos
   * filtros que `listAudit` salvo `scope` (el backend siempre cuenta todo). */
  getAuditSummary: (params: AuditFilterParams = {}) =>
    httpClient.get<AuditSummaryResponse>(`${BASE}/audit/summary${auditQuery(params)}`),

  /** Últimos mails enviados o intentados por la app (paginado en SQL). */
  listMailLog: (params: PageParams = {}) =>
    httpClient.get<Page<MailLogRow>>(`${BASE}/mail-log${toQuery({ ...params })}`),

  // ------------------------------------------------------- Detalle de equipos
  /** Últimos pedidos de insumos en CD para una serie (`limit` ≤ 20).
   * Con `dryRun` solo se loguea la consulta — el SOAP es read-only igual. */
  getDeviceSupplies: (serial: string, params: { limit?: number; dryRun?: boolean } = {}) =>
    httpClient.get<DeviceSuppliesResponse>(
      `${BASE}/devices/${encodeURIComponent(serial)}/supplies${toQuery({ ...params })}`,
    ),

  /** Historial de nivel (~12 meses) de UN consumible — el gráfico del modal. */
  getConsumableHistory: (deviceId: number, index: number) =>
    httpClient.get<ConsumableHistoryResponse>(
      `${BASE}/devices/${deviceId}/consumables/${index}/history`,
    ),

  /** Todas las solicitudes de HP SDS para ese consumible (los 6 workflowStatus). */
  getConsumableRequestHistory: (deviceId: number, index: number, customerId: number) =>
    httpClient.get<ConsumableRequestHistoryResponse>(
      `${BASE}/devices/${deviceId}/consumables/${index}/requests${toQuery({ customerId })}`,
    ),

  /** Datos ampliados en vivo del consumible — 404 si no existe en Insight. */
  getConsumableDetail: (deviceId: number, index: number) =>
    httpClient.get<ConsumableDetail>(`${BASE}/devices/${deviceId}/consumables/${index}/detail`),

  /** Ventanas de "sin contacto" del equipo — la franja sobre el gráfico. */
  getDeviceAvailabilityWindows: (deviceId: number) =>
    httpClient.get<AvailabilityWindowsResponse>(`${BASE}/devices/${deviceId}/availability-windows`),

  // --------------------------------------------------------------- Estadísticas
  /** Tendencia diaria + rankings globales, con comparativa contra el período
   * anterior del mismo largo. Mandá `days` O `startDate`/`endDate`. */
  getEstadisticas: (filters: EstadisticasFilters = {}) =>
    httpClient.get<EstadisticasResponse>(`${BASE}/estadisticas${toQuery({ ...filters })}`),

  /** Detalle de un cliente: éxito/error, tiempo de atención en horas hábiles,
   * tránsito logístico de CD, equipos y consumibles más pedidos. */
  getEstadisticasCliente: (customerId: number, filters: EstadisticasFilters = {}) =>
    httpClient.get<CustomerDetailResponse>(
      `${BASE}/estadisticas/clientes/${customerId}${toQuery({ ...filters })}`,
    ),

  // ------------------------------------------------------------ Configuración
  /** Parámetros de operación vigentes (umbrales, auto-carga, offline, alertas). */
  getConfig: () => httpClient.get<InsumosConfig>(`${BASE}/config`),

  /** Guarda los parámetros. Responde 200 aunque el rango sea inválido. */
  saveConfig: (payload: InsumosConfigPayload) =>
    httpClient.put<SaveConfigResponse>(`${BASE}/config`, payload),

  // ----------------------------------------------------------- Equipos nuevos
  /** Equipos sin monitorear de clientes habilitados, más nuevo primero. */
  listNewDevices: (params: PageParams = {}) =>
    httpClient.get<Page<NewDeviceRow>>(`${BASE}/new-devices${toQuery({ ...params })}`),

  /** Solo el contador de pendientes sin ignorar — el badge de la barra lateral. */
  getNewDevicesSummary: () => httpClient.get<NewDevicesSummary>(`${BASE}/new-devices/summary`),

  /** Marca o desmarca un equipo como ignorado (p.ej. fuera de contrato). */
  setNewDeviceDismissed: (deviceId: number, dismissed: boolean) =>
    httpClient.patch<DismissDeviceResponse>(`${BASE}/new-devices/${deviceId}`, { dismissed }),

  /** Fuerza el sync del inventario contra Insight (lo mismo que hace el
   * poller). Devuelve solo el resultado: la lista se vuelve a pedir aparte. */
  syncNewDevices: () => httpClient.post<SyncNewDevicesResponse>(`${BASE}/new-devices/sync`),

  // --------------------------------------------------------- Equipos offline
  /** Equipos sin reportar +72hs con veredicto de CD, más antiguo primero. */
  listOfflineDevices: (params: { customerId?: number } & PageParams = {}) =>
    httpClient.get<Page<OfflineDeviceRow>>(`${BASE}/offline-devices${toQuery({ ...params })}`),

  /** Caídas de colector y salidas masivas detectadas en el inventario actual. */
  listOfflineOutages: (params: PageParams = {}) =>
    httpClient.get<Page<MassOutageRow>>(`${BASE}/offline-devices/outages${toQuery({ ...params })}`),

  /** Contador de candidatos a baja — el badge de la barra lateral. */
  getOfflineSummary: () => httpClient.get<OfflineSummary>(`${BASE}/offline-devices/summary`),

  /** Verifica hasta `limit` equipos pendientes contra Canal Directo (SOAP).
   * Responde 409 si ya hay una verificación en curso. */
  verifyOfflineDevices: (payload: VerifyOfflinePayload) =>
    httpClient.post<VerifyOfflineResponse>(`${BASE}/offline-devices/verify`, payload),

  /** Marca o desmarca un equipo offline como descartado de la vista. */
  setOfflineDismissed: (deviceId: number, dismissed: boolean) =>
    httpClient.patch<OfflineDismissResponse>(`${BASE}/offline-devices/${deviceId}`, { dismissed }),

  /** Da de baja los equipos seleccionados en el PortalWeb de SDS (solo `deletable`). */
  deleteOfflineDevices: (payload: DeleteOfflinePayload) =>
    httpClient.post<DeleteOfflineResponse>(`${BASE}/offline-devices/delete`, payload),

  // ------------------------------------------------------------------ Alertas
  /** Alertas escaladas sin reconocer, la más antigua primero. El `total` del
   * envelope es el `escalatedCount` del legacy. */
  listAlerts: (params: PageParams = {}) =>
    httpClient.get<Page<AlertRow>>(`${BASE}/alerts${toQuery({ ...params })}`),

  /** Reconoce a mano una o varias alertas escaladas. */
  acknowledgeAlerts: (hpRequestIds: number[]) =>
    httpClient.post<AcknowledgeResponse>(`${BASE}/alerts/ack`, { hpRequestIds }),

  // ------------------------------------------------------------------ Clientes
  ...insumosCustomersApi,
};
