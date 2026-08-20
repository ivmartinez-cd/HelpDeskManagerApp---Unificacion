import type { GrillaVariante, VarianteEstadoUi } from "../types/grilla-variantes";

/** La DB solo persiste ACTIVA/CANCELADA (ADR-025): Programada/Vigente/Vencida
 * se derivan por fecha en el cliente — no hay job de vencimiento, al pasar
 * `hasta` la grilla titular vuelve sola (mismo criterio que Coberturas). */
export function deriveEstadoVariante(
  variante: Pick<GrillaVariante, "estado" | "desde" | "hasta">,
  hoy: string = hoyIso(),
): VarianteEstadoUi {
  if (variante.estado === "CANCELADA") return "cancelada";
  if (hoy < variante.desde) return "programada";
  if (hoy > variante.hasta) return "vencida";
  return "vigente";
}

/** Fecha local del navegador en ISO (YYYY-MM-DD) — no `toISOString()`, que es
 * UTC y en Argentina corre el día de 21:00 a 00:00. */
export function hoyIso(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export const ESTADO_VARIANTE_META: Record<
  VarianteEstadoUi,
  { label: string; variant: "success" | "accent" | "neutral" | "danger" }
> = {
  vigente: { label: "Vigente", variant: "success" },
  programada: { label: "Programada", variant: "accent" },
  vencida: { label: "Vencida", variant: "neutral" },
  cancelada: { label: "Cancelada", variant: "danger" },
};

/** "2026-08-28" → "28/08" */
export function formatDiaMes(iso: string): string {
  const [, m, d] = iso.split("-");
  return `${d}/${m}`;
}

/** "2026-08-28" → "28/08/2026" */
export function formatFecha(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

/** "08:30:00" → "08:30" */
export function hhmm(hora: string): string {
  return hora.slice(0, 5);
}
