/** Períodos "AAAA-MM" y rangos (port de `format.ts` del legacy). */

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

/** Rango máximo pedible de una vez (cada mes viejo agranda la consulta a wsAyC). */
export const MAX_MESES_RANGO = 24;

/** Presets compartidos por la selección y la barra del dashboard. */
export const PRESETS_RANGO = [
  { value: 1, label: "1 mes" },
  { value: 3, label: "3 meses" },
  { value: 6, label: "6 meses" },
  { value: 12, label: "1 año" },
  { value: 24, label: "2 años" },
] as const;

export function etiquetaPeriodo(periodo: string): string {
  const [anio, mes] = periodo.split("-").map(Number);
  return `${MESES[(mes ?? 1) - 1] ?? ""} ${anio ?? ""}`;
}

/** Los últimos `cantidad` períodos, del más nuevo al más viejo. */
export function periodosRecientes(cantidad = MAX_MESES_RANGO, desde = new Date()): string[] {
  return Array.from({ length: cantidad }, (_, i) => {
    const d = new Date(desde.getFullYear(), desde.getMonth() - i, 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });
}

/** Meses entre dos períodos, inclusive (asume desde <= hasta). */
export function mesesEntre(desde: string, hasta: string): number {
  const [da, dm] = desde.split("-").map(Number);
  const [ha, hm] = hasta.split("-").map(Number);
  return (ha ?? 0) * 12 + (hm ?? 1) - ((da ?? 0) * 12 + (dm ?? 1)) + 1;
}

export function acotarMeses(meses: number): number {
  return Number.isFinite(meses) && meses >= 1 ? Math.min(Math.floor(meses), MAX_MESES_RANGO) : 1;
}

export function formatearEntero(valor: number): string {
  return new Intl.NumberFormat("es-AR").format(valor);
}

/** "10/06" o "10" según el rango abarque más de un mes. */
export function etiquetaDia(fechaIso: string, variosMeses: boolean): string {
  const [, mes, dia] = fechaIso.split("-");
  return variosMeses ? `${dia}/${mes}` : (dia ?? "");
}
