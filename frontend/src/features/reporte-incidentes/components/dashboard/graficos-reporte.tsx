"use client";

import { useMemo } from "react";
import dynamic from "next/dynamic";
import type { DimensionFiltro, Filtros, Reporte } from "../../types/reporte";

// chart.js fuera del bundle inicial (mismo criterio que trend-chart-lazy).
function Esqueleto({ alto }: { alto: number }) {
  return <div className="animate-pulse rounded-[12px] border border-border bg-card" style={{ height: alto }} />;
}

const GraficoEvolucion = dynamic(
  () => import("./graficos/grafico-evolucion").then((m) => m.GraficoEvolucion),
  { ssr: false, loading: () => <Esqueleto alto={320} /> },
);
const GraficoCategorias = dynamic(
  () => import("./graficos/grafico-categorias").then((m) => m.GraficoCategorias),
  { ssr: false, loading: () => <Esqueleto alto={420} /> },
);
const GraficoSubcategorias = dynamic(
  () => import("./graficos/grafico-subcategorias").then((m) => m.GraficoSubcategorias),
  { ssr: false, loading: () => <Esqueleto alto={420} /> },
);
const GraficoSucursales = dynamic(
  () => import("./graficos/grafico-sucursales").then((m) => m.GraficoSucursales),
  { ssr: false, loading: () => <Esqueleto alto={340} /> },
);

interface Props {
  reporte: Reporte;
  filtros: Filtros;
  onFiltrar: (dimension: DimensionFiltro, valor: string) => void;
}

/** Evolución a lo ancho, dona + subcategorías lado a lado y sucursales a lo
 * ancho (layout del legacy). Salvo la evolución, muestran el período completo
 * y actúan de navegador: tocar un valor lo filtra, tocarlo de nuevo lo quita. */
export function GraficosReporte({ reporte, filtros, onFiltrar }: Props) {
  const vista = useMemo(() => ({ ...reporte, filtros }), [reporte, filtros]);
  return (
    <div className="flex flex-col gap-5">
      <GraficoEvolucion reporte={vista} />
      <div className="grid gap-5 xl:grid-cols-2">
        <GraficoCategorias reporte={vista} onFiltrar={onFiltrar} />
        <GraficoSubcategorias reporte={vista} onFiltrar={onFiltrar} />
      </div>
      <GraficoSucursales reporte={vista} onFiltrar={onFiltrar} />
    </div>
  );
}
