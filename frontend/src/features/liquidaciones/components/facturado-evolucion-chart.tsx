"use client";

import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from "chart.js";
import { useMemo } from "react";
import { Bar } from "react-chartjs-2";
import type { FacturadoPorPeriodoItem } from "../types/liquidaciones";
import { formatARS } from "../lib/format";

ChartJS.register(CategoryScale, LinearScale, BarElement, Legend, Tooltip);

const mesFormat = new Intl.DateTimeFormat("es-AR", { month: "short", year: "2-digit" });

function labelPeriodo(periodo: string): string {
  const [anio, mes] = periodo.split("-").map(Number);
  if (!anio || !mes) return periodo;
  return mesFormat.format(new Date(anio, mes - 1, 1));
}

export function FacturadoEvolucionChart({ items }: { items: FacturadoPorPeriodoItem[] }) {
  const { periodos, data } = useMemo(() => {
    // Mismo criterio que evolucion-incidentes-chart: año en curso, no el
    // histórico completo (arranca en 2015 y hace ilegible el gráfico).
    const anioActual = new Date().getFullYear();
    const delAnio = items.filter((i) => i.periodo.startsWith(`${anioActual}-`));
    const periodos = [...new Set(delAnio.map((i) => i.periodo))].sort();
    const porPeriodo = Object.fromEntries(delAnio.map((i) => [i.periodo, i.totalImporte]));
    return { periodos, data: periodos.map((p) => porPeriodo[p] ?? 0) };
  }, [items]);

  if (periodos.length < 2) {
    return (
      <p className="font-body text-sm text-muted-foreground">
        Todavía no hay suficientes meses cargados este año.
      </p>
    );
  }

  return (
    <div className="h-[220px]">
      <Bar
        data={{
          labels: periodos.map(labelPeriodo),
          datasets: [
            {
              label: "Total facturado",
              data,
              backgroundColor: "#F7941D",
              borderRadius: 2,
              borderWidth: 0,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (contexto) => formatARS(contexto.parsed.y as number),
              },
            },
          },
          scales: {
            x: {
              ticks: { color: "#9ca3af", font: { size: 9 } },
              grid: { display: false },
            },
            y: {
              beginAtZero: true,
              ticks: {
                color: "#9ca3af",
                font: { size: 9 },
                callback: (value) => formatARS(Number(value)),
              },
              grid: { color: "#e5e7eb33" },
            },
          },
        }}
      />
    </div>
  );
}
