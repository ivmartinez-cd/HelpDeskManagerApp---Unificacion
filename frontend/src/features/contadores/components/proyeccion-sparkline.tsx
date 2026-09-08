"use client";

import { useMemo } from "react";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { Chart } from "react-chartjs-2";

/** Mini gráfico de barras de 12 meses de la grilla de Proyección — 11 meses
 * de histórico real + el mes actual (estimado), paridad con `BarChart.razor`
 * legacy: línea punteada roja al nivel del mes actual, para comparar de un
 * vistazo contra el histórico (mixed chart bar+line, nativo de chart.js —
 * no hace falta `chartjs-plugin-annotation`). */

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, LineController, Tooltip);

const AZUL_HISTORICO = "#60a5fa";
const ROJO_ACTUAL = "rgba(239, 68, 68, .65)";
const ROJO_LINEA = "#dc2626";

interface ProyeccionSparklineProps {
  historico12: number[];
}

export function ProyeccionSparkline({ historico12 }: ProyeccionSparklineProps) {
  const data = useMemo(() => {
    const valores = historico12.length === 12 ? historico12 : Array(12).fill(0);
    const actual = valores[11];
    return {
      labels: valores.map((_, i) => String(i)),
      datasets: [
        {
          type: "bar" as const,
          data: valores,
          backgroundColor: valores.map((_, i) => (i === 11 ? ROJO_ACTUAL : AZUL_HISTORICO)),
          borderRadius: 1,
          order: 2,
        },
        {
          type: "line" as const,
          data: Array(12).fill(actual),
          borderColor: ROJO_LINEA,
          borderWidth: 1.2,
          borderDash: [3, 3],
          pointRadius: 0,
          tension: 0,
          order: 1,
        },
      ],
    };
  }, [historico12]);

  return (
    <div style={{ width: 92, height: 32 }}>
      <Chart
        type="bar"
        data={data}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: {
            x: { display: false },
            y: { display: false, beginAtZero: true },
          },
        }}
      />
    </div>
  );
}
