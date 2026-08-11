/** Vocabulario del historial de auditoría (`GET /api/insumos/audit`) y las
 * reglas puras que decide la pantalla sobre cada fila.
 *
 * Todo lo de acá es función pura sobre `AuditRow` — sin React, sin fetch —
 * porque son las reglas que el legacy tenía inline en `HistorialView.vue` y
 * que conviene poder leer (y en el futuro testear) sin montar la tabla.
 *
 * Las claves de evento son las del backend
 * (`domain/entities/audit_record.py`): CREATED, FAILED, RELEASED, CANCELLED,
 * DISMISSED, AUTO_DISMISSED. `DEVICE_DELETED` es del legacy (baja de equipo
 * offline) y todavía no lo emite ningún caso de uso portado: se mantiene
 * mapeado para no romper cuando se porte Equipos Offline.
 */

import type { AuditRow, DateRange } from "../../types";
import type { StatusTone } from "../shared";
import { toArgDateKey } from "../../utils/format";

export const EVENT_CREATED = "CREATED";
export const EVENT_FAILED = "FAILED";
export const EVENT_RELEASED = "RELEASED";
export const EVENT_CANCELLED = "CANCELLED";
export const EVENT_DISMISSED = "DISMISSED";
export const EVENT_AUTO_DISMISSED = "AUTO_DISMISSED";
export const EVENT_DEVICE_DELETED = "DEVICE_DELETED";

export const ORDER_TYPE_SUPPLY = "supply";

/** Eventos que genera la app sola (poller, ventana de validación, baja de
 * equipos), sin que nadie apriete un botón — la pestaña "Acciones del
 * Sistema".
 *
 * DESVÍO CONSCIENTE DEL LEGACY: allá "sistema" era exactamente
 * `event === 'DEVICE_DELETED'` y todo el resto caía en "Solo Pedidos". Ese
 * evento no existe todavía en el backend portado, así que ese criterio dejaba
 * la pestaña permanentemente vacía. RELEASED (lo emite el poller cuando la
 * solicitud desapareció de SDS, ver `_request_association.py`) y
 * AUTO_DISMISSED (falsa alarma de sensor, ver `validation_window.py`) son
 * automáticos por definición, así que van acá. */
const SYSTEM_EVENTS = new Set([EVENT_RELEASED, EVENT_AUTO_DISMISSED, EVENT_DEVICE_DELETED]);

export function isSystemEvent(row: AuditRow): boolean {
  return SYSTEM_EVENTS.has(row.event);
}

const EVENT_LABELS: Record<string, string> = {
  [EVENT_CREATED]: "Creado",
  [EVENT_FAILED]: "Falló",
  [EVENT_RELEASED]: "Liberado",
  [EVENT_CANCELLED]: "Anulado",
  [EVENT_DISMISSED]: "Descartado",
  [EVENT_AUTO_DISMISSED]: "Falsa alarma",
  [EVENT_DEVICE_DELETED]: "Equipo eliminado",
};

/** Etiqueta visible del evento. Una corrida en seco se muestra como
 * "Simulación" pase lo que pase: no tocó Canal Directo. */
export function eventLabel(row: AuditRow): string {
  if (row.dry_run) return "Simulación";
  return EVENT_LABELS[row.event] ?? row.event;
}

/** Tono de la pill. El legacy usaba celeste para AUTO_DISMISSED e índigo para
 * DEVICE_DELETED: ambos están prohibidos por el handoff, van a naranja y gris
 * respectivamente. */
export function eventTone(row: AuditRow): StatusTone {
  if (row.dry_run) return "neutral";
  switch (row.event) {
    case EVENT_CREATED:
      return "ok";
    case EVENT_FAILED:
      return "atencion";
    case EVENT_RELEASED:
    case EVENT_CANCELLED:
      return "advertencia";
    case EVENT_AUTO_DISMISSED:
      return "activo";
    default:
      return "neutral";
  }
}

export const EVENT_FILTER_ALL = "ALL";
/** Valor combinado del select: el operador piensa "anulado", no distingue si
 * lo anuló él (CANCELLED) o lo liberó el poller (RELEASED). */
