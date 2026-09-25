"use client";

import { X } from "lucide-react";
import type { EstadoDashboard } from "../../hooks/use-reporte";
import type { DimensionFiltro } from "../../types/reporte";

const ETIQUETAS: Record<DimensionFiltro, string> = {
  sucursal: "Sucursal",
  categoria: "Categoría",
  subcategoria: "Subcategoría",
};
const DIMENSIONES = Object.keys(ETIQUETAS) as DimensionFiltro[];

/** Chips de los filtros activos; cada uno se quita con la ×. */
export function FiltrosActivos({ estado }: { estado: EstadoDashboard }) {
  const { reporte, filtros } = estado;
  if (!reporte?.filtros_activos) return null;
  const activas = DIMENSIONES.filter((d) => filtros[d]);

  return (
    <div className="flex flex-wrap items-center gap-2.5" aria-label="Filtros activos">
      <span className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        Filtrado por
      </span>
      {activas.map((d) => (
        <span
          key={d}
          className="inline-flex items-center gap-1 rounded-full bg-brand-orange/10 py-1 pl-3 pr-1.5 font-body text-xs font-semibold text-brand-orange"
        >
          {ETIQUETAS[d]}: {filtros[d]}
          <button
            type="button"
            disabled={estado.navegando}
            onClick={() => estado.quitarFiltro(d)}
            aria-label={`Quitar filtro de ${ETIQUETAS[d]}`}
            title={`Quitar filtro de ${ETIQUETAS[d]}`}
            className="flex cursor-pointer rounded-full p-0.5 hover:bg-brand-orange/20 disabled:opacity-50"
          >
            <X className="h-3 w-3" aria-hidden="true" />
          </button>
        </span>
      ))}
      <button
        type="button"
        disabled={estado.navegando}
        onClick={estado.limpiarFiltros}
        className="cursor-pointer px-1.5 py-1 font-body text-xs font-semibold text-muted-foreground underline hover:text-foreground disabled:opacity-50"
      >
        Limpiar todo
      </button>
    </div>
  );
}
