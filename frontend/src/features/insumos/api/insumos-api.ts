import { httpClient } from "@/services/http-client";
import type {
  AcknowledgeResponse,
  AlertRow,
  AuditRow,
  AvailabilityWindowsResponse,
  CancelResponse,
  ConsumableDetail,
  ConsumableHistoryResponse,
  ConsumableRequestHistoryResponse,
  CustomerDetailResponse,
  DashboardResponse,
  DeviceSuppliesResponse,
  DismissDeviceResponse,
  DismissRequestPayload,
  DismissResponse,
  EstadisticasFilters,
  EstadisticasResponse,
  InsumosConfig,
  InsumosConfigPayload,
  LoadRequestPayload,
  LoadResponse,
  MailLogRow,
  NewDeviceRow,
  NewDevicesSummary,
  PendingOrderRow,
  ReconcileRequestPayload,
  ReconcileResponse,
  RequestRow,
  SaveConfigResponse,
  SyncNewDevicesResponse,
} from "../types";

/** Envelope de paginación del backend (`Page[T]` en
 * `shared/presentation/schemas/pagination.py`). Se declara local a este
 * archivo, igual que en `features/contadores/api/contadores-api.ts` — no hay
 * un tipo compartido y no se quiere acoplar features entre sí.
 *
 * A diferencia de contadores, acá NO se desenvuelve `.items` en el cliente:
 * varias tablas de insumos necesitan el `total` (el de `/alerts` es
 * directamente el contador de escaladas), así que los métodos de listado
 * devuelven el `Page<T>` completo. */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

/** Parámetros de paginación de cualquier listado del módulo. Todos los
 * endpoints tienen un `size` default generoso (500 en las tablas que filtran
 * client-side, 100 en las paginadas en SQL): omitirlos es lo normal. */
export interface PageParams {
  page?: number;
  size?: number;
}

/** Arma un querystring salteando `undefined`/`null` (mandar `?days=undefined`
 * rompe la validación de FastAPI). Devuelve "" o "?a=1&b=2". */
function toQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

const BASE = "/api/insumos";

/**
 * Todos los endpoints reales de `/api/insumos/*`, agrupados en un objeto —
 * mismo patrón que `contadoresApi`. Los nombres de campo de request y response
 * salen del OpenAPI del backend, no de la documentación del legacy: ver
 * `../types/*` para el detalle de cada schema.
 *
 * OJO con las cuatro acciones sobre solicitudes (`load`/`cancel`/`dismiss`/
 * `reconcile`) y con `saveConfig`: responden **200 aunque fallen**, con el
 * error de negocio en el body (`ok: false` + `error`). `httpClient` no tira
 * `ApiError` en esos casos — hay que chequear `response.ok` a mano.
 */
export const insumosApi = {
  // ---------------------------------------------------------------- Dashboard
  /** Resumen global de solicitudes pendientes de todos los clientes habilitados. */
  getDashboard: () => httpClient.get<DashboardResponse>(`${BASE}/dashboard`),

  // --------------------------------------------------------------- Solicitudes
  /** Solicitudes OUTSTANDING de un cliente (`customerId`) o de todos. */
  listRequests: (params: { customerId?: number } & PageParams = {}) =>
    httpClient.get<Page<RequestRow>>(`${BASE}/requests${toQuery({ ...params })}`),

  /** Crea el pedido en Canal Directo para la solicitud dada. */
  loadRequest: (requestId: number, payload: LoadRequestPayload) =>
    httpClient.post<LoadResponse>(`${BASE}/requests/${requestId}/load`, payload),

  /** Anula en Canal Directo el pedido asociado y libera el registro local. */
  cancelRequest: (requestId: number) =>
    httpClient.post<CancelResponse>(`${BASE}/requests/${requestId}/cancel`),

  /** Descarta la solicitud directamente en HP SDS (status_update=DELETE). */
  dismissRequest: (requestId: number, payload: DismissRequestPayload = {}) =>
    httpClient.post<DismissResponse>(`${BASE}/requests/${requestId}/dismiss`, payload),

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
  /** Historial permanente de eventos, más reciente primero (paginado en SQL). */
  listAudit: (params: PageParams = {}) =>
    httpClient.get<Page<AuditRow>>(`${BASE}/audit${toQuery({ ...params })}`),

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

  // ------------------------------------------------------------------ Alertas
  /** Alertas escaladas sin reconocer, la más antigua primero. El `total` del
   * envelope es el `escalatedCount` del legacy. */
  listAlerts: (params: PageParams = {}) =>
    httpClient.get<Page<AlertRow>>(`${BASE}/alerts${toQuery({ ...params })}`),

  /** Reconoce a mano una o varias alertas escaladas. */
  acknowledgeAlerts: (hpRequestIds: number[]) =>
    httpClient.post<AcknowledgeResponse>(`${BASE}/alerts/ack`, { hpRequestIds }),
};
