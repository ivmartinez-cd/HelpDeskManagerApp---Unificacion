"use client";

import type { MouseEvent, ReactNode } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { PENDIENTE, type DimensionFiltro, type Incidente } from "../../types/reporte";
import type { EstadoDashboard } from "../../hooks/use-reporte";
import { cn } from "@/shared/utils/cn";
import { DetalleIncidente } from "./detalle-incidente";
import { URL_WEBAGENTES } from "./estilos";

export const CANTIDAD_COLUMNAS = 8;
const TD = "border-t border-border px-3 py-3 align-top font-body text-[13px] leading-[18px] text-foreground";
/** Como el legacy: corta a 75 caracteres con "..." (el texto completo queda en
 * el `title` y en el detalle expandido). */
const LIMITE_RECORTE = 75;

function recortar(texto: string | null | undefined): string {
  if (!texto || texto === "—") return "—";
  return texto.length <= LIMITE_RECORTE ? texto : `${texto.slice(0, LIMITE_RECORTE)}...`;
}

const detener = (e: MouseEvent) => e.stopPropagation();

/** Botón que alterna un filtro del dashboard (sucursal, categoría, subcategoría). */
function BotonFiltro({
  estado,
  dimension,
  valor,
  className,
  children,
}: {
  estado: EstadoDashboard;
  dimension: DimensionFiltro;
  valor: string;
  className?: string;
  children: ReactNode;
}) {
  const activo = estado.filtros[dimension] === valor;
  return (
    <button
      type="button"
      disabled={estado.navegando}
      onClick={(e) => {
        e.stopPropagation();
        estado.alternarFiltro(dimension, valor);
      }}
      title={activo ? "Quitar filtro" : `Filtrar por ${valor}`}
      className={cn(
        "cursor-pointer text-left transition-colors hover:text-brand-orange hover:underline disabled:cursor-wait",
        activo && "font-semibold text-brand-orange",
        className,
      )}
    >
      {children}
    </button>
  );
}

function CeldaTipificacion({ incidente, estado }: { incidente: Incidente; estado: EstadoDashboard }) {
  const categoria = incidente.categoria ?? PENDIENTE;
  if (categoria === PENDIENTE) {
    return (
      <BotonFiltro estado={estado} dimension="categoria" valor={PENDIENTE}>
        <span className="inline-flex whitespace-nowrap rounded-full bg-warning/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[.025em] text-warning">
          Pendiente de revisión
        </span>
      </BotonFiltro>
    );
  }
  const color = estado.reporte?.colores[categoria] ?? "var(--muted-foreground)";
  return (
    <div className="flex items-start gap-2">
      <span className="mt-1.5 h-2 w-2 flex-none rounded-[2px]" style={{ background: color }} aria-hidden="true" />
      <div className="flex min-w-0 flex-col">
        {incidente.subcategoria && (
          <BotonFiltro estado={estado} dimension="subcategoria" valor={incidente.subcategoria.trim()} className="font-semibold">
            {incidente.subcategoria}
          </BotonFiltro>
        )}
        <BotonFiltro estado={estado} dimension="categoria" valor={categoria} className="text-[11px] text-muted-foreground">
          {categoria}
        </BotonFiltro>
      </div>
    </div>
  );
}

/** Fila de la tabla + su detalle cuando está expandida. Clic en la fila la
 * expande; número, sucursal y tipificación tienen su propia acción. */
export function FilaIncidente({
  incidente,
  estado,
  expandida,
  onAlternar,
}: {
  incidente: Incidente;
  estado: EstadoDashboard;
  expandida: boolean;
  onAlternar: () => void;
}) {
  const Chevron = expandida ? ChevronDown : ChevronRight;
  return (
    <>
      <tr onClick={onAlternar} className={cn("cursor-pointer transition-colors hover:bg-muted/50", expandida && "bg-surface-2")}>
        <td className={cn(TD, "py-2.5 pr-1 pl-3")}>
          <button
            type="button"
            aria-label={expandida ? "Contraer fila" : "Expandir fila"}
            aria-expanded={expandida}
            onClick={(e) => {
              e.stopPropagation();
              onAlternar();
            }}
            className={cn("flex cursor-pointer rounded-[6px] p-1", expandida ? "text-brand-orange" : "text-muted-foreground")}
          >
            <Chevron className="h-4 w-4" aria-hidden="true" />
          </button>
        </td>
        <td className={cn(TD, "whitespace-nowrap")} onClick={detener}>
          <a
            href={`${URL_WEBAGENTES}${incidente.numero}`}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold tabular-nums text-brand-orange hover:underline"
          >
            {incidente.numero}
          </a>
        </td>
        <td className={cn(TD, "whitespace-nowrap tabular-nums")}>{incidente.fecha}</td>
        <td className={TD}>
          {incidente.sucursal ? (
            <BotonFiltro estado={estado} dimension="sucursal" valor={incidente.sucursal}>
              {incidente.sucursal}
            </BotonFiltro>
          ) : (
            "—"
          )}
        </td>
        <td className={TD}>
          <span title={incidente.descripcion}>{recortar(incidente.descripcion)}</span>
        </td>
        <td className={cn(TD, "text-muted-foreground")}>{incidente.causa ?? "—"}</td>
        <td className={TD}>
          <span title={incidente.solucion ?? undefined}>{recortar(incidente.solucion)}</span>
        </td>
        <td className={TD}>
          <CeldaTipificacion incidente={incidente} estado={estado} />
        </td>
      </tr>
      {expandida && (
        <tr className="bg-surface-2">
          <td colSpan={CANTIDAD_COLUMNAS} className="px-4 pb-6 sm:pr-6 sm:pl-14">
            <DetalleIncidente incidente={incidente} estado={estado} />
          </td>
        </tr>
      )}
    </>
  );
}
