/** `GET /api/insumos/dashboard` — `DashboardResponse` y anidados. */

/** `ThresholdsOut`: días restantes que separan cada severidad. */
export interface Thresholds {
  critical: number;
  urgent: number;
  warning: number;
}

/** `CustomerSummaryOut`: una fila de la tabla de clientes del Dashboard
 * (Patrón 1). `error` viene con texto cuando la consulta a HP SDS de ESE
 * cliente falló — el resto de los contadores quedan en 0, no es un 0 real. */
export interface CustomerSummary {
  customerId: number;
  name: string;
  pending: number;
  critical: number;
  urgent: number;
  warning: number;
  good: number;
  loaded: number;
  error?: string | null;
}

export interface DashboardResponse {
  /** Totales agregados por clave de severidad (`pending`, `critical`,
   * `urgent`, `warning`, `good`, ...). El backend lo declara como
   * `dict[str, int]` abierto, así que no se enumeran las claves acá. */
  totals: Record<string, number>;
  loadedToday: number;
  customersEnabled: number;
  perCustomer: CustomerSummary[];
  thresholds: Thresholds;
  /** Cada cuántos minutos conviene refrescar (lo decide la config del backend). */
  refreshMinutes: number;
}