const EVENT_FILTER_RELEASED_CANCELLED = "RELEASED_CANCELLED";

export const EVENT_FILTER_OPTIONS: { value: string; label: string }[] = [
  { value: EVENT_FILTER_ALL, label: "Todos los eventos" },
  { value: EVENT_CREATED, label: "Creado" },
  { value: EVENT_FAILED, label: "Falló" },
  { value: EVENT_FILTER_RELEASED_CANCELLED, label: "Anulado / liberado" },
  { value: EVENT_DISMISSED, label: "Descartado" },
  { value: EVENT_AUTO_DISMISSED, label: "Falsa alarma (validación)" },
  { value: EVENT_DEVICE_DELETED, label: "Equipo eliminado" },
];

export function matchesEventFilter(row: AuditRow, value: string): boolean {
  if (value === EVENT_FILTER_ALL) return true;
  if (value === EVENT_FILTER_RELEASED_CANCELLED) {
    return row.event === EVENT_RELEASED || row.event === EVENT_CANCELLED;
  }
  return row.event === value;
}

/** Búsqueda libre sobre las mismas 6 columnas que el legacy. `term` ya viene
 * en minúsculas y sin espacios de los extremos. */
export function matchesSearch(row: AuditRow, term: string): boolean {
  if (!term) return true;
  const haystack = [
    row.customer_name,
    row.device_serial,
    row.sku,
    row.description,
    row.internal_order_id,
    row.detail,
  ];
  return haystack.some((field) => (field ?? "").toLowerCase().includes(term));
}

/** Rango de fechas sobre la **fecha de carga** (`created_at`), comparando
 * claves `YYYY-MM-DD` del día calendario argentino — no restas de
 * milisegundos, que corren de día según el huso del navegador. */
export function matchesRange(row: AuditRow, range: DateRange | null): boolean {
  if (!range) return true;
  if (!row.created_at) return false;
  const date = new Date(row.created_at);
  if (Number.isNaN(date.getTime())) return false;
  const key = toArgDateKey(date);
  return key >= range.startDate && key <= range.endDate;
}

export type RowAction = "cancel" | "reconcile" | null;

/** Qué acción ofrece la fila, si alguna. Las dos reglas miran el resto del
 * historial (`allRows`), porque lo que define si un pedido sigue vivo no es la
 * fila sino que no exista después un evento que lo cierre.
 *
 * - **Anular**: la fila creó un pedido real (CREATED, no simulación) y nada
 *   posterior lo anuló ni lo liberó.
 * - **Vincular**: la creación falló (FAILED) sobre un pedido de insumos, pero
 *   Canal Directo pudo haberlo creado igual (ver `_verify_created` del cliente
 *   SOAP) y todavía no hay un CREATED para esa solicitud.
 *
 * OJO: `allRows` es lo que la pantalla tiene cargado, no la tabla entera — con
 * el historial parcialmente cargado la regla puede ofrecer "Anular" sobre algo
 * ya anulado en una página que no se trajo. El backend responde `ok:false` en
 * ese caso, así que el peor escenario es un toast de error. */
export function rowAction(row: AuditRow, allRows: readonly AuditRow[]): RowAction {
  if (row.dry_run || !row.hp_request_id) return null;
  if (row.event === EVENT_CREATED) {
    const closed = allRows.some(
      (other) =>
        other.hp_request_id === row.hp_request_id &&
        (other.event === EVENT_CANCELLED || other.event === EVENT_RELEASED),
    );
    return closed ? null : "cancel";
  }
  if (row.event === EVENT_FAILED && row.order_type === ORDER_TYPE_SUPPLY && row.customer_id) {
    const created = allRows.some(
      (other) => other.hp_request_id === row.hp_request_id && other.event === EVENT_CREATED,
    );
    return created ? null : "reconcile";
  }
  return null;
}

/** URL del equipo en el portal de HP SDS — el mismo link que el legacy pone en
 * la columna Serie. */
export function sdsDeviceUrl(deviceId: number | null | undefined): string | null {
  return deviceId != null
    ? `https://hp-sds-latam.insightportal.net/PortalWeb/devices/${deviceId}`
    : null;
}
