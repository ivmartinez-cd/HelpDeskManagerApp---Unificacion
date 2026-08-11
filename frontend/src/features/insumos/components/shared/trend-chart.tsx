"use client";

import { useMemo } from "react";
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  type ChartData,
  type ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { cn } from "@/shared/utils/cn";

/** Gráfico de tendencia del Patrón 2 del handoff, sobre Chart.js 4.4 +
 * react-chartjs-2 (el handoff pide Chart.js explícitamente, no ApexCharts).
 *
 * Decisiones tomadas acá para no sumar dependencias:
 *  - Las anotaciones (reposición / falla) NO usan `chartjs-plugin-annotation`:
 *    van como datasets extra de puntos superpuestos, como sugiere el propio
 *    README del handoff. Se implementan como datasets `line` con
 *    `showLine: false` en vez de `scatter` — se ve igual (solo los puntos) y
 *    evita registrar un segundo controller y tipar un chart mixto.
 *  - El magenta `#E32D91` que el handoff proponía para las anotaciones de
 *    reposición está PROHIBIDO en este proyecto (no es línea Institucional de
 *    Canal Directo): las anotaciones usan naranja `#F7941D` por default y rojo
 *    `#ef4444` para las de falla.
 */

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const ORANGE = "#F7941D";
const GRAY = "#58595B";
const RED = "#ef4444";

/** Un punto marcado sobre la serie principal (reposición, falla, etc.). */
export interface TrendAnnotation {
  /** Índice dentro de `labels` donde cae la marca. */
  index: number;
  /** Valor en el eje Y. Normalmente el mismo `values[index]`. */
  value: number;
  /** Naranja para eventos operativos, rojo para fallas. */
  tone?: "orange" | "red";
  /** Texto que reemplaza al label del dataset en el tooltip de esa marca. */
  label?: string;
}

/** Una opción del selector de período (pills naranjas del handoff). */
export interface TrendPeriodOption {
  key: string;
  label: string;
}

interface TrendChartProps {
  /** Etiquetas del eje X, ya formateadas (ver `utils/format.formatDayLabel`). */
  labels: string[];
  /** Serie principal — línea naranja con fill. */
  values: (number | null)[];
  seriesLabel?: string;
  /** Serie de proyección opcional — gris punteada, sin fill. Usar `null` en
   * los índices donde todavía no arranca la proyección. */
  projection?: (number | null)[] | null;
  projectionLabel?: string;
  annotations?: TrendAnnotation[];
  /** Selector de período. Si no se pasa, no se renderiza. */
  periods?: TrendPeriodOption[];
  activePeriod?: string;
  onPeriodChange?: (key: string) => void;
  title?: string;
  subtitle?: string;
  /** Alto del canvas en px (el handoff usa 320). */
  heightPx?: number;
  /** Formateador del valor en tooltips y eje Y. */
  formatValue?: (value: number) => string;
  className?: string;
}

const defaultFormatValue = (value: number) => value.toLocaleString("es-AR");

export function TrendChart({
  labels,
  values,
  seriesLabel = "Pedidos",
  projection = null,
  projectionLabel = "Proyección",
  annotations,
  periods,
  activePeriod,
  onPeriodChange,
  title,
  subtitle,
  heightPx = 320,
  formatValue = defaultFormatValue,
  className,
}: TrendChartProps) {
  const marks = useMemo(() => annotations ?? [], [annotations]);

  const data = useMemo<ChartData<"line", (number | null)[]>>(() => {
    const datasets: ChartData<"line", (number | null)[]>["datasets"] = [
      {
        label: seriesLabel,
        data: values,
        borderColor: ORANGE,
        backgroundColor: "rgba(247,148,29,.08)",
        fill: true,
        tension: 0.4,
        borderWidth: 2,
        pointBackgroundColor: ORANGE,
        // Con muchos días la línea se vuelve un collar de puntos: se ocultan.
        pointRadius: values.length > 45 ? 0 : 3,
        pointHoverRadius: 5,
      },
    ];

    if (projection) {
      datasets.push({
        label: projectionLabel,
        data: projection,
        borderColor: GRAY,
        backgroundColor: "transparent",
        borderDash: [6, 4],
        fill: false,
        tension: 0.4,
        borderWidth: 2,
        pointBackgroundColor: GRAY,
        pointRadius: 3,
      });
    }

    for (const tone of ["orange", "red"] as const) {
      const toneMarks = marks.filter((mark) => (mark.tone ?? "orange") === tone);
      if (toneMarks.length === 0) continue;
      datasets.push({
        label: tone === "red" ? "Falla" : "Reposición",
        // Eje de categorías: alcanza con un array alineado a `labels` que
        // tenga valor solo en los índices anotados (el resto va `null`).
        data: labels.map(
          (_, index) => toneMarks.find((mark) => mark.index === index)?.value ?? null,
        ),
        borderColor: "transparent",
        backgroundColor: tone === "red" ? RED : ORANGE,
        pointBackgroundColor: tone === "red" ? RED : ORANGE,
        pointRadius: 6,
        pointHoverRadius: 8,
        showLine: false,
        fill: false,
      });
    }

    return { labels, datasets };
  }, [labels, values, seriesLabel, projection, projectionLabel, marks]);

  const options = useMemo<ChartOptions<"line">>(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const raw = typeof ctx.raw === "number" ? ctx.raw : null;
              if (raw === null) return "";
              const isAnnotation = ctx.dataset.showLine === false;
              const note = isAnnotation
                ? marks.find((mark) => mark.index === ctx.dataIndex)
                : undefined;
              return `${note?.label ?? ctx.dataset.label ?? ""}: ${formatValue(raw)}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(128,128,128,.15)" },
          ticks: { color: "#9a9a9a", font: { size: 12 }, maxRotation: 0, autoSkip: true },
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(128,128,128,.15)" },
          ticks: {
            color: "#9a9a9a",
            font: { size: 12 },
            callback: (value) => (typeof value === "number" ? formatValue(value) : String(value)),
          },
        },
      },
    }),
    [marks, formatValue],
  );

  return (
    <div className={cn("rounded-[12px] border border-border bg-card p-6", className)}>
      {(title || (periods && periods.length > 0)) && (
        <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
          <div>
            {title && (
              <div className="font-heading text-base font-bold text-foreground">{title}</div>
            )}
            {subtitle && (
              <div className="font-body text-[13px] text-muted-foreground">{subtitle}</div>
            )}
          </div>
          {periods && periods.length > 0 && (
            <div className="flex gap-2">
              {periods.map((period) => {
                const active = period.key === activePeriod;
                return (
                  <button
                    key={period.key}
                    type="button"
                    onClick={() => onPeriodChange?.(period.key)}
                    aria-pressed={active}
                    className={cn(
                      "rounded-[6px] px-3 py-1.5 font-body text-xs font-semibold transition-colors",
                      active
                        ? "bg-brand-orange text-white"
                        : "border border-brand-orange/30 text-brand-orange hover:bg-brand-orange/10",
                    )}
                  >
                    {period.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      <div className="relative" style={{ height: heightPx }}>
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
