import type { Cobertura, CoberturaEstadoUi } from "../types/coberturas";

/** La DB solo persiste ACTIVA/CANCELADA (ADR-013): Programada y Vencida se
 * derivan por fecha en tiempo de consulta — no hay job de vencimiento, al
 * pasar `hasta` la regla simplemente deja de matchear. */
export function deriveEstado(cobertura: Cobertura, hoy: string = hoyIso()): CoberturaEstadoUi {
  if (cobertura.estado === "CANCELADA") return "cancelada";
  if (hoy < cobertura.desde) return "programada";
  if (hoy > cobertura.hasta) return "vencida";
  return "activa";
}

/** Fecha local del navegador en ISO (YYYY-MM-DD). No usar
 * `toISOString().slice(0,10)`: eso es UTC y en Argentina (UTC-3) corre el
 * día de 21:00 a 00:00. */
export function hoyIso(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export const ESTADO_META: Record<
  CoberturaEstadoUi,
  { label: string; variant: "success" | "accent" | "neutral" | "danger" }
> = {
  activa: { label: "Activa", variant: "success" },
  programada: { label: "Programada", variant: "accent" },
  vencida: { label: "Vencida", variant: "neutral" },
  cancelada: { label: "Cancelada", variant: "danger" },
};

/** "2026-08-15" → "15 ago 2026". timeZone UTC porque son fechas puras: sin
 * eso, new Date("2026-08-15") (medianoche UTC) retrocede un día en huso
 * negativo — mismo patrón que prestador-historial-panel.tsx. */
export function formatFechaCorta(iso: string): string {
  return new Date(iso)
    .toLocaleDateString("es-AR", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" })
    .replace(/\./g, "");
}
