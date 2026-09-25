"use client";

import { useMemo } from "react";
import { BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip, type ChartOptions } from "chart.js";
import { Bar } from "react-chartjs-2";
import { formatearEntero } from "../../../lib/periodos";
import { useTemaGrafico } from "./use-tema-grafico";
import { ALFA_ATENUADO, conAlfa } from "./utilidades";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

export interface Barra {
  nombre: string;
  cantidad: number;
  color: string;
  /** Línea extra del tooltip (p. ej. la categoría de una subcategoría). */
  detalle?: string;
}

interface Props {
  barras: Barra[];
  /** Valor filtrado actualmente: el resto se atenúa. */
  activa: string;
  alto: number;
  grosor: number;
  /** Recorte de la etiqueta del eje (el nombre completo va en el tooltip). */
  etiqueta: (nombre: string) => string;
  onClick?: (nombre: string) => void;
  /** Colores de papel fijos (PDF), sin importar el tema. */
  claro?: boolean;
}

/** Barras horizontales compartidas por subcategorías y sucursales. */
export function BarrasHorizontales({ barras, activa, alto, grosor, etiqueta, onClick, claro }: Props) {
  const tema = useTemaGrafico(claro);

  const options = useMemo<ChartOptions<"bar">>(
    () => ({
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      // En el PDF el canvas se copia como imagen: el doble de resolución no se pixela al imprimir.
      devicePixelRatio: claro ? 2 : undefined,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => barras[items[0]?.dataIndex ?? 0]?.nombre ?? "",
            label: (ctx) => {
              const barra = barras[ctx.dataIndex];
              const linea = `${formatearEntero(Number(ctx.raw))} incidentes`;
              return barra?.detalle ? [barra.detalle, linea] : linea;
            },
          },
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: { color: tema.grilla },
          border: { display: false },
          ticks: { color: tema.texto, font: { size: 11 }, precision: 0 },
        },
        y: {
          grid: { display: false },
          border: { display: false },
          ticks: {
            color: tema.texto,
            font: { size: 12 },
            autoSkip: false,
            callback: (_valor, indice) => etiqueta(barras[indice]?.nombre ?? ""),
          },
        },
      },
      onClick: (_evento, elementos) => {
        const nombre = barras[elementos[0]?.index ?? -1]?.nombre;
        if (onClick && nombre) onClick(nombre);
      },
      onHover: (evento, elementos) => {
        const destino = evento.native?.target as HTMLElement | undefined;
        if (destino) destino.style.cursor = onClick && elementos.length ? "pointer" : "default";
      },
    }),
    [tema, barras, etiqueta, onClick, claro],
  );

  return (
    <div className="relative px-5 pb-5 pt-4" style={{ height: alto + 36 }}>
      <Bar
        options={options}
        data={{
          labels: barras.map((b) => b.nombre),
          datasets: [
            {
              data: barras.map((b) => b.cantidad),
              backgroundColor: barras.map((b) =>
                activa && activa !== b.nombre ? conAlfa(b.color, ALFA_ATENUADO) : b.color,
              ),
              borderRadius: 4,
              barThickness: grosor,
            },
          ],
        }}
      />
    </div>
  );
}
