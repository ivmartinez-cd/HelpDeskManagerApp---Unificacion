"use client";

import { useMemo } from "react";
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  type ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";
import type { Reporte } from "../../../types/reporte";
import { etiquetaDia, formatearEntero } from "../../../lib/periodos";
import { SinDatos, TarjetaGrafico } from "./tarjeta-grafico";
import { useTemaGrafico } from "./use-tema-grafico";
import { NARANJA } from "./utilidades";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);

interface Props {
  reporte: Reporte;
  alto?: number;
  /** Colores de papel fijos (PDF), sin importar el tema. */
  claro?: boolean;
}

/** Incidentes por día de la selección filtrada (port de `Timeline`). Con más
 * de un mes el eje pasa a "dd/MM" para poder ubicar el pico (el PDF no tiene
 * tooltip que lo aclare). */
export function GraficoEvolucion({ reporte, claro, alto = 220 }: Props) {
  const tema = useTemaGrafico(claro);
  const variosMeses = reporte.meses > 1;
  const serie = reporte.evolucion;

  const options = useMemo<ChartOptions<"line">>(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      // En el PDF el canvas se copia como imagen: el doble de resolución no se pixela al imprimir.
      devicePixelRatio: claro ? 2 : undefined,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => serie[items[0]?.dataIndex ?? 0]?.nombre ?? "",
            label: (ctx) => `${formatearEntero(Number(ctx.raw))} incidentes`,
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: tema.texto, font: { size: 11 }, maxRotation: 0, autoSkip: true, autoSkipPadding: variosMeses ? 24 : 8 },
        },
        y: {
          beginAtZero: true,
          grid: { color: tema.grilla },
          border: { display: false },
          ticks: { color: tema.texto, font: { size: 11 }, precision: 0 },
        },
      },
    }),
    [tema, serie, variosMeses, claro],
  );

  return (
    <TarjetaGrafico
      titulo={variosMeses ? "Evolución diaria del período" : "Evolución diaria del mes"}
      derecha="incidentes / día"
    >
      {serie.length === 0 ? (
        <SinDatos />
      ) : (
        <div className="relative px-5 pb-4 pt-4" style={{ height: alto + 32 }}>
          <Line
            options={options}
            data={{
              labels: serie.map((d) => etiquetaDia(d.nombre, variosMeses)),
              datasets: [
                {
                  data: serie.map((d) => d.cantidad),
                  borderColor: NARANJA,
                  backgroundColor: "rgba(247,148,29,.12)",
                  fill: true,
                  tension: 0.35,
                  borderWidth: 2,
                  pointRadius: 0,
                  pointHoverRadius: 4,
                  pointBackgroundColor: NARANJA,
                },
              ],
            }}
          />
        </div>
      )}
    </TarjetaGrafico>
  );
}
