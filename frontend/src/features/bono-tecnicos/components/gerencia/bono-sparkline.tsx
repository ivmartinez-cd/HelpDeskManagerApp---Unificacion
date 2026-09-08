"use client";

import { useMemo } from "react";
import { BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip } from "chart.js";
import { Bar } from "react-chartjs-2";

/** Mini gráfico de 12 barras con el puntaje mensual de un técnico, para la
 * columna "Últimos 12 meses" del ranking de gerencia — mismo recurso que
 * `contadores/components/proyeccion-sparkline.tsx`, sin ejes ni tooltip. */

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

const NARANJA = "#F7941D";
const GRIS = "rgba(88, 89, 91, .35)";

interface BonoSparklineProps {
  puntajes: (number | null)[];
}

export function BonoSparkline({ puntajes }: BonoSparklineProps) {
  const data = useMemo(() => {
    const valores = puntajes.map((v) => v ?? 0);
    return {
      labels: valores.map((_, i) => String(i)),
      datasets: [
        {
          data: valores,
          backgroundColor: puntajes.map((v) => (v === null ? GRIS : NARANJA)),
          borderRadius: 1,
        },
      ],
    };
  }, [puntajes]);

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
