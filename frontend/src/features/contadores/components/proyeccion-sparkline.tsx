"use client";

import { useMemo } from "react";
import { BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip } from "chart.js";
import { Bar } from "react-chartjs-2";

/** Mini gráfico de barras de 12 meses de la grilla de Proyección — 11 meses
 * de histórico real + el mes actual (estimado), como describe la sección UX
 * del tablero principal. Sin línea de referencia punteada ni "overflow
 * indicator" (`chartjs-plugin-annotation` no está en el proyecto y no vale
 * la pena sumarlo por un detalle de un sparkline chico) — se puede agregar
 * después si hace falta. */

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

const AZUL_HISTORICO = "#60a5fa";
const ROJO_ACTUAL = "rgba(239, 68, 68, .65)";

interface ProyeccionSparklineProps {
  historico12: number[];
}

export function ProyeccionSparkline({ historico12 }: ProyeccionSparklineProps) {
  const data = useMemo(() => {
    const valores = historico12.length === 12 ? historico12 : Array(12).fill(0);
    return {
      labels: valores.map((_, i) => String(i)),
      datasets: [
        {
          data: valores,
          backgroundColor: valores.map((_, i) => (i === 11 ? ROJO_ACTUAL : AZUL_HISTORICO)),
          borderRadius: 1,
        },
      ],
    };
  }, [historico12]);

  return (
    <div style={{ width: 92, height: 32 }}>
      <Bar
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
