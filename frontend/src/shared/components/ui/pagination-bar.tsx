"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/shared/utils/cn";

/** Barra de paginación genérica: "Mostrando X–Y de Z" + anterior/siguiente,
 * con selector opcional de filas por página. Patrón replicado de
 * `insumos/historial-pagination.tsx` para no reinventar la UI en cada tabla. */

interface PaginationBarProps {
  page: number;
  total: number;
  size: number;
  onPageChange: (page: number) => void;
  /** Sustantivo del total ("equipos", "incidentes", "anexos"). */
  noun: string;
  sizes?: readonly number[];
  onSizeChange?: (size: number) => void;
  className?: string;
}

const navButtonClass =
  "flex cursor-pointer items-center gap-1 rounded-[8px] border border-border px-2.5 py-1.5 font-body text-xs font-semibold text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:pointer-events-none disabled:opacity-40";

export function PaginationBar({
  page,
  total,
  size,
  onPageChange,
  noun,
  sizes,
  onSizeChange,
  className,
}: PaginationBarProps) {
  const totalPages = Math.max(1, Math.ceil(total / size));
  const currentPage = Math.min(Math.max(page, 1), totalPages);
  const from = total === 0 ? 0 : (currentPage - 1) * size + 1;
  const to = Math.min(currentPage * size, total);

  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-between gap-4 px-1 py-1 font-body text-xs text-muted-foreground",
        className,
      )}
    >
      <div>
        Mostrando <span className="font-bold text-foreground">{formatNumber(from)}</span>–
        <span className="font-bold text-foreground">{formatNumber(to)}</span> de{" "}
        <span className="font-bold text-foreground">{formatNumber(total)}</span> {noun}
      </div>

      <div className="flex flex-wrap items-center gap-4">
        {sizes && onSizeChange && (
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
        )}

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            className={navButtonClass}
            disabled={currentPage <= 1}
            onClick={() => onPageChange(currentPage - 1)}
          >
            <ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" />
            Anterior
          </button>
          <span className="px-1.5 font-body text-xs font-bold text-foreground tabular-nums">
            {currentPage} / {totalPages}
          </span>
          <button
            type="button"
            className={navButtonClass}
            disabled={currentPage >= totalPages}
            onClick={() => onPageChange(currentPage + 1)}
          >
            Siguiente
            <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
}

function formatNumber(value: number): string {
  return value.toLocaleString("es-AR");
}
