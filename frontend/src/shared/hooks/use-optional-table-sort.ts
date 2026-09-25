"use client";

import { useCallback, useMemo, useState } from "react";
import { compareSortValues, type SortDirection, type SortValue } from "./use-table-sort";

/** Variante de `useTableSort` que admite "sin orden" (`key: null`): la tabla
 * arranca mostrando las filas tal como llegan (orden del backend) y recién se
 * ordena cuando el usuario clickea un encabezado. Existe para no cambiar lo que
 * se ve al entrar en tablas cuyo orden actual no sale de ninguna columna. */

export interface OptionalSortState<K extends string> {
  key: K | null;
  direction: SortDirection;
}

const UNSORTED = { key: null, direction: "asc" } as const;

/** `cycleToUnsorted`: el tercer clic sobre la misma columna vuelve al orden de
 * llegada (primero → segundo sentido → sin orden). Opt-in: replica tablas de un
 * legacy que ciclaban así (reporte de incidentes); el resto alterna asc ↔ desc. */
export interface OptionalSortOptions {
  cycleToUnsorted?: boolean;
}

export function useOptionalTableSort<K extends string>(
  descFirstKeys: readonly K[] = [],
  initial: OptionalSortState<K> = UNSORTED,
  { cycleToUnsorted = false }: OptionalSortOptions = {},
) {
  const [sort, setSort] = useState<OptionalSortState<K>>(initial);

  const toggleSort = useCallback(
    (key: K) => {
      setSort((prev) => {
        const first: SortDirection = descFirstKeys.includes(key) ? "desc" : "asc";
        if (prev.key !== key) return { key, direction: first };
        if (cycleToUnsorted && prev.direction !== first) return UNSORTED;
        return { key, direction: prev.direction === "asc" ? "desc" : "asc" };
      });
    },
    [descFirstKeys, cycleToUnsorted],
  );

  return { sort, toggleSort };
}

/** Copia ordenada de `rows` (sort estable: los empates conservan el orden de
 * llegada). Sin clave activa devuelve `rows` tal cual. */
export function useSortedRows<T, K extends string>(
  rows: readonly T[],
  sort: OptionalSortState<K>,
  valueOf: (row: T, key: K) => SortValue,
): readonly T[] {
  return useMemo(() => {
    const { key, direction } = sort;
    if (key === null) return rows;
    return [...rows].sort((a, b) => compareSortValues(valueOf(a, key), valueOf(b, key), direction));
  }, [rows, sort, valueOf]);
}

/** Fecha ISO → timestamp comparable; vacía o inválida → `null` (va al final). */
export function isoSortValue(raw: string | null | undefined): number | null {
  if (!raw) return null;
  const time = new Date(raw).getTime();
  return Number.isNaN(time) ? null : time;
}

/** Fecha de Canal Directo (`DD/MM/YYYY[ HH:MM:SS]`, hora argentina) → número
 * `YYYYMMDDHHMMSS` comparable; cualquier otro formato → `null`. */
export function cdDateSortValue(raw: string | null | undefined): number | null {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})(?: (\d{2}):(\d{2}):(\d{2}))?$/.exec((raw ?? "").trim());
  if (!match) return null;
  const [, dd, mm, yyyy, hh = "00", mi = "00", ss = "00"] = match;
  return Number(`${yyyy}${mm}${dd}${hh}${mi}${ss}`);
}

/** Booleano como número, para columnas de sí/no (`true` = 1). */
export function boolSortValue(value: boolean): number {
  return value ? 1 : 0;
}
