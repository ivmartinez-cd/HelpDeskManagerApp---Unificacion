/** Historial permanente y log de mails: `GET /api/insumos/audit` y
 * `GET /api/insumos/mail-log`.
 *
 * ATENCIÓN: los dos schemas del backend (`AuditRowOut`, `MailLogRowOut`) NO
 * tienen `serialization_alias`, así que viajan en **snake_case**. Es la
 * excepción dentro del módulo — el resto es camelCase. Está tipado tal cual
 * llega; no renombrar.
 */

export interface AuditRow {
  id: number;
  /** Clave del evento (`order_created`, `order_cancelled`, `dismissed`, ...). */
  event: string;
  hp_request_id?: number | null;
  device_id?: number | null;
  customer_id?: number | null;
  customer_name?: string | null;
  device_serial?: string | null;
  sku?: string | null;
  description?: string | null;
  internal_order_id?: string | null;
  /** `supply` por default. */
  order_type: string;
  detail?: string | null;
  dry_run: boolean;
  hp_request_time?: string | null;
  initial_percent_left?: number | null;
  initial_days_left?: number | null;
  initial_pages_left?: number | null;
  supply_url?: string | null;
  created_at?: string | null;
  /** Acción que ofrece la fila, ya resuelta por el backend contra toda la
   * tabla (`audit_router.py`) — el frontend ya no recalcula esto mirando
   * `allRows` cargadas en el cliente. */
  action?: "cancel" | "reconcile" | null;
}

/** Acción de fila del historial de auditoría. Vive acá (y no en
 * `audit-events.ts`, que lo re-exporta) porque es parte del contrato del
 * campo `AuditRow.action`. */
export type RowAction = "cancel" | "reconcile" | null;

/** Contadores de las tres pestañas de auditoría (`orders`/`system`/`all`),
 * calculados por el backend contra el total filtrado — no contra lo cargado
 * en el cliente. */
export interface AuditTabCounts {
  orders: number;
  system: number;
  all: number;
}

/** `GET /api/insumos/audit/summary`. Snake_case a propósito, como el resto de
 * este archivo: viaja tal cual del backend, sin `serialization_alias`. */
export interface AuditSummaryResponse {
  by_event: Record<string, number>;
  orders: number;
  system: number;
  total: number;
}

export interface MailLogRow {
  id: number;
  /** Tipo de mail: backup diario, alerta de poller, aviso de pendientes... */
  kind: string;
  recipients: string;
  subject: string;
  success: boolean;
  error?: string | null;
  sent_at: string;
}
