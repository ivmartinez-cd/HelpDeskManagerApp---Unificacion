"use client";

import type { ReactNode } from "react";
import { MapPin } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { DimensionFiltro, Reporte } from "../../types/reporte";
import { formatearEntero } from "../../lib/periodos";
import { TarjetaGrafico } from "./graficos/tarjeta-grafico";
import { categoriaDe, colorCategoria, formatearPct } from "./graficos/utilidades";

interface Props {
  reporte: Reporte;
  onFiltrar: (dimension: DimensionFiltro, valor: string) => void;
}

const ETIQUETA = "font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground";

/** "Oportunidades de Mejora" (port de `FocusPanel`): titular con los casos
 * cerrados sin reparar el equipo, su desglose por motivo y el resto de las
 * causas fuera del equipo. Período completo; cada fila filtra el reporte. */
export function OportunidadesMejora({ reporte, onFiltrar }: Props) {
  const op = reporte.oportunidades;
  if (op.fuera_del_equipo_total === 0) return null;
  const activa = reporte.filtros.subcategoria;
  // UNA sola escala para las dos columnas: si cada una se escalara contra su
  // propio máximo, dos barras iguales representarían valores distintos.
  const maximo = Math.max(op.sin_reparacion_items[0]?.cantidad ?? 0, op.items[0]?.cantidad ?? 0);

  return (
    <TarjetaGrafico
      titulo="Oportunidades de Mejora"
      subtitulo="Período completo, sin filtros. Cada fila filtra el resto del reporte."
      derecha={
        <>
          <strong className="text-foreground">{formatearEntero(op.fuera_del_equipo_total)}</strong> de{" "}
          {formatearEntero(op.total)} incidentes ({formatearPct(op.fuera_del_equipo_pct)}) fuera del equipo
        </>
      }
    >
      <div className="grid gap-6 px-6 pb-6 pt-5 lg:grid-cols-[300px_minmax(0,1fr)_minmax(0,1.35fr)]">
        {op.sin_reparacion_total > 0 && (
          <div className="flex flex-col gap-2 rounded-[10px] bg-muted p-5">
            <span className={ETIQUETA}>Sin reparación</span>
            <span className="font-heading text-[40px] font-extrabold leading-none text-brand-orange">
              {formatearEntero(op.sin_reparacion_total)}
            </span>
            <p className="font-body text-[15px] font-bold text-foreground">casos se cerraron sin reparar el equipo</p>
            <p className="font-body text-[13px] leading-relaxed text-muted-foreground">
              El {formatearPct(op.sin_reparacion_pct)} de los {formatearEntero(op.total)} incidentes del
              período. La impresora estaba operativa: no se encontró falla, se resolvió con un instructivo o
              el problema estaba en la PC del puesto.
            </p>
          </div>
        )}

        {op.sin_reparacion_items.length > 0 && (
          <Columna titulo="Por motivo">
            {op.sin_reparacion_items.map((item) => (
              <Fila
                key={item.subcategoria}
                nombre={item.subcategoria}
                color={colorCategoria(reporte, categoriaDe(reporte, item.subcategoria))}
                cantidad={item.cantidad}
                pct={item.pct}
                maximo={maximo}
                activa={activa === item.subcategoria}
                onClick={() => onFiltrar("subcategoria", item.subcategoria)}
              />
            ))}
          </Columna>
        )}

        {op.items.length > 0 && (
          <Columna titulo="Otras causas fuera del equipo">
            {op.items.map((item) => (
              <Fila
                key={item.subcategoria}
                nombre={item.subcategoria}
                color={colorCategoria(reporte, item.categoria)}
                cantidad={item.cantidad}
                pct={item.pct}
                maximo={maximo}
                activa={activa === item.subcategoria}
                onClick={() => onFiltrar("subcategoria", item.subcategoria)}
                insignia={
                  // Como el legacy: la sucursal sale solo cuando concentra los casos;
                  // "repartido" es lo normal y no aporta información.
                  item.concentrado && (
                    <span
                      title={`${item.sucursal_principal} · ${formatearPct(item.sucursal_principal_pct)}`}
                      className="flex max-w-[50%] items-center gap-1 rounded-full bg-warning/10 px-2 py-0.5 font-body text-[11px] font-bold text-warning"
                    >
                      <MapPin className="h-3 w-3 flex-none" aria-hidden="true" />
                      <span className="truncate">{item.sucursal_principal}</span>
                      <span className="flex-none">· {formatearPct(item.sucursal_principal_pct)}</span>
                    </span>
                  )
                }
              />
            ))}
          </Columna>
        )}
      </div>
    </TarjetaGrafico>
  );
}

function Columna({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <p className={cn(ETIQUETA, "px-2.5 pb-1")}>{titulo}</p>
      {children}
    </div>
  );
}

interface FilaProps {
  nombre: string;
  color: string;
  cantidad: number;
  pct: number;
  maximo: number;
  activa: boolean;
  onClick: () => void;
  insignia?: ReactNode;
}

function Fila({ nombre, color, cantidad, pct, maximo, activa, onClick, insignia }: FilaProps) {
  const ancho = maximo > 0 ? (cantidad / maximo) * 100 : 0;
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={activa}
      title={activa ? "Quitar filtro" : `Filtrar por ${nombre}`}
      className={cn(
        "flex w-full cursor-pointer flex-col gap-1.5 rounded-[8px] px-2.5 py-2 text-left transition-colors hover:bg-muted",
        activa && "bg-brand-orange/10 ring-1 ring-brand-orange/40",
      )}
    >
      <span className="flex w-full items-center gap-2">
        <span className="h-2 w-2 flex-none rounded-[2px]" style={{ background: color }} aria-hidden="true" />
        <span className="min-w-0 flex-1 truncate font-body text-[13px] font-semibold text-foreground">{nombre}</span>
        {insignia}
        <span className="font-body text-[13px] font-bold tabular-nums text-foreground">{formatearEntero(cantidad)}</span>
        <span className="w-[52px] text-right font-body text-xs tabular-nums text-muted-foreground">
          {formatearPct(pct)}
        </span>
      </span>
      <span className="block h-1.5 w-full rounded-[3px] bg-foreground/10" aria-hidden="true">
        <span className="block h-1.5 rounded-[3px]" style={{ width: `${ancho}%`, background: color }} />
      </span>
    </button>
  );
}
