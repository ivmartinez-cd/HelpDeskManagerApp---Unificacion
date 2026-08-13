/** Helpers de fechas del módulo (strings YYYY-MM-DD del wire, sin Date con
 * timezone para evitar off-by-one). */

const MESES_CORTOS = [
  "ene",
  "feb",
  "mar",
  "abr",
  "may",
  "jun",
  "jul",
  "ago",
  "sep",
  "oct",
  "nov",
  "dic",
];

export function formatFechaCorta(iso: string): string {
  const [, m, d] = iso.split("-").map(Number);
  return `${String(d).padStart(2, "0")}/${String(m).padStart(2, "0")}`;
}

export function formatFecha(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return `${String(d).padStart(2, "0")}/${String(m).padStart(2, "0")}/${y}`;
}

export function formatRango(desde: string, hasta: string): string {
  const [, m1, d1] = desde.split("-").map(Number);
  const [, m2, d2] = hasta.split("-").map(Number);
  return `${d1} ${MESES_CORTOS[m1 - 1]} – ${d2} ${MESES_CORTOS[m2 - 1]}`;
}

export function formatAntiguedad(anios: number): string {
  if (anios < 1) return "menos de 1 año";
  const enteros = Math.floor(anios);
  return enteros === 1 ? "1 año" : `${enteros} años`;
}

export function hoyIso(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function iniciales(nombre: string): string {
  return nombre
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

/** Paleta de identidad para sectores/empleados (semántica de UI, no colores
 * de otras líneas de marca — ver design_handoff_vacaciones/README.md). */
export const COLORES_IDENTIDAD = [
  "#2563eb",
  "#059669",
  "#d97706",
  "#475569",
  "#dc2626",
  "#0f766e",
] as const;
