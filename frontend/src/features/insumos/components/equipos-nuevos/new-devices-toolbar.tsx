"use client";

import { Search } from "lucide-react";
import { cn } from "@/shared/utils/cn";

/** Barra de acciones de Equipos Nuevos: búsqueda libre + filtro por año de
 * descubrimiento + switch de "ignorados". Mismo estilo de input que el
 * Patrón 5 del handoff (`radius 8px`, borde sutil, foco naranja). */

export const ALL_YEARS = "all";

interface NewDevicesToolbarProps {
  query: string;
  onQueryChange: (value: string) => void;
  year: string;
  years: readonly string[];
  onYearChange: (value: string) => void;
  showDismissed: boolean;
  onShowDismissedChange: (value: boolean) => void;
  dismissedCount: number;
}

const controlClass =
  "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange focus:ring-2 focus:ring-brand-orange/30";

export function NewDevicesToolbar({
  query,
  onQueryChange,
  year,
  years,
  onYearChange,
  showDismissed,
  onShowDismissedChange,
  dismissedCount,
}: NewDevicesToolbarProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-3">
      <div className="relative min-w-[240px] flex-1 sm:max-w-sm">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <input
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Buscar por serie, modelo, cliente, zona o IP…"
          aria-label="Buscar equipos nuevos"
          className={cn(controlClass, "w-full pl-9")}
        />
      </div>

      <label className="flex items-center gap-2 font-body text-sm text-muted-foreground">
        <span>Descubiertos en</span>
        <select
          value={year}
          onChange={(event) => onYearChange(event.target.value)}
          className={cn(controlClass, "cursor-pointer")}
        >
          <option value={ALL_YEARS}>Todos los años</option>
          {years.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="flex cursor-pointer items-center gap-2 font-body text-sm text-muted-foreground">
        <input
          type="checkbox"
          checked={showDismissed}
          onChange={(event) => onShowDismissedChange(event.target.checked)}
          className="h-4 w-4 cursor-pointer accent-[#F7941D]"
        />
        <span>
          Mostrar ignorados
          {dismissedCount > 0 && ` (${dismissedCount})`}
        </span>
      </label>
    </div>
  );
}
