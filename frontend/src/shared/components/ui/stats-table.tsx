"use client";

import type { ReactNode } from "react";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import {
  type OptionalSortState,
  useOptionalTableSort,
  useSortedRows,
} from "@/shared/hooks/use-optional-table-sort";
import type { SortValue } from "@/shared/hooks/use-table-sort";
import { cn } from "@/shared/utils/cn";
import { statsSortValue } from "./stats-table-sort";

/** Tabla de lectura (rankings de Estadísticas, detalles de SLA/WATI/Bono).
 * Una columna ordena si declara `sortField` o `sortValue`.
 *
 * - Sin `sort`/`onToggleSort`: ordena sola las filas que recibe, arrancando
 *   en el orden en que llegan. Sirve cuando `rows` es la lista completa.
 * - Con `sort`/`onToggleSort`: el que la usa ordena (antes de cortar la
 *   página, o en el servidor con `sortField` como `sort_by`) y la tabla solo
 *   pinta los encabezados. Obligatorio si la tabla recibe una sola página.
 *
 * `render` recibe siempre el índice de llegada, así una columna de puesto
 * (#) sigue mostrando el ranking real aunque se reordene.
 */

export interface StatsColumn<T> {
  key: string;
  label: string;
  align?: "left" | "right";
  /** Ancho fijo opcional (clases Tailwind) para columnas numéricas. */
  className?: string;
  render: (row: T, index: number) => ReactNode;
  /** Campo de la fila por el que ordena (y el `sort_by` del backend). */
  sortField?: keyof T & string;
  /** Valor de orden cuando no alcanza con un campo (ej. un texto armado). */
  sortValue?: (row: T, index: number) => SortValue;
  /** El primer clic ordena de mayor a menor (cantidades, fechas). */
  descFirst?: boolean;
}

interface StatsTableProps<T> {
  title: string;
  subtitle?: string;
  columns: StatsColumn<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  emptyLabel?: string;
  className?: string;
  /** Clases adicionales por fila (ej. resaltar en rojo casos vencidos). */
  rowClassName?: (row: T, index: number) => string | undefined;
  /** Orden controlado desde afuera (ver comentario del archivo). */
  sort?: OptionalSortState<string>;
  onToggleSort?: (key: string) => void;
}

interface Fila<T> {
  row: T;
  index: number;
}

/** Columnas cuyo primer clic es descendente, para `useOptionalTableSort`. */
export function statsDescFirstKeys<T>(columns: StatsColumn<T>[]): string[] {
  return columns.filter((c) => c.descFirst).map((c) => c.key);
}

function useFilasOrdenadas<T>(rows: T[], columns: StatsColumn<T>[], controlado: boolean) {
  const { sort, toggleSort } = useOptionalTableSort(statsDescFirstKeys(columns));
  const filas = rows.map((row, index) => ({ row, index }));
  const valor = (f: Fila<T>, key: string) => {
    const column = columns.find((c) => c.key === key);
    return column ? statsSortValue(column, f.row, f.index) : null;
  };
  const ordenadas = useSortedRows(filas, controlado ? { key: null, direction: "asc" } : sort, valor);
  return { sort, toggleSort, ordenadas };
}

export function StatsTable<T>({
  title,
  subtitle,
  columns,
  rows,
  rowKey,
  emptyLabel = "Sin datos en el período seleccionado.",
  className,
  rowClassName,
  sort: sortExterno,
  onToggleSort,
}: StatsTableProps<T>) {
  const controlado = sortExterno !== undefined && onToggleSort !== undefined;
  const interno = useFilasOrdenadas(rows, columns, controlado);
  const sort = controlado ? sortExterno : interno.sort;
  const toggle = controlado ? onToggleSort : interno.toggleSort;
  return (
    <section
      data-print-card
      className={cn("flex flex-col rounded-[12px] border border-border bg-card", className)}
    >
      <header className="border-b border-border px-6 py-4">
        <h2 className="font-heading text-base font-bold text-foreground">{title}</h2>
        {subtitle && (
          <p className="mt-0.5 font-body text-[13px] text-muted-foreground">{subtitle}</p>
        )}
      </header>

      {rows.length === 0 ? (
        <p className="px-6 py-8 text-center font-body text-sm text-muted-foreground">
          {emptyLabel}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                {columns.map((column) => (
                  <Encabezado key={column.key} column={column} sort={sort} onToggleSort={toggle} />
                ))}
              </tr>
            </thead>
            <tbody>
              {interno.ordenadas.map(({ row, index }) => (
                <tr
                  key={rowKey(row, index)}
                  className={cn(
                    "border-t border-border align-middle last:border-b-0",
                    rowClassName?.(row, index),
                  )}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={cn(
                        "px-6 py-3 font-body text-sm text-foreground",
                        column.align === "right" ? "text-right tabular-nums" : "text-left",
                        column.className,
                      )}
                    >
                      {column.render(row, index)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

const TH =
  "whitespace-nowrap px-6 py-2.5 font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground";

function Encabezado<T>({
  column,
  sort,
  onToggleSort,
}: {
  column: StatsColumn<T>;
  sort: OptionalSortState<string>;
  onToggleSort: (key: string) => void;
}) {
  const alineacion = column.align === "right" ? "text-right" : "text-left";
  if (!column.sortField && !column.sortValue) {
    return (
      <th scope="col" className={cn(TH, alineacion, column.className)}>
        {column.label}
      </th>
    );
  }
  return (
    <SortableHeader
      column={{ key: column.key, label: column.label, className: cn(alineacion, column.className) }}
      sort={sort}
      onToggleSort={onToggleSort}
      thClassName={TH}
    />
  );
}
