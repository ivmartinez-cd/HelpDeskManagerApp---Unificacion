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
import { labelTipo } from "../lib/tarifarios-matriz";
import type { EvolucionIncidentesItem } from "../types/liquidaciones";

ChartJS.register(CategoryScale, LinearScale, BarElement, Legend, Tooltip);

// Excepción de marca puntual para este gráfico (2026-09-09, pedido de Iván):
// con 6+ tipos de incidente un solo matiz no alcanza para distinguirlos — la
// escala naranja-monocromática que se probó antes era ilegible en la
// práctica. En vez de forzar 6 colores (chocaba con dos reglas ya fijadas:
// rojo/amarillo/verde reservados para semaforización de estado, y magenta/
// violeta/celeste vetados por ser las otras 3 líneas de Canal Directo — no
// sobra espacio de matices seguro para 6 categorías bien separadas), se
// valida con `dataviz/scripts/validate_palette.js` un set de 3 colores bien
// distinguibles (naranja de marca + azul + verde azulado, ninguno de los 3
// tonos vetados/reservados) para los tipos más frecuentes, y el resto de los
// tipos (incluido cualquier valor crudo del CSV sin catalogar) se agrupa en
// "Otros" en gris neutro — el desglose real de "Otros" se ve en el tooltip.
const TIPOS_PRINCIPALES: { tipo: string; color: string }[] = [
  { tipo: "correctivo", color: "#F7941D" },
  { tipo: "preventivo", color: "#2A78D6" },
  { tipo: "instalacion_desinstalacion", color: "#1BAF7A" },
];
const COLOR_OTROS = "#9CA3AF";

const mesFormat = new Intl.DateTimeFormat("es-AR", { month: "short", year: "2-digit" });

function labelPeriodo(periodo: string): string {
  const [anio, mes] = periodo.split("-").map(Number);
  if (!anio || !mes) return periodo;
  return mesFormat.format(new Date(anio, mes - 1, 1));
}

export function EvolucionIncidentesChart({ items }: { items: EvolucionIncidentesItem[] }) {
  const { periodos, datasets, otrosPorPeriodo } = useMemo(() => {
    // Pedido de gerencia: solo el año en curso, no el histórico completo del
    // prestador (que en prestadores viejos arranca en 2015 y hace ilegible
    // el gráfico).
    const anioActual = new Date().getFullYear();
    const delAnio = items.filter((i) => i.periodo.startsWith(`${anioActual}-`));

    const periodos = [...new Set(delAnio.map((i) => i.periodo))].sort();
    const tiposPrincipalesSet = new Set(TIPOS_PRINCIPALES.map((t) => t.tipo));

    const cantidadPor: Record<string, Record<string, number>> = {};
    // Detalle real de "Otros" por período — para desglosarlo en el tooltip
    // en vez de esconder qué tipos lo componen.
    const otrosPorPeriodo: Record<string, { tipo: string; cantidad: number }[]> = {};
    for (const it of delAnio) {
      if (tiposPrincipalesSet.has(it.tipo)) {
        (cantidadPor[it.tipo] ??= {})[it.periodo] = it.cantidad;
      } else {
        (otrosPorPeriodo[it.periodo] ??= []).push({ tipo: it.tipo, cantidad: it.cantidad });
      }
    }

    const datasets = TIPOS_PRINCIPALES.filter(({ tipo }) =>
      delAnio.some((i) => i.tipo === tipo),
    ).map(({ tipo, color }) => ({
      label: labelTipo(tipo),
      data: periodos.map((p) => cantidadPor[tipo]?.[p] ?? 0),
      backgroundColor: color,
      borderRadius: 2,
      borderWidth: 0,
    }));

    if (Object.keys(otrosPorPeriodo).length > 0) {
      datasets.push({
        label: "Otros",
        data: periodos.map((p) =>
          (otrosPorPeriodo[p] ?? []).reduce((s, x) => s + x.cantidad, 0),
        ),
        backgroundColor: COLOR_OTROS,
        borderRadius: 2,
        borderWidth: 0,
      });
    }

    return { periodos, datasets, otrosPorPeriodo };
  }, [items]);

  if (periodos.length < 2) {
    return (
      <p className="font-body text-sm text-muted-foreground">
        Todavía no hay suficientes meses cargados este año para este prestador.
      </p>
    );
  }

  return (
    <div className="h-[220px]">
      <Bar
        data={{ labels: periodos.map(labelPeriodo), datasets }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom" as const,
              labels: { color: "#9ca3af", font: { size: 10 }, boxWidth: 10 },
            },
            tooltip: {
              callbacks: {
                label: (contexto) => {
                  const base = `${contexto.dataset.label}: ${contexto.parsed.y}`;
                  if (contexto.dataset.label !== "Otros") return base;
                  const periodo = periodos[contexto.dataIndex];
                  const detalle = (otrosPorPeriodo[periodo] ?? [])
                    .map((x) => `${labelTipo(x.tipo)} ${x.cantidad}`)
                    .join(", ");
                  return detalle ? `${base} (${detalle})` : base;
                },
                footer: (contexto) => {
                  const total = contexto.reduce((s, c) => s + (c.parsed.y as number), 0);
                  return `Total del mes: ${total}`;
                },
              },
            },
          },
          scales: {
            x: {
              stacked: true,
              ticks: { color: "#9ca3af", font: { size: 9 } },
              grid: { display: false },
            },
            y: {
              stacked: true,
              beginAtZero: true,
              ticks: { color: "#9ca3af", font: { size: 9 }, precision: 0 },
              grid: { color: "#e5e7eb33" },
            },
          },
        }}
      />
    </div>
  );
}
