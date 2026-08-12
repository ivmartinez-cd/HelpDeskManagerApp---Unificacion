import type { CSSProperties } from "react";
import type { CalendarEvent } from "../types/calendario";

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

// Los colores que manda Gestión son directos de operador/tomador, pensados
// para un fondo claro — sobre el tema oscuro de esta app quedan demasiado
// saturados/neón (feedback del usuario, 2026-08-12). Se atenúan mezclando
// con negro en oklch (más parejo perceptualmente que mezclar en sRGB) en vez
// de un CSS `filter` sobre el pill entero, que también opacaría el texto
// blanco encima.
function mutedColor(hex: string): string {
  return `color-mix(in oklch, ${hex} 70%, black)`;
}

export function getEventPillInlineStyle(evt: CalendarEvent): CSSProperties | undefined {
  if (!evt.background_color) return undefined;
  return {
    backgroundColor: mutedColor(evt.background_color),
    borderColor: mutedColor(evt.border_color || evt.background_color),
  };
}

export const WEEKDAYS = ["LUN", "MAR", "MIÉR", "JUEV", "VIER", "SÁB", "DOM"];
