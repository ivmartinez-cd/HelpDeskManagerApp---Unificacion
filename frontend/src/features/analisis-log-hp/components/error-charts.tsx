"use client";

import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { useState } from "react";
import { Bar, Line } from "react-chartjs-2";
import type { AnalysisResult, Severity } from "../types/analisis-log-hp";
import { SEV_COLOR, buildFrequencyChartData, buildVolumeChartData, filterIncidentsBySeverity } from "../utils/analysis-utils";

ChartJS.register(
  CategoryScale, LinearScale, BarElement, LineElement, PointElement, Filler, Legend, Tooltip,
);

type VolumeMode = "area" | "barras" | "lineas";

interface Props {
  analysis: AnalysisResult;
  activeSeverities: Set<Severity>;
}

function VolumeChart({ analysis, mode }: { analysis: AnalysisResult; mode: VolumeMode }) {
  const d = buildVolumeChartData(analysis.events);
  if (!d.labels.length) return (
    <div className="h-[180px] flex items-center justify-center text-muted-foreground font-body text-sm">
      Sin datos
    </div>
  );

  const datasets = [
    { label: "ERROR", data: d.errors, backgroundColor: `${SEV_COLOR.ERROR}cc`, borderColor: SEV_COLOR.ERROR, borderWidth: 1.5, fill: mode === "area" },
    { label: "WARNING", data: d.warnings, backgroundColor: `${SEV_COLOR.WARNING}cc`, borderColor: SEV_COLOR.WARNING, borderWidth: 1.5, fill: mode === "area" },
    { label: "INFO", data: d.infos, backgroundColor: `${SEV_COLOR.INFO}cc`, borderColor: SEV_COLOR.INFO, borderWidth: 1.5, fill: mode === "area" },
  ];

  const opts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "bottom" as const, labels: { color: "#9ca3af", font: { size: 10 } } },
      tooltip: {},
    },
    scales: {
      x: {
        stacked: mode !== "lineas",
        ticks: { color: "#9ca3af", font: { size: 9 }, maxRotation: 45 },
        grid: { color: "#ffffff0a" },
      },
      y: {
        stacked: mode !== "lineas",
        ticks: { color: "#9ca3af", font: { size: 9 } },
        grid: { color: "#ffffff0a" },
      },
    },
  };

  if (mode === "barras") return <Bar data={{ labels: d.labels, datasets }} options={opts} />;
  return <Line data={{ labels: d.labels, datasets: datasets.map((ds) => ({ ...ds, tension: 0.3, pointRadius: 2 })) }} options={opts} />;
}

function FrequencyChart({ analysis, activeSeverities }: { analysis: AnalysisResult; activeSeverities: Set<Severity> }) {
  const visible = filterIncidentsBySeverity(analysis.incidents, activeSeverities);
  const d = buildFrequencyChartData(visible);
  if (!d.labels.length) return (
    <div className="h-[180px] flex items-center justify-center text-muted-foreground font-body text-sm">
      Sin incidentes
    </div>
  );

  return (
    <Bar
      data={{
        labels: d.labels,
        datasets: [{ label: "Ocurrencias", data: d.counts, backgroundColor: d.colors, borderRadius: 4, borderWidth: 0 }],
      }}
      options={{
        indexAxis: "y" as const,
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: {} },
        scales: {
          x: { ticks: { color: "#9ca3af", font: { size: 9 } }, grid: { color: "#ffffff0a" } },
          y: { ticks: { color: "#e5e7eb", font: { family: "monospace", size: 10 } }, grid: { display: false } },
        },
      }}
    />
  );
}

export function ErrorCharts({ analysis, activeSeverities }: Props) {
  const [mode, setMode] = useState<VolumeMode>("area");
  const modes: { v: VolumeMode; l: string }[] = [
    { v: "area", l: "Área" },
    { v: "barras", l: "Barras" },
    { v: "lineas", l: "Líneas" },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      {/* Volumen temporal */}
      <div className="rounded-[12px] border border-border bg-card p-4 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="font-heading text-[13px] font-bold text-foreground">
            Volumen de incidencias (registro completo)
          </span>
          <div className="flex gap-1">
            {modes.map(({ v, l }) => (
              <button
                key={v}
                type="button"
                onClick={() => setMode(v)}
                className="rounded-md px-2 py-0.5 font-body text-[11px] transition-colors"
                style={{
                  background: mode === v ? "#F7941D22" : "transparent",
                  color: mode === v ? "#F7941D" : "#6b7280",
                }}
              >
                {l}
              </button>
            ))}
          </div>
        </div>
        <div className="h-[180px]">
          <VolumeChart analysis={analysis} mode={mode} />
        </div>
      </div>

      {/* Errores más frecuentes */}
      <div className="rounded-[12px] border border-border bg-card p-4 flex flex-col gap-3">
        <span className="font-heading text-[13px] font-bold text-foreground">
          Errores más frecuentes
        </span>
        <div className="h-[180px]">
          <FrequencyChart analysis={analysis} activeSeverities={activeSeverities} />
        </div>
      </div>
    </div>
  );
}
