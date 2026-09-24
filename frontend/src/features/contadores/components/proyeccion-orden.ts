import type { SortState } from "@/shared/hooks/use-table-sort";
import type { FilaProyeccion, Semaforo } from "../types/proyeccion";
import { compararEsAr } from "./proyeccion-formato";

/** Orden por encabezado de la grilla del Estimador. Ordena equipos, no filas:
 * cada equipo arrastra sus clases. El orden inicial (Ubicación ascendente) es
 * el del Estimador v1.7 y lo fija `ProyeccionGrilla`. */

export type ProyeccionSortKey =
  | "ubicacion"
  | "nro_serie"
  | "modelo"
  | "meses"
  | "historico"
  | "prom6"
  | "clases"
  | "ultimo_facturado"
  | "a_facturar"
  | "impresiones"
  | "semaforo";

export const PROYECCION_SORT_KEYS: readonly ProyeccionSortKey[] = [
  "ubicacion",
  "nro_serie",
  "modelo",
  "meses",
  "historico",
  "prom6",
  "clases",
  "ultimo_facturado",
  "a_facturar",
  "impresiones",
  "semaforo",
];

/** Arrancan de mayor a menor: lo más urgente (más meses sin real, peor
 * semáforo) queda arriba con el primer clic. */
export const PROYECCION_DESC_PRIMERO: readonly ProyeccionSortKey[] = ["meses", "semaforo"];

/** Las clases de un equipo (Cl.10 primero), como `GrupoEquipo` del legacy. */
export interface GrupoEquipo {
  filas: FilaProyeccion[];
}

const GRAVEDAD: Record<Semaforo, number> = { VERDE: 0, AMARILLO: 1, NARANJA: 2, ROJO: 3 };

type Valor = string | number | null;

/** Suma de las dos primeras clases (mono + color), como "Impresiones". */
function sumaClases(g: GrupoEquipo, valor: (f: FilaProyeccion) => number | null): number {
  return g.filas.slice(0, 2).reduce((s, f) => s + (valor(f) ?? 0), 0);
}

function sumaHistorico(f: FilaProyeccion): number {
  return f.historico_12.reduce((s, v) => s + v, 0);
}

const VALOR_ORDEN: Record<ProyeccionSortKey, (g: GrupoEquipo) => Valor> = {
  ubicacion: (g) => `${g.filas[0].empresa}|${g.filas[0].sucursal}|${g.filas[0].sector}`,
  nro_serie: (g) => g.filas[0].nro_serie,
  modelo: (g) => g.filas[0].modelo,
  meses: (g) => g.filas[0].meses_sin_real,
  historico: (g) => sumaClases(g, sumaHistorico),
  prom6: (g) => sumaClases(g, (f) => f.prom_6_facturados),
  clases: (g) => g.filas.length,
  ultimo_facturado: (g) => g.filas[0].ultimo_facturado_valor,
  a_facturar: (g) => g.filas[0].estim_propuesto,
  impresiones: (g) => sumaClases(g, (f) => f.impresiones),
  semaforo: (g) => Math.max(...g.filas.map((f) => GRAVEDAD[f.semaforo])),
};

/** Texto con la cultura es-AR; los vacíos van siempre al final. */
function comparar(a: Valor, b: Valor, factor: number): number {
  if (a === null || b === null) return a === b ? 0 : a === null ? 1 : -1;
  if (typeof a === "number" && typeof b === "number") return (a - b) * factor;
  return compararEsAr(String(a), String(b)) * factor;
}

/** Orden por equipo, estable. */
export function ordenarGrupos(grupos: GrupoEquipo[], sort: SortState<ProyeccionSortKey>): GrupoEquipo[] {
  const factor = sort.direction === "asc" ? 1 : -1;
  const valor = VALOR_ORDEN[sort.key];
  return [...grupos].sort((a, b) => comparar(valor(a), valor(b), factor));
}
