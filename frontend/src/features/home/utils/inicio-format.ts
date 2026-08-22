export const FALLBACK_COLOR = "#F7941D";

export function fmtInt(n: number): string {
  return n.toLocaleString("es-AR");
}

export function fmtPct(n: number): string {
  return n.toLocaleString("es-AR", { maximumFractionDigits: 2 });
}

/** Tinte de fondo del handoff: color del operador mezclado con transparente
 * vía `--tint-alpha` (definido por tema en globals.css). Un alpha fijo en hex
 * se veía bien sobre card oscuro pero quedaba casi invisible sobre card claro
 * (mismo % de color, mucho más desaturado al mezclar con blanco) — por eso el
 * alpha depende del tema en vez de estar hardcodeado. Solo aplica a colores
 * hex; para cualquier otro formato cae a un tinte neutro sobre `--foreground`. */
export function tint(color: string): string {
  return /^#[0-9a-fA-F]{6}$/.test(color)
    ? `color-mix(in srgb, ${color} var(--tint-alpha, 13%), transparent)`
    : "color-mix(in srgb, var(--foreground) 6%, transparent)";
}

/** Texto de acento sobre `tint()`: el color crudo del operador pierde
 * contraste contra su propio tinte cuando `--tint-alpha` es alto (tema
 * claro) — se oscurece con `--accent-text-weight` (100% = sin cambio, el
 * comportamiento original que ya andaba bien en oscuro). */
export function accentText(color: string): string {
  return /^#[0-9a-fA-F]{6}$/.test(color)
    ? `color-mix(in oklch, ${color} var(--accent-text-weight, 100%), black)`
    : color;
}

/** Intensidad del heatmap semanal (README del handoff): 0 vacía, 1-2 tenue,
 * 3-4 media, 5+ naranja sólido. El texto de 1-4 mezcla `--foreground` en vez
 * de blanco fijo: sobre el tinte naranja pálido de tema claro, blanco fijo
 * quedaba invisible (mismo bug de fondo que `tint()`). */
export function heatCellStyle(n: number): { bg: string; text: string } {
  if (n === 0) return { bg: "var(--chart-empty)", text: "transparent" };
  if (n <= 2) return { bg: "rgba(247,148,29,.14)", text: "color-mix(in srgb, var(--foreground) 75%, transparent)" };
  if (n <= 4) return { bg: "rgba(247,148,29,.38)", text: "color-mix(in srgb, var(--foreground) 75%, transparent)" };
  return { bg: "#F7941D", text: "#fff" };
}

export const AGING_BUCKETS = [
  { label: "1-2 días", min: 0, max: 2, color: "#22c55e" },
  { label: "3-4 días", min: 3, max: 4, color: "#9aa832" },
  { label: "5-7 días", min: 5, max: 7, color: "#d69e08" },
  { label: "8-10 días", min: 8, max: 10, color: "#c2410c" },
  { label: "+10 días", min: 11, max: Infinity, color: "#ef4444" },
] as const;

/** Dot semántico de la lista de pendientes: ≥10 rojo, ≥5 ámbar, <5 verde. */
export function agingDotColor(dias: number): string {
  if (dias >= 10) return "#ef4444";
  if (dias >= 5) return "#d69e08";
  return "#22c55e";
}

/** Minutos transcurridos desde un ISO; null si no hay fecha. */
export function minutosDesde(iso: string | null | undefined, ahora = Date.now()): number | null {
  if (!iso) return null;
  const t = Date.parse(iso);
  return Number.isNaN(t) ? null : Math.max(0, Math.round((ahora - t) / 60_000));
}

/** Formato ÚNICO de frescura del dashboard: "hace un momento" / "hace 12 min" /
 * "hace 3 h" / "hace 2 d". Antes cada card tenía el suyo. */
export function textoHace(iso: string | null | undefined, ahora = Date.now()): string {
  const mins = minutosDesde(iso, ahora);
  if (mins === null) return "sin fecha";
  if (mins < 2) return "hace un momento";
  if (mins < 60) return `hace ${mins} min`;
  const horas = Math.round(mins / 60);
  if (horas < 48) return `hace ${horas} h`;
  return `hace ${Math.round(horas / 24)} d`;
}

/** "Sábado 22 de agosto" para el encabezado de Inicio. */
export function fechaLarga(d: Date): string {
  const s = d.toLocaleDateString("es-AR", { weekday: "long", day: "numeric", month: "long" });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** "AAAAMM" del mes actual desplazado `offset` meses (para /api/sla/resumen). */
export function periodoOffset(offset: number): string {
  const now = new Date();
  const d = new Date(now.getFullYear(), now.getMonth() + offset, 1);
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}`;
}

/** "Mar", "Abr"... para las etiquetas de la tendencia SLA. */
export function periodoLabel(periodo: string): string {
  const d = new Date(Number(periodo.slice(0, 4)), Number(periodo.slice(4, 6)) - 1, 1);
  const mes = d.toLocaleDateString("es-AR", { month: "short" }).replace(".", "");
  return mes.charAt(0).toUpperCase() + mes.slice(1);
}
