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
 *
 * El filtrado (evento, rango, búsqueda, scope orders/system) y la acción por
 * fila ya NO se calculan acá: los resuelve `GET /api/insumos/audit` en SQL,
 * `action` viaja en cada `AuditRow`. Este archivo se queda solo con lo que
 * sigue siendo puramente de presentación (etiquetas, tonos, el vocabulario
 * del `<select>` de eventos).
 */

import type { AuditRow } from "../../types";
import type { StatusTone } from "../shared";

export const EVENT_CREATED = "CREATED";
export const EVENT_FAILED = "FAILED";
export const EVENT_RELEASED = "RELEASED";
export const EVENT_CANCELLED = "CANCELLED";
export const EVENT_DISMISSED = "DISMISSED";
export const EVENT_AUTO_DISMISSED = "AUTO_DISMISSED";
export const EVENT_DEVICE_DELETED = "DEVICE_DELETED";

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

/** Traduce el valor del `<select>` de eventos al query param `event` del
 * backend (lista, porque el combinado "Anulado / liberado" no existe como
 * clave única del lado del servidor). `undefined` = no mandar el filtro. */
export function eventFilterToParam(value: string): string[] | undefined {
  if (value === EVENT_FILTER_ALL) return undefined;
  if (value === EVENT_FILTER_RELEASED_CANCELLED) return [EVENT_RELEASED, EVENT_CANCELLED];
  return [value];
}

/** Re-exportado acá porque `audit-table.tsx` y otros consumidores del vocabulario
 * de eventos ya importaban `RowAction` desde este archivo antes de que se
 * mudara a `types/audit.ts` (ahora es parte del contrato de `AuditRow`). */
export type { RowAction } from "../../types";

/** URL del equipo en el portal de HP SDS — el mismo link que el legacy pone en
 * la columna Serie. */
export function sdsDeviceUrl(deviceId: number | null | undefined): string | null {
  return deviceId != null
    ? `https://hp-sds-latam.insightportal.net/PortalWeb/devices/${deviceId}`
    : null;
}
