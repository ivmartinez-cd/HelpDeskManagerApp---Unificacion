import type { CSSProperties } from "react";
import { getInitials } from "@/shared/components/ui/user-avatar";
import { mutedColor } from "@/shared/utils/muted-color";
import type { CalendarEvent, CalendarioVerPor, CoberturaEvento, Operador } from "../types/calendario";

export function formatDateLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function getMonthDateRange(offsetMonths = 0) {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + offsetMonths;
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  return {
    startStr: formatDateLocal(firstDay),
    endStr: formatDateLocal(lastDay),
  };
}

export function cleanTitle(title: string | null | undefined): string {
  if (!title) return "";
  return title.replace(/<[^>]*>/g, "").trim();
}

export function getMonthNameCapitalized(dateStr: string): string {
  const parts = dateStr.split("-");
  if (parts.length >= 2) {
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const d = new Date(year, month, 1);
    const monthName = d.toLocaleDateString("es-AR", { month: "long" });
    const capitalizedMonth = monthName.charAt(0).toUpperCase() + monthName.slice(1);
    return `${capitalizedMonth} ${year}`;
  }
  return dateStr;
}

export function formatPillText(evt: CalendarEvent): string {
  let raw = cleanTitle(evt.title);
  if (!raw) {
    raw = evt.cliente ? `(Facturación) ${evt.cliente}` : "Facturación";
  } else {
    // Normalizar [Facturación] o [Facturación]: a (Facturación)
    raw = raw.replace(/^\[(.*?)\]\s*:?\s*/, "($1) ");
    if (!raw.startsWith("(") && evt.string_tipo_evento) {
      raw = `(${evt.string_tipo_evento}) ${raw}`;
    }
  }
  return raw;
}

// El color por evento viene de Gestión (background_color/border_color, uno
// por operador/tomador) y se respeta tal cual. Sin ese dato, se cae a la
// línea Institucional Canal Directo (naranja/gris) por tipo de evento.
export function getEventPillClassName(evt: CalendarEvent): string {
  if (evt.background_color) {
    return "text-white border border-black/10 hover:brightness-95";
  }

  const tipo = (evt.string_tipo_evento || "").toLowerCase();
  const title = (evt.title || "").toLowerCase();

  if (tipo.includes("facturaci") || title.includes("facturaci")) {
    return "bg-brand-orange text-white hover:bg-brand-orange-hover";
  }
  if (tipo.includes("vencimiento") || title.includes("vencimiento")) {
    return "bg-brand-gray text-white hover:bg-brand-charcoal";
  }
  return "bg-brand-gray/50 text-white hover:bg-brand-gray/70";
}

export function getEventPillInlineStyle(evt: CalendarEvent): CSSProperties | undefined {
  if (!evt.background_color) return undefined;
  return {
    backgroundColor: mutedColor(evt.background_color),
    borderColor: mutedColor(evt.border_color || evt.background_color),
  };
}

export const WEEKDAYS = ["LUN", "MAR", "MIÉR", "JUEV", "VIER", "SÁB", "DOM"];

/** Días de atraso de un evento respecto de `todayIso`. Ambas fechas puras
 * parseadas en UTC para no correr un día en huso negativo (mismo criterio
 * que formatFechaCobertura). */
export function diasDeAtraso(startIso: string, todayIso: string): number {
  const start = Date.parse(`${startIso.slice(0, 10)}T00:00:00Z`);
  const today = Date.parse(`${todayIso}T00:00:00Z`);
  return Math.round((today - start) / 86_400_000);
}

/** "hace 1 día" / "hace N días" para atraso ya vencido; "hoy" / "en N días"
 * cuando `dias` es cero o negativo (todavía no llegó su fecha). */
export function textoAtraso(dias: number): string {
  if (dias === 0) return "hoy";
  if (dias < 0) return -dias === 1 ? "en 1 día" : `en ${-dias} días`;
  return dias === 1 ? "hace 1 día" : `hace ${dias} días`;
}

/** "actualizado hace X" a partir de un timestamp ISO de sync; texto propio
 * cuando nunca se sincronizó. */
export function textoDesdeSync(iso: string | null): string {
  if (!iso) return "nunca sincronizado";
  const min = Math.floor((Date.now() - Date.parse(iso)) / 60_000);
  if (min < 1) return "actualizado recién";
  if (min < 60) return `actualizado hace ${min} min`;
  const horas = Math.floor(min / 60);
  if (horas < 24) return `actualizado hace ${horas} h`;
  return `actualizado hace ${Math.floor(horas / 24)} d`;
}

/** Visual del pill según el switch "Ver por" (§3.3 del handoff): en modo
 * efectivo un evento cubierto toma el color del reemplazante (o naranja
 * institucional si el catálogo no le asignó color); en modo real conserva
 * el color original de Gestión. El set de eventos nunca cambia. */
export function getPillVisual(
  evt: CalendarEvent,
  verPor: CalendarioVerPor,
): { className: string; style?: CSSProperties } {
  const cobertura = evt.cobertura;
  if (!cobertura || verPor === "real") {
    return { className: getEventPillClassName(evt), style: getEventPillInlineStyle(evt) };
  }
  const color = cobertura.operador_reemplazante_color;
  if (!color) {
    return { className: "bg-brand-orange text-white hover:bg-brand-orange-hover" };
  }
  return {
    className: "text-white border border-black/10 hover:brightness-95",
    style: { backgroundColor: mutedColor(color), borderColor: mutedColor(color) },
  };
}

export function coberturaBadgeText(cobertura: CoberturaEvento, verPor: CalendarioVerPor): string {
  const iniciales = getInitials(
    cobertura.operador_reemplazante_nombre ?? cobertura.operador_reemplazante_id,
  );
  return verPor === "efectivo" ? `CUBIERTO POR ${iniciales}` : `↩ ${iniciales} cubre`;
}

export interface OperadorEfectivo {
  id: string;
  nombre: string;
  color: string | null;
  /** Presente cuando el resultado viene de una cobertura, no del operador
   * real del evento — quien renderiza puede usarlo para avisar el reemplazo
   * (tooltip, badge). */
  cobertura: CoberturaEvento | null;
}

/** Operador que corresponde mostrar por un evento: el reemplazante cuando
 * hay una cobertura vigente (ADR-013), si no el operador real. Único punto
 * de esta regla para las cards de Inicio, que —a diferencia del Calendario—
 * no tienen el switch "ver por" y siempre muestran el efectivo. */
export function operadorEfectivo(evt: CalendarEvent, operadores: Operador[]): OperadorEfectivo | null {
  const cobertura = evt.cobertura;
  if (cobertura) {
    return {
      id: cobertura.operador_reemplazante_id,
      nombre: cobertura.operador_reemplazante_nombre ?? cobertura.operador_reemplazante_id,
      color: cobertura.operador_reemplazante_color,
      cobertura,
    };
  }
  if (!evt.operador_id) return null;
  const op = operadores.find((o) => o.id === evt.operador_id);
  return { id: evt.operador_id, nombre: op?.nombre ?? evt.operador_id, color: op?.color ?? null, cobertura: null };
}

/** "2026-08-15" → "15 ago 2026". timeZone UTC porque son fechas puras: sin
 * eso, new Date("2026-08-15") (medianoche UTC) retrocede un día en huso
 * negativo — mismo patrón que coberturas/lib/estado.ts. */
export function formatFechaCobertura(iso: string): string {
  return new Date(iso)
    .toLocaleDateString("es-AR", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" })
    .replace(/\./g, "");
}
