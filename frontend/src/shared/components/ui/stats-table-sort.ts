"use client";

import { useCallback } from "react";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import type { SortValue } from "@/shared/hooks/use-table-sort";
import type { StatsColumn } from "./stats-table";

/** Orden de `StatsTable` para quien lo controla desde afuera. */

/** Valor por el que ordena una columna: `sortValue`, o si no el `sortField`.
 * Un valor que no es texto ni número (fecha ISO incluida, que es texto y
 * ordena bien así) se ignora. */
export function statsSortValue<T>(column: StatsColumn<T>, row: T, index: number): SortValue {
  if (column.sortValue) return column.sortValue(row, index);
  if (!column.sortField) return null;
  const valor: unknown = row[column.sortField];
  if (typeof valor === "boolean") return valor ? 1 : 0;
  return typeof valor === "string" || typeof valor === "number" ? valor : null;
}

/** Campo a mandar como `sort_by` al backend para la columna activa. */
export function statsSortField<T>(columns: StatsColumn<T>[], key: string | null): string | undefined {
  return columns.find((c) => c.key === key)?.sortField;
}

function descFirst<T>(columns: StatsColumn<T>[]): string[] {
  return columns.filter((c) => c.descFirst).map((c) => c.key);
}

/** Para tablas paginadas en el navegador: ordena la lista COMPLETA (antes de
 * cortar la página) y devuelve el estado para pasarle a `StatsTable`.
 * `onChange` corre en cada clic (típicamente, volver a la página 1). */
export function useStatsSort<T>(columns: StatsColumn<T>[], rows: readonly T[], onChange?: () => void) {
  const { sort, toggleSort } = useOptionalTableSort(descFirst(columns));
  const valor = useCallback(
    (row: T, key: string) => {
      const column = columns.find((c) => c.key === key);
      return column ? statsSortValue(column, row, rows.indexOf(row)) : null;
    },
    [columns, rows],
  );
  const ordenadas = useSortedRows(rows, sort, valor);
  const onToggleSort = (key: string) => {
    toggleSort(key);
    onChange?.();
  };
  return { sort, onToggleSort, ordenadas };
}

/** Para tablas paginadas en el servidor: solo el estado; el que la usa manda
 * `statsSortField(columns, sort.key)` y `sort.direction` al backend. */
export function useStatsServerSort<T>(columns: StatsColumn<T>[], onChange?: () => void) {
  const { sort, toggleSort } = useOptionalTableSort(descFirst(columns));
  const onToggleSort = (key: string) => {
    toggleSort(key);
    onChange?.();
  };
  return { sort, onToggleSort };
}
