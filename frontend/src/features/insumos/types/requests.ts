/** Solicitudes de insumos y pedidos en Canal Directo:
 * `GET /api/insumos/requests`, `GET /api/insumos/orders/pending` y las cuatro
 * acciones `POST /api/insumos/requests/{id}/{load,cancel,dismiss,reconcile}`.
 *
 * OJO con las acciones: el backend responde **200 siempre**, incluso cuando la
 * operación falla. El error de negocio viaja en el body (`ok: false` + `error`
 * / `conflictType`), no como status HTTP — o sea que `httpClient` NO va a
 * tirar `ApiError`. Hay que ramificar por `response.ok`.
 */

/** `RequestRowOut`: una solicitud OUTSTANDING de HP SDS, ya enriquecida con
 * equipo, severidad, validación y el pedido propio asociado (si existe). */
export interface RequestRow {
  requestId: number;
  deviceId: number;
  customerId?: number | null;
  customerName?: string | null;
  store: string;
  serial: string;
  description: string;
  sku: string;
  /** Nivel de tóner en % (`number`, puede tener decimales). */
  percentLeft?: number | null;
  daysLeft: number;
  pagesLeft?: number | null;
  /** Índice del consumible dentro del equipo — el que pide
   * `/devices/{deviceId}/consumables/{index}/...`. */
  consumableIndex?: number | null;
  /** URL al consumible en el portal de Insight. */
  consumableUrl: string;
  /** Fecha de la solicitud ya formateada por el backend (string de display). */
  time: string;
  /** Misma fecha en crudo (ISO) para ordenar/filtrar. */
  rawTime?: string | null;
  /** `critical` | `urgent` | `warning` | `good` (según los umbrales de config). */
  statusKey: string;
  statusLabel: string;
  /** Id del pedido propio en Canal Directo, si ya se cargó. */
  orderId?: string | null;
  requestedPercent?: number | null;
  requestedDaysLeft?: number | null;
  lastContact?: string | null;
  daysOffline?: number | null;
  /** El equipo lleva demasiado sin reportar: el nivel mostrado es viejo. */
  isStaleOffline: boolean;
  /** Se cargó el pedido pero todavía no se confirmó el cambio de consumible. */
  validationPending: boolean;
  validationDeadline?: string | null;
  validationSwapNote?: string | null;
  validationDiagnosisHeadline?: string | null;
  validationDiagnosisDetail?: string | null;
  supplyId?: string | null;
  supplyUrl?: string | null;
  supplyStatus?: string | null;
  /** Aviso de entrega alternativa (zona con observación "CARGAR PARA SUCURSAL: ...").
   * No hay forma de fijar la sucursal de entrega por SOAP, así que esto solo alimenta
   * un aviso — ver detect_sucursal_override en el backend. sucursalEntrega es null si
   * el patrón matcheó pero no se pudo extraer un nombre legible; ahí se muestra
   * observacionZona completa igual. */
  requiereCambioSucursal: boolean;
  sucursalEntrega?: string | null;
  observacionZona?: string | null;
}

/** `SupplyStatusEventOut`: un estado del pedido en CD y cuándo la app lo
 * detectó por primera vez (no el momento real de la transición: CD no lo
 * expone). */
export interface SupplyStatusEvent {
  estado: string;
  at: string;
}

/** `PendingOrderRowOut`: pedido propio que sigue circulando en Canal Directo. */
export interface PendingOrderRow {
  hpRequestId: number;
  customerId: number;
  customerName?: string | null;
  deviceId: number;
  serial: string;
  store: string;
  sku: string;
  description: string;
  orderId: string;
  supplyUrl?: string | null;
  supplyStatus: string;
  createdAt?: string | null;
  /** Nivel/días/páginas al momento de crear el pedido. */
  initialPercentLeft?: number | null;
  initialDaysLeft?: number | null;
  initialPagesLeft?: number | null;
  /** Los mismos valores hoy — sirven para ver si el consumible ya se cambió. */
  currentPercentLeft?: number | null;
  currentDaysLeft?: number | null;
  currentPagesLeft?: number | null;
  statusKey?: string | null;
  statusLabel?: string | null;
  statusHistory?: SupplyStatusEvent[];
}

/** `LoadRequestBody`. No acepta deviceId/serial/sku a propósito: todo se
 * deriva del lado del servidor releyendo Insight (diseño de seguridad del
 * legacy). */
export interface LoadRequestPayload {
  customerId: number;
  customerName: string;
  dryRun?: boolean;
  forceOverride?: boolean;
  overrideInsumoId?: string | null;
  revision?: boolean;
}

/** `LoadResponse`. Status 200 SIEMPRE — ver nota al tope del archivo. */
export interface LoadResponse {
  ok: boolean;
  orderId?: string | null;
  supplyUrl?: string | null;
  warn?: string | null;
  error?: string | null;
  /** Tipo de conflicto de negocio (p.ej. pedido ya existente en CD) que la UI
   * usa para elegir el flujo de resolución (reconciliar / forzar / elegir). */
  conflictType?: string | null;
  conflictData?: Record<string, unknown> | null;
  /** Opciones de insumo para elegir cuando el SKU es ambiguo — cada opción es
   * un mapa plano de strings; se pasa la elegida como `overrideInsumoId`. */
  options?: Record<string, string>[] | null;
  /** Presente cuando ok=true y la zona tiene instrucción de entrega alternativa: el
   * frontend abre el modal recordatorio de cambio de sucursal. */
  requiereCambioSucursal?: boolean;
  sucursalEntrega?: string | null;
  observacionZona?: string | null;
}

export interface CancelResponse {
  ok: boolean;
  supplyStatus?: string | null;
  error?: string | null;
}

/** `DismissRequestBody` (action_schemas): solo metadatos para el Historial —
 * la baja en HP SDS usa el id del path. */
export interface DismissRequestPayload {
  customerId?: number | null;
  customerName?: string;
  serial?: string;
  sku?: string;
}

export interface DismissResponse {
  ok: boolean;
  error?: string | null;
}

export interface ReconcileRequestPayload {
  customerId: number;
  customerName?: string;
}

export interface ReconcileResponse {
  ok: boolean;
  orderId?: string | null;
  supplyUrl?: string | null;
  alreadyLinked?: boolean;
  error?: string | null;
}
