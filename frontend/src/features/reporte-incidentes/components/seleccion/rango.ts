/** Lógica de rango compartida por la selección y la barra del dashboard
 * (port de `periodRangeLabel`/`RANGE_PRESETS` del legacy). */

import { PRESETS_RANGO, etiquetaPeriodo } from "../../lib/periodos";

export const PERSONALIZADO = "personalizado";

export const OPCIONES_RANGO = [
  ...PRESETS_RANGO.map((p) => ({ value: String(p.value), label: p.label })),
  { value: PERSONALIZADO, label: "Personalizado" },
];

export function esPreset(meses: number): boolean {
  return PRESETS_RANGO.some((p) => p.value === meses);
}

/** El período `n` meses antes de `periodo` ("AAAA-MM"). */
export function periodoMenos(periodo: string, n: number): string {
  const [anio, mes] = periodo.split("-").map(Number);
  const d = new Date(anio ?? 0, (mes ?? 1) - 1 - n, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

/** "Septiembre 2026" o "Abril 2026 – Septiembre 2026" (igual que el backend). */
export function etiquetaRango(hasta: string, meses: number): string {
  if (meses <= 1) return etiquetaPeriodo(hasta);
  return `${etiquetaPeriodo(periodoMenos(hasta, meses - 1))} – ${etiquetaPeriodo(hasta)}`;
}

export function textoMeses(meses: number): string {
  return meses === 1 ? "1 mes" : `${meses} meses`;
}

/** Al activar "Personalizado" sin un "Desde" previo, el legacy propone un año
 * hacia atrás (o el más viejo disponible). `opciones` va del más nuevo al más viejo. */
export function desdeInicial(opciones: string[], fallback: string): string {
  return opciones[Math.min(11, opciones.length - 1)] ?? opciones[0] ?? fallback;
}
