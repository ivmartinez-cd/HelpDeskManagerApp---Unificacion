import type { Reporte } from "../../../types/reporte";

/** Gris neutro para lo que no tiene color de categoría (el legacy usaba este). */
export const COLOR_SIN_CATEGORIA = "#9aa0a6";
export const NARANJA = "#F7941D";
/** Opacidad de lo no seleccionado cuando hay un filtro activo (legacy: .28). */
export const ALFA_ATENUADO = 0.28;

export function colorCategoria(reporte: Reporte, categoria: string | undefined): string {
  return (categoria && reporte.colores[categoria]) || COLOR_SIN_CATEGORIA;
}

/** Categoría a la que pertenece una subcategoría, según la taxonomía. */
export function categoriaDe(reporte: Reporte, subcategoria: string): string | undefined {
  return (
    reporte.subcategorias.find((s) => s.nombre === subcategoria)?.categoria ??
    reporte.taxonomia.find((c) => c.subcategorias.includes(subcategoria))?.nombre
  );
}

export function formatearPct(valor: number): string {
  return `${valor.toLocaleString("es-AR", { maximumFractionDigits: 1 })}%`;
}

/** "#rrggbb" con alfa, para atenuar colores en canvas. */
export function conAlfa(hex: string, alfa: number): string {
  const limpio = hex.replace("#", "");
  if (!/^[0-9a-fA-F]{6}$/.test(limpio)) return hex;
  return `#${limpio}${Math.round(alfa * 255).toString(16).padStart(2, "0")}`;
}

/** Recorta por el MEDIO: en las sucursales lo que distingue una de otra suele
 * estar al final ("Centro De Distribución Garín (ga)"). */
export function recortarAlMedio(valor: string, max: number): string {
  if (valor.length <= max) return valor;
  const cabeza = Math.ceil((max - 1) / 2);
  const cola = max - 1 - cabeza;
  return `${valor.slice(0, cabeza).trimEnd()}…${valor.slice(valor.length - cola).trimStart()}`;
}
