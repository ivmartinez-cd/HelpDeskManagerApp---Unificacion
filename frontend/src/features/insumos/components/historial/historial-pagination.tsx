"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { formatNumber } from "../../utils/format";

/** Pie de paginación compartido por la tabla de auditoría y la de mails:
 * "Mostrando X–Y de Z" + filas por página + anterior/siguiente. */

interface HistorialPaginationProps {
  page: number;
  pageCount: number;
  /** Índices 1-based del primer y último ítem visible. */
  from: number;
  to: number;
  total: number;
  size: number;
  sizes: readonly number[];
  onPageChange: (page: number) => void;
  onSizeChange: (size: number) => void;
  /** Sustantivo del total ("eventos", "mails"). */
  noun: string;
}

const navButtonClass =
  "flex cursor-pointer items-center gap-1 rounded-[8px] border border-border px-2.5 py-1.5 font-body text-xs font-semibold text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:pointer-events-none disabled:opacity-40";

export function HistorialPagination({
  page,
  pageCount,
  from,
  to,
  total,
  size,
  sizes,
  onPageChange,
  onSizeChange,
  noun,
}: HistorialPaginationProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 px-1 py-1 font-body text-xs text-muted-foreground">
      <div>
        Mostrando <span className="font-bold text-foreground">{formatNumber(from)}</span>–
        <span className="font-bold text-foreground">{formatNumber(to)}</span> de{" "}
        <span className="font-bold text-foreground">{formatNumber(total)}</span> {noun}
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2">
          <span className="whitespace-nowrap">Filas por página</span>
          <select
            value={size}
            onChange={(event) => onSizeChange(Number(event.target.value))}
            className="rounded-[8px] border border-border bg-card px-2 py-1.5 font-body text-xs text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
          >
            {sizes.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            className={navButtonClass}
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" />
            Anterior
          </button>
          <span className={cn("px-1.5 font-body text-xs font-bold text-foreground tabular-nums")}>
            {page} / {pageCount}
          </span>
          <button
            type="button"
            className={navButtonClass}
            disabled={page >= pageCount}
            onClick={() => onPageChange(page + 1)}
          >
            Siguiente
            <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
}
