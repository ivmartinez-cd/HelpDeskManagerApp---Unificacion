"use client";

import { useMemo } from "react";
import { ArcElement, Chart as ChartJS, Tooltip, type ChartOptions } from "chart.js";
import { Doughnut } from "react-chartjs-2";
import { cn } from "@/shared/utils/cn";
import type { DimensionFiltro, Reporte } from "../../../types/reporte";
import { formatearEntero } from "../../../lib/periodos";
import { SinDatos, TarjetaGrafico } from "./tarjeta-grafico";
import { useTemaGrafico } from "./use-tema-grafico";
import { ALFA_ATENUADO, colorCategoria, conAlfa } from "./utilidades";

ChartJS.register(ArcElement, Tooltip);

interface Props {
  reporte: Reporte;
  onFiltrar?: (dimension: DimensionFiltro, valor: string) => void;
  alto?: number;
  /** Colores de papel fijos (PDF), sin importar el tema. */
  claro?: boolean;
}

/** Dona de categorías del período completo + leyenda (port de `CategoryDonut`).
 * Con `onFiltrar`, tocar un sector o una fila de la leyenda filtra; sin él
 * (PDF) es solo lectura. */
export function GraficoCategorias({ reporte, onFiltrar, claro, alto = 200 }: Props) {
  const tema = useTemaGrafico(claro);
  const datos = reporte.categorias;
  const total = datos.reduce((s, d) => s + d.cantidad, 0);
  const activa = reporte.filtros.categoria;
  const color = (nombre: string) => {
    const base = colorCategoria(reporte, nombre);
    return activa && activa !== nombre ? conAlfa(base, ALFA_ATENUADO) : base;
  };

  const options = useMemo<ChartOptions<"doughnut">>(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      // En el PDF el canvas se copia como imagen: el doble de resolución no se pixela al imprimir.
      devicePixelRatio: claro ? 2 : undefined,
      cutout: "68%",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const valor = Number(ctx.raw);
              const pct = total ? Math.round((valor / total) * 100) : 0;
              return `${formatearEntero(valor)} incidentes · ${pct}%`;
            },
          },
        },
      },
      onClick: (_evento, elementos) => {
        const nombre = datos[elementos[0]?.index ?? -1]?.nombre;
        if (onFiltrar && nombre) onFiltrar("categoria", nombre);
      },
      onHover: (evento, elementos) => {
        const destino = evento.native?.target as HTMLElement | undefined;
        if (destino) destino.style.cursor = onFiltrar && elementos.length ? "pointer" : "default";
      },
    }),
    [datos, total, onFiltrar, claro],
  );

  return (
    <TarjetaGrafico titulo="Incidentes por categoría" subtitulo="Período completo" derecha={`${formatearEntero(total)} total`}>
      {total === 0 ? (
        <SinDatos />
      ) : (
        <div className="flex flex-col items-center gap-6 px-6 py-5 sm:flex-row">
          <div className="relative flex-none" style={{ width: alto, height: alto }}>
            <Doughnut
              options={options}
              data={{
                labels: datos.map((d) => d.nombre),
                datasets: [
                  {
                    data: datos.map((d) => d.cantidad),
                    backgroundColor: datos.map((d) => color(d.nombre)),
                    borderColor: tema.fondo,
                    borderWidth: 2,
                  },
                ],
              }}
            />
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-heading text-[26px] font-extrabold leading-none text-foreground">
                {formatearEntero(total)}
              </span>
              <span className="font-body text-xs text-muted-foreground">incidentes</span>
            </div>
          </div>
          <ul className="flex w-full min-w-0 flex-1 flex-col gap-0.5">
            {datos.map((d) => (
              <li key={d.nombre}>
                <FilaLeyenda
                  nombre={d.nombre}
                  color={colorCategoria(reporte, d.nombre)}
                  cantidad={d.cantidad}
                  pct={total ? Math.round((d.cantidad / total) * 100) : 0}
                  activa={activa === d.nombre}
                  atenuada={Boolean(activa) && activa !== d.nombre}
                  onClick={onFiltrar && (() => onFiltrar("categoria", d.nombre))}
                />
              </li>
            ))}
          </ul>
        </div>
      )}
    </TarjetaGrafico>
  );
}

interface FilaLeyendaProps {
  nombre: string;
  color: string;
  cantidad: number;
  pct: number;
  activa: boolean;
  atenuada: boolean;
  onClick?: () => void;
}

function FilaLeyenda({ nombre, color, cantidad, pct, activa, atenuada, onClick }: FilaLeyendaProps) {
  const contenido = (
    <>
      <span className="h-2.5 w-2.5 flex-none rounded-[3px]" style={{ background: color }} aria-hidden="true" />
      <span className="min-w-0 flex-1 truncate font-body text-[13px] text-foreground">{nombre}</span>
      <span className="font-body text-[13px] font-bold tabular-nums text-foreground">{formatearEntero(cantidad)}</span>
      <span className="w-[44px] text-right font-body text-xs tabular-nums text-muted-foreground">{pct}%</span>
    </>
  );
  const clases = cn(
    "flex w-full items-center gap-2.5 rounded-[8px] px-2 py-1.5 text-left",
    atenuada && "opacity-40",
    activa && "bg-brand-orange/10 ring-1 ring-brand-orange/40",
  );
  if (!onClick) return <div className={clases}>{contenido}</div>;
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={activa}
      title={activa ? "Quitar filtro" : `Filtrar por ${nombre}`}
      className={cn(clases, "cursor-pointer transition-colors hover:bg-muted")}
    >
      {contenido}
    </button>
  );
}
