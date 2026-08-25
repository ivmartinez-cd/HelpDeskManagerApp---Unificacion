import type { ReactNode } from "react";
import { cn } from "@/shared/utils/cn";

/** Tabla de ranking de Estadísticas (global y detalle de cliente). Son tablas
 * de lectura, cortas y ya ordenadas por el backend: no llevan sort ni
 * paginación client-side — el endpoint devuelve el top N y nada más.
 */

export interface StatsColumn<T> {
  key: string;
  label: string;
  align?: "left" | "right";
  /** Ancho fijo opcional (clases Tailwind) para columnas numéricas. */
  className?: string;
  render: (row: T, index: number) => ReactNode;
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
}: StatsTableProps<T>) {
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
                  <th
                    key={column.key}
                    scope="col"
                    className={cn(
                      "whitespace-nowrap px-6 py-2.5 font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground",
                      column.align === "right" ? "text-right" : "text-left",
                      column.className,
                    )}
                  >
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
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
