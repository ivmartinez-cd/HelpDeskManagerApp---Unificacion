"use client";

import type { ReactNode } from "react";
import { Search } from "lucide-react";
import { DateRangePickerPopover } from "../shared";
import type { DateRange } from "../../types";
import { EVENT_FILTER_OPTIONS } from "./audit-events";

/** Barra de filtros combinados de la pantalla: búsqueda de texto + tipo de
 * evento (solo en las pestañas de auditoría) + rango de fechas (Patrón 4 en su
 * variante popover) + los controles propios de cada pestaña (`children`).
 *
 * Todos los filtros son client-side: ninguno de los tres endpoints del
 * Historial acepta filtros por query param (ver `use-historial-audit.ts`). */

interface HistorialFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder: string;
  /** Se omite en las pestañas que no son de auditoría. */
  eventFilter?: string;
  onEventFilterChange?: (value: string) => void;
  range: DateRange | null;
  onRangeChange: (range: DateRange | null) => void;
  /** Texto a la derecha ("N eventos"), y controles extra por pestaña. */
  summary?: ReactNode;
  children?: ReactNode;
}

export function HistorialFilters({
  search,
  onSearchChange,
  searchPlaceholder,
  eventFilter,
  onEventFilterChange,
  range,
  onRangeChange,
  summary,
  children,
}: HistorialFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <label className="relative flex min-w-[240px] flex-1 items-center sm:max-w-[340px]">
        <Search
          className="pointer-events-none absolute left-3 h-4 w-4 text-muted-foreground"
          aria-hidden="true"
        />
        <span className="sr-only">Buscar</span>
        <input
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={searchPlaceholder}
          className="w-full rounded-[8px] border border-border bg-card py-2.5 pl-9 pr-3 font-body text-sm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-brand-orange/40"
        />
      </label>

      {eventFilter !== undefined && onEventFilterChange && (
        <label className="flex items-center gap-2 font-body text-xs text-muted-foreground">
          <span className="whitespace-nowrap">Evento</span>
          <select
            value={eventFilter}
            onChange={(event) => onEventFilterChange(event.target.value)}
            className="rounded-[8px] border border-border bg-card px-2.5 py-2 font-body text-[13px] text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
          >
            {EVENT_FILTER_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      )}

      <DateRangePickerPopover
        value={range}
        onChange={onRangeChange}
        placeholder="Todo el historial"
      />

      {children}

      {summary && (
        <div className="ml-auto font-body text-xs text-muted-foreground">{summary}</div>
      )}
    </div>
  );
}
