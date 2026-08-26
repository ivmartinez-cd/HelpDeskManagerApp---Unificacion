"use client";

import dynamic from "next/dynamic";

// chart.js (via react-chartjs-2) fuera del bundle inicial de las 3 pantallas
// que usan este primitivo (estadísticas, cliente, detalle de consumible) --
// mismo criterio que sla-mes-card.tsx en el dashboard de Inicio.
export const TrendChart = dynamic(() => import("./trend-chart").then((m) => m.TrendChart), {
  ssr: false,
  loading: () => <div className="h-80 animate-pulse rounded-[12px] border border-border bg-card" />,
});
