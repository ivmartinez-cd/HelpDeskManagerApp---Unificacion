/** Estadísticas: `GET /api/insumos/estadisticas` (global) y
 * `GET /api/insumos/estadisticas/clientes/{customerId}` (detalle).
 *
 * Los dos aceptan los mismos filtros de período: `days` (últimos N días) O
 * `startDate`/`endDate` — si mandás `startDate`, el backend ignora `days`.
 * Ambas respuestas traen además el período inmediatamente anterior del mismo
 * largo (`previousStartDate`/`previousEndDate` + los totales) para la
 * comparativa, ya calculado del lado del servidor: no recalcular en la UI.
 *
 * Todas las fechas de acá son `YYYY-MM-DD` salvo las que dicen lo contrario.
 */

/** `DailyPointOut`: un día de la serie de tendencia. */
export interface DailyPoint {
  date: string;
  created: number;
  failed: number;
}

/** `CustomerStatOut`: ranking de clientes de la vista global. */
export interface CustomerStat {
  customerId: number;
  customerName: string;
  created: number;
  failed: number;
  total: number;
}

/** `SkuStatOut`: ranking de insumos más pedidos. */
export interface SkuStat {
  sku: string;
  description?: string | null;
  count: number;
}

/** `DeviceStatOut`: ranking de equipos (solo en el detalle de cliente). */
export interface DeviceStat {
  deviceSerial: string;
  count: number;
}

/** `FailureReasonOut`: motivos de error agrupados. `lastAt` es date-time. */
export interface FailureReason {
  reason: string;
  count: number;
  lastAt: string;
}

/** `RecentFailureOut`. `createdAt` es date-time. */
export interface RecentFailure {
  createdAt: string;
  sku?: string | null;
  deviceSerial?: string | null;
  detail?: string | null;
}

/** `FulfillmentWorstOut`: el peor caso de tiempo de atención del período. */
export interface FulfillmentWorst {
  createdAt: string;
  sku?: string | null;
  deviceSerial?: string | null;
  minutes: number;
}

/** `FulfillmentStatsOut`: tiempo de atención medido en **horas hábiles**
 * (`workHourStart`–`workHourEnd`, según la config del módulo). `coveragePct`
 * dice sobre qué porcentaje de los pedidos se pudo medir. */
export interface FulfillmentStats {
  measured: number;
  totalCreated: number;
  coveragePct: number;
  avgMinutes?: number | null;
  maxMinutes?: number | null;
  worst?: FulfillmentWorst | null;
  workHourStart: number;
  workHourEnd: number;
}

/** `PendingToDispatchWorstOut`. */
export interface PendingToDispatchWorst {
  orderId: string;
  sku?: string | null;
  deviceSerial?: string | null;
  days: number;
}

/** `PendingToDispatchStatsOut`: tránsito logístico dentro de Canal Directo
 * (de Pendiente a Despachado), en días corridos. */
export interface PendingToDispatchStats {
  measured: number;
  totalCreated: number;
  coveragePct: number;
  avgDays?: number | null;
  maxDays?: number | null;
  worst?: PendingToDispatchWorst | null;
}

/** `EstadisticasResponse` — vista global. */
export interface EstadisticasResponse {
  days: number;
  startDate: string;
  endDate: string;
  /** Fecha del primer dato disponible; acota el rango elegible del picker. */
  earliestDate?: string | null;
  totalCreated: number;
  totalFailed: number;
  previousCreated: number;
  previousStartDate: string;
  previousEndDate: string;
  dailyAverage: number;
  peakDay?: string | null;
  peakDayCount: number;
  activeCustomers: number;
  distinctSkus: number;
  series: DailyPoint[];
  topCustomers: CustomerStat[];
  topSkus: SkuStat[];
}

/** `CustomerDetailResponse` — detalle de un cliente. */
export interface CustomerDetailResponse {
  customerId: number;
  customerName: string;
  days: number;
  startDate: string;
  endDate: string;
  earliestDate?: string | null;
  previousStartDate: string;
  previousEndDate: string;
  totalCreated: number;
  totalFailed: number;
  /** 0–100. */
  successRate: number;
  previousCreated: number;
  previousFailed: number;
  dailyAverage: number;
  peakDay?: string | null;
  peakDayCount: number;
  /** Cuántos pedidos los creó la auto-carga vs. un operario. */
  autoCreated: number;
  manualCreated: number;
  autoPct: number;
  monitoredDevices: number;
  distinctSkus: number;
  fulfillment: FulfillmentStats;
  pendingToDispatch: PendingToDispatchStats;
  series: DailyPoint[];
  topSkus: SkuStat[];
  topDevices: DeviceStat[];
  failureReasons: FailureReason[];
  recentFailures: RecentFailure[];
}

/** Filtros de período comunes a los dos endpoints. Mandá `days` O el par
 * `startDate`/`endDate`, no las dos cosas. */
export interface EstadisticasFilters {
  days?: number;
  startDate?: string;
  endDate?: string;
}
