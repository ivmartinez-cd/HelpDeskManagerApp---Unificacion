/** Alertas escaladas: `GET /api/insumos/alerts` y `POST /api/insumos/alerts/ack`.
 *
 * El listado escala las vencidas al momento de consultarlo, y el `total` del
 * envelope `Page<T>` es el `escalatedCount` del legacy — no hace falta contar
 * `items.length` (que está acotado por `size`).
 */

/** `AlertRowOut`: solicitud escalada sin reconocer. Las fechas son date-time. */
export interface AlertRow {
  hpRequestId: number;
  customerId?: number | null;
  customerName: string;
  deviceSerial: string;
  sku: string;
  description: string;
  /** Cuándo la pidió HP SDS. */
  requestedAt?: string | null;
  /** Cuándo la vio por primera vez esta app (arranca el reloj de escalado). */
  firstSeenAt: string;
  escalatedAt?: string | null;
}

export interface AcknowledgeResponse {
  ok: boolean;
  acknowledged: number;
}
